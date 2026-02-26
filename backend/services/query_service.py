"""Wraps the existing FixedLLMTester for async API use."""

import os
import json
import re
from datetime import datetime
from typing import Optional

from backend.config import (
    API_KEYS,
    CONFIGURED_PROVIDERS,
    HAS_OPENAI,
    HAS_ANTHROPIC,
    HAS_GOOGLE,
    MAX_TOKENS,
    TEMPERATURE,
    REQUEST_TIMEOUT,
    MODELS,
    WEB_SEARCH,
    DEEP_RESEARCH,
    RESULTS_DIR,
    PROJECT_ROOT,
)


class QueryService:
    """Provides the same provider test methods as FixedLLMTester, but without side effects."""

    def __init__(self):
        self.api_keys = API_KEYS
        self.configured_providers = CONFIGURED_PROVIDERS
        self.has_openai = HAS_OPENAI
        self.has_anthropic = HAS_ANTHROPIC
        self.has_google = HAS_GOOGLE
        self.request_sources = os.getenv("REQUEST_SOURCES", "false").lower() == "true"
        self.source_instruction = os.getenv(
            "SOURCE_INSTRUCTION",
            "Please cite your sources with specific URLs or domain names where this information can be verified.",
        )

    def _enhance_prompt(self, prompt: str, request_sources: bool = False) -> str:
        if request_sources or self.request_sources:
            return f"{prompt}\n\n{self.source_instruction}"
        return prompt

    def get_provider_display_name(self, provider: str) -> str:
        names = {
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "perplexity": "Perplexity",
            "google": "Google",
            "google_search": "Google Search",
        }
        return names.get(provider, provider)

    def test_provider(
        self,
        provider: str,
        query: str,
        request_sources: bool = False,
        web_search: Optional[bool] = None,
        deep_research: Optional[bool] = None,
    ) -> dict:
        dispatch = {
            "openai": self._test_openai,
            "anthropic": self._test_anthropic,
            "perplexity": self._test_perplexity,
            "google": self._test_google,
            "google_search": self._test_google_search,
        }
        fn = dispatch.get(provider)
        if not fn:
            return {"provider": self.get_provider_display_name(provider), "error": f"Unknown provider: {provider}"}
        return fn(query, request_sources, web_search, deep_research)

    # ------------------------------------------------------------------
    # OpenAI — uses Responses API when web_search is enabled
    # ------------------------------------------------------------------
    def _test_openai(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
    ) -> dict:
        if "openai" not in self.configured_providers or not self.has_openai:
            return {"provider": "OpenAI", "error": "Not configured or library not installed"}

        use_web = web_search if web_search is not None else WEB_SEARCH["openai"]

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_keys["openai"])
            enhanced = self._enhance_prompt(prompt, request_sources)

            if use_web:
                # Responses API with web_search tool
                response = client.responses.create(
                    model=MODELS["openai"],
                    tools=[{"type": "web_search"}],
                    input=enhanced,
                )
                return {
                    "provider": "OpenAI",
                    "response": response.output_text,
                    "model": MODELS["openai"],
                    "web_search": True,
                    "success": True,
                }
            else:
                # Standard Chat Completions API
                response = client.chat.completions.create(
                    model=MODELS["openai"],
                    messages=[{"role": "user", "content": enhanced}],
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                )
                return {
                    "provider": "OpenAI",
                    "response": response.choices[0].message.content,
                    "model": response.model,
                    "web_search": False,
                    "success": True,
                }
        except Exception as e:
            return {"provider": "OpenAI", "error": str(e)}

    # ------------------------------------------------------------------
    # Anthropic — web_search_20250305 tool when enabled
    # ------------------------------------------------------------------
    def _test_anthropic(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
    ) -> dict:
        if "anthropic" not in self.configured_providers or not self.has_anthropic:
            return {"provider": "Anthropic", "error": "Not configured or library not installed"}

        use_web = web_search if web_search is not None else WEB_SEARCH["anthropic"]

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_keys["anthropic"])
            enhanced = self._enhance_prompt(prompt, request_sources)

            kwargs = {
                "model": MODELS["anthropic"],
                "max_tokens": MAX_TOKENS,
                "messages": [{"role": "user", "content": enhanced}],
            }

            if use_web:
                kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]

            response = client.messages.create(**kwargs)

            # Extract text from content blocks (web search returns multiple blocks)
            text_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)

            return {
                "provider": "Anthropic",
                "response": "\n".join(text_parts),
                "model": response.model,
                "web_search": use_web,
                "success": True,
            }
        except Exception as e:
            return {"provider": "Anthropic", "error": str(e)}

    # ------------------------------------------------------------------
    # Perplexity — model swap for deep research
    # ------------------------------------------------------------------
    def _test_perplexity(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
    ) -> dict:
        if "perplexity" not in self.configured_providers:
            return {"provider": "Perplexity", "error": "Not configured"}

        use_deep = deep_research if deep_research is not None else DEEP_RESEARCH["perplexity"]
        model = "sonar-deep-research" if use_deep else MODELS["perplexity"]

        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_keys["perplexity"],
                base_url="https://api.perplexity.ai",
            )
            enhanced = self._enhance_prompt(prompt, request_sources)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": enhanced}],
                max_tokens=MAX_TOKENS,
            )
            return {
                "provider": "Perplexity",
                "response": response.choices[0].message.content,
                "model": response.model,
                "web_search": True,
                "deep_research": use_deep,
                "success": True,
            }
        except Exception as e:
            return {"provider": "Perplexity", "error": str(e)}

    # ------------------------------------------------------------------
    # Google Gemini — grounding with Google Search when enabled
    # ------------------------------------------------------------------
    def _test_google(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
    ) -> dict:
        if "google" not in self.configured_providers or not self.has_google:
            return {"provider": "Google", "error": "Not configured or library not installed"}

        use_web = web_search if web_search is not None else WEB_SEARCH["google"]
        use_deep = deep_research if deep_research is not None else DEEP_RESEARCH["google"]

        try:
            from google import genai
            client = genai.Client(api_key=self.api_keys["google"])
            enhanced = self._enhance_prompt(prompt, request_sources)

            model = MODELS["google"]
            config_kwargs = {}

            if use_deep:
                # Use deep research model
                model = "deep-research-pro-preview-12-2025"
            elif use_web:
                # Grounding with Google Search
                config_kwargs["tools"] = [genai.types.Tool(google_search=genai.types.GoogleSearch())]

            if config_kwargs:
                config = genai.types.GenerateContentConfig(**config_kwargs)
                response = client.models.generate_content(
                    model=model, contents=enhanced, config=config,
                )
            else:
                response = client.models.generate_content(
                    model=model, contents=enhanced,
                )

            return {
                "provider": "Google",
                "response": response.text,
                "model": model,
                "web_search": use_web or use_deep,
                "deep_research": use_deep,
                "success": True,
            }
        except ImportError:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_keys["google"])
                model_obj = genai.GenerativeModel(MODELS["google"])
                enhanced = self._enhance_prompt(prompt, request_sources)
                response = model_obj.generate_content(enhanced)
                return {
                    "provider": "Google",
                    "response": response.text,
                    "model": MODELS["google"],
                    "web_search": False,
                    "success": True,
                }
            except Exception as e:
                return {"provider": "Google", "error": str(e)}
        except Exception as e:
            return {"provider": "Google", "error": str(e)}

    # ------------------------------------------------------------------
    # Google Custom Search (unchanged)
    # ------------------------------------------------------------------
    def _test_google_search(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
    ) -> dict:
        if "google_search" not in self.configured_providers:
            return {"provider": "Google Search", "error": "Not configured"}
        try:
            import requests

            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_keys["google_search"],
                "cx": self.api_keys["google_cx"],
                "q": prompt,
                "num": 10,
            }
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                return {
                    "provider": "Google Search",
                    "error": f"API returned status {response.status_code}",
                }
            data = response.json()
            search_results = []
            for item in data.get("items", []):
                search_results.append(
                    {
                        "title": item.get("title", "No title"),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "No description available"),
                    }
                )
            return {
                "provider": "Google Search",
                "response": search_results,
                "total_results": data.get("searchInformation", {}).get("totalResults", "0"),
                "success": True,
            }
        except Exception as e:
            return {"provider": "Google Search", "error": str(e)}

    def save_results(self, query: str, results: list[dict]) -> str:
        """Save results to JSON file, matching existing file naming convention."""
        RESULTS_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^\w\s-]", "", query.lower())
        slug = re.sub(r"[-\s]+", "_", slug)[:50]
        filename = f"llm_results_{slug}_{timestamp}.json"
        filepath = RESULTS_DIR / filename

        output = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "results": results,
        }
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2, default=str)

        return filename
