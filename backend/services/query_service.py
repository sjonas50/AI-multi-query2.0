"""Wraps the existing FixedLLMTester for async API use."""

import os
import json
import re
from datetime import datetime
from typing import Optional, Callable

from backend.config import (
    API_KEYS,
    CONFIGURED_PROVIDERS,
    HAS_OPENAI,
    HAS_ANTHROPIC,
    HAS_GOOGLE,
    RESULTS_DIR,
    PROJECT_ROOT,
)
from backend.services.company_config_service import (
    get_models,
    get_max_tokens,
    get_temperature,
    get_request_timeout,
    get_web_search,
    get_deep_research,
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
        # Load effective config from DB (falls back to .env)
        self.models = get_models()
        self.max_tokens = get_max_tokens()
        self.temperature = get_temperature()
        self.request_timeout = get_request_timeout()
        self.web_search = get_web_search()
        self.deep_research = get_deep_research()

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
            "xai": "Grok",
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
            "xai": self._test_xai,
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

        use_web = web_search if web_search is not None else self.web_search["openai"]
        use_deep = deep_research if deep_research is not None else self.deep_research["openai"]

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_keys["openai"])
            enhanced = self._enhance_prompt(prompt, request_sources)

            if use_deep:
                # Deep research — dedicated model via Responses API
                response = client.responses.create(
                    model="o3-deep-research",
                    tools=[{"type": "web_search_preview"}],
                    input=enhanced,
                )
                return {
                    "provider": "OpenAI",
                    "response": response.output_text,
                    "model": "o3-deep-research",
                    "web_search": True,
                    "deep_research": True,
                    "success": True,
                }
            elif use_web:
                # Responses API with web_search tool
                response = client.responses.create(
                    model=self.models["openai"],
                    tools=[{"type": "web_search"}],
                    input=enhanced,
                )
                return {
                    "provider": "OpenAI",
                    "response": response.output_text,
                    "model": self.models["openai"],
                    "web_search": True,
                    "success": True,
                }
            else:
                # Standard Chat Completions API
                response = client.chat.completions.create(
                    model=self.models["openai"],
                    messages=[{"role": "user", "content": enhanced}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
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
    # Anthropic — web_search_20260209 tool when enabled (dynamic filtering)
    # ------------------------------------------------------------------
    def _test_anthropic(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
    ) -> dict:
        if "anthropic" not in self.configured_providers or not self.has_anthropic:
            return {"provider": "Anthropic", "error": "Not configured or library not installed"}

        use_web = web_search if web_search is not None else self.web_search["anthropic"]
        use_deep = deep_research if deep_research is not None else self.deep_research["anthropic"]

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_keys["anthropic"])
            enhanced = self._enhance_prompt(prompt, request_sources)

            kwargs = {
                "model": self.models["anthropic"],
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": enhanced}],
            }

            if use_deep:
                # Deep research: extended thinking + web search for thorough analysis
                kwargs["thinking"] = {"type": "enabled", "budget_tokens": 10000}
                kwargs["max_tokens"] = 16000
                kwargs["tools"] = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]
            elif use_web:
                kwargs["tools"] = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]

            response = client.messages.create(**kwargs)

            # Extract text from content blocks (web search / thinking returns multiple blocks)
            text_parts = []
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    text_parts.append(block.text)

            return {
                "provider": "Anthropic",
                "response": "\n".join(text_parts),
                "model": response.model,
                "web_search": use_web or use_deep,
                "deep_research": use_deep,
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

        use_deep = deep_research if deep_research is not None else self.deep_research["perplexity"]
        model = "sonar-deep-research" if use_deep else self.models["perplexity"]

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
                max_tokens=self.max_tokens,
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

        use_web = web_search if web_search is not None else self.web_search["google"]
        use_deep = deep_research if deep_research is not None else self.deep_research["google"]

        try:
            from google import genai
            client = genai.Client(api_key=self.api_keys["google"])
            enhanced = self._enhance_prompt(prompt, request_sources)

            if use_deep:
                # Deep research via Interactions API (polling-based)
                return self._google_deep_research(client, enhanced)

            model = self.models["google"]
            config_kwargs = {}

            if use_web:
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
                "web_search": use_web,
                "deep_research": False,
                "success": True,
            }
        except ImportError:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_keys["google"])
                model_obj = genai.GenerativeModel(self.models["google"])
                enhanced = self._enhance_prompt(prompt, request_sources)
                response = model_obj.generate_content(enhanced)
                return {
                    "provider": "Google",
                    "response": response.text,
                    "model": self.models["google"],
                    "web_search": False,
                    "success": True,
                }
            except Exception as e:
                return {"provider": "Google", "error": str(e)}
        except Exception as e:
            return {"provider": "Google", "error": str(e)}

    def _google_deep_research(self, client, prompt: str) -> dict:
        """Google Deep Research via Interactions API (polling). No status updates."""
        return self._google_deep_research_with_status(prompt, False, None)

    def _google_deep_research_with_status(
        self, prompt: str, request_sources: bool = False,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """Google Deep Research via Interactions API with status updates during polling."""
        import time as _time

        _DEEP_RESEARCH_MODEL = "deep-research-pro-preview-12-2025"

        try:
            from google import genai
            client = genai.Client(api_key=self.api_keys["google"])
            enhanced = self._enhance_prompt(prompt, request_sources)

            if on_status:
                on_status("Initiating deep research agent...")

            interaction = client.interactions.create(
                input=enhanced,
                agent=_DEEP_RESEARCH_MODEL,
                background=True,
            )

            # Poll until complete (timeout after 5 minutes)
            deadline = _time.time() + 300
            poll_count = 0
            while _time.time() < deadline:
                interaction = client.interactions.get(interaction.id)
                poll_count += 1
                elapsed = int(_time.time() - (deadline - 300))

                if interaction.status == "completed":
                    if on_status:
                        on_status("Deep research complete, processing results...")
                    text = interaction.outputs[-1].text if interaction.outputs else ""
                    return {
                        "provider": "Google",
                        "response": text,
                        "model": _DEEP_RESEARCH_MODEL,
                        "web_search": True,
                        "deep_research": True,
                        "success": True,
                    }
                elif interaction.status == "failed":
                    error = getattr(interaction, "error", "Unknown error")
                    return {"provider": "Google", "error": f"Deep research failed: {error}"}

                # Send progress updates during polling
                if on_status:
                    status_text = getattr(interaction, "status", "processing")
                    on_status(f"Deep research in progress ({elapsed}s elapsed, status: {status_text})...")

                _time.sleep(10)

            return {"provider": "Google", "error": "Deep research timed out after 5 minutes"}
        except Exception as e:
            return {"provider": "Google", "error": str(e)}

    # ------------------------------------------------------------------
    # xAI Grok — OpenAI-compatible API at api.x.ai
    # ------------------------------------------------------------------
    def _test_xai(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
    ) -> dict:
        if "xai" not in self.configured_providers:
            return {"provider": "Grok", "error": "Not configured"}

        use_web = web_search if web_search is not None else self.web_search.get("xai", False)

        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_keys["xai"],
                base_url="https://api.x.ai/v1",
            )
            enhanced = self._enhance_prompt(prompt, request_sources)

            if use_web:
                # Grok supports web search via the Responses API with search tool
                response = client.responses.create(
                    model=self.models["xai"],
                    tools=[{"type": "web_search"}],
                    input=enhanced,
                )
                return {
                    "provider": "Grok",
                    "response": response.output_text,
                    "model": self.models["xai"],
                    "web_search": True,
                    "success": True,
                }
            else:
                response = client.chat.completions.create(
                    model=self.models["xai"],
                    messages=[{"role": "user", "content": enhanced}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                return {
                    "provider": "Grok",
                    "response": response.choices[0].message.content,
                    "model": response.model,
                    "web_search": False,
                    "success": True,
                }
        except Exception as e:
            return {"provider": "Grok", "error": str(e)}

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
            response = requests.get(url, params=params, timeout=self.request_timeout)
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

    # ==================================================================
    # Streaming methods — call on_token/on_thinking callbacks per chunk
    # ==================================================================

    def stream_provider(
        self,
        provider: str,
        query: str,
        request_sources: bool = False,
        web_search: Optional[bool] = None,
        deep_research: Optional[bool] = None,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        context_messages: Optional[list[dict]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """Stream tokens from a provider. Falls back to test_provider for unsupported providers."""
        dispatch = {
            "openai": self._stream_openai,
            "anthropic": self._stream_anthropic,
            "perplexity": self._stream_perplexity,
            "google": self._stream_google,
            "xai": self._stream_xai,
        }
        fn = dispatch.get(provider)
        if not fn:
            # google_search and unknown providers: non-streaming fallback
            if on_status:
                on_status("Fetching search results...")
            return self.test_provider(provider, query, request_sources, web_search, deep_research)
        return fn(query, request_sources, web_search, deep_research, on_token, on_thinking, context_messages, on_status)

    def _stream_openai(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        context_messages: Optional[list[dict]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> dict:
        if "openai" not in self.configured_providers or not self.has_openai:
            return {"provider": "OpenAI", "error": "Not configured or library not installed"}

        use_web = web_search if web_search is not None else self.web_search["openai"]
        use_deep = deep_research if deep_research is not None else self.deep_research["openai"]

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_keys["openai"])
            enhanced = self._enhance_prompt(prompt, request_sources)

            if use_deep:
                # Deep research — non-streaming fallback (long-running)
                if on_status:
                    on_status("Starting deep research (this may take several minutes)...")
                return self._test_openai(prompt, request_sources, web_search, deep_research)
            elif use_web:
                # Responses API with web_search tool — streaming
                if on_status:
                    on_status("Searching the web...")
                # Prepend conversation context for follow-ups
                web_input = enhanced
                if context_messages and len(context_messages) > 1:
                    ctx_parts = ["Previous conversation:\n"]
                    for msg in context_messages[:-1]:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        content = msg["content"]
                        if len(content) > 2000:
                            content = content[:2000] + "..."
                        ctx_parts.append(f"{role}: {content}")
                    ctx_parts.append(f"\nNow answer this follow-up question:\n{enhanced}")
                    web_input = "\n".join(ctx_parts)
                parts = []
                started_text = False
                stream = client.responses.create(
                    model=self.models["openai"],
                    tools=[{"type": "web_search"}],
                    input=web_input,
                    stream=True,
                )
                for event in stream:
                    if event.type == "response.output_text.delta":
                        if not started_text and on_status:
                            on_status("Generating response...")
                            started_text = True
                        text = event.delta
                        if text and on_token:
                            on_token(text)
                        if text:
                            parts.append(text)
                return {
                    "provider": "OpenAI",
                    "response": "".join(parts),
                    "model": self.models["openai"],
                    "web_search": True,
                    "success": True,
                }
            else:
                # Standard Chat Completions API — streaming
                if on_status:
                    on_status("Generating response...")
                parts = []
                messages = context_messages if context_messages else [{"role": "user", "content": enhanced}]
                if context_messages:
                    # Enhance the last user message with source instruction if needed
                    messages = list(context_messages)
                    if request_sources or self.request_sources:
                        last = messages[-1]
                        messages[-1] = {**last, "content": self._enhance_prompt(last["content"], True)}
                stream = client.chat.completions.create(
                    model=self.models["openai"],
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stream=True,
                )
                model_name = self.models["openai"]
                for chunk in stream:
                    if chunk.model:
                        model_name = chunk.model
                    if chunk.choices and chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        if on_token:
                            on_token(text)
                        parts.append(text)
                return {
                    "provider": "OpenAI",
                    "response": "".join(parts),
                    "model": model_name,
                    "web_search": False,
                    "success": True,
                }
        except Exception as e:
            return {"provider": "OpenAI", "error": str(e)}

    def _stream_anthropic(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        context_messages: Optional[list[dict]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> dict:
        if "anthropic" not in self.configured_providers or not self.has_anthropic:
            return {"provider": "Anthropic", "error": "Not configured or library not installed"}

        use_web = web_search if web_search is not None else self.web_search["anthropic"]
        use_deep = deep_research if deep_research is not None else self.deep_research["anthropic"]

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_keys["anthropic"])
            enhanced = self._enhance_prompt(prompt, request_sources)

            if context_messages:
                messages = list(context_messages)
                if request_sources or self.request_sources:
                    last = messages[-1]
                    messages[-1] = {**last, "content": self._enhance_prompt(last["content"], True)}
            else:
                messages = [{"role": "user", "content": enhanced}]

            kwargs = {
                "model": self.models["anthropic"],
                "max_tokens": self.max_tokens,
                "messages": messages,
            }

            if use_deep:
                if on_status:
                    on_status("Deep research: thinking + web search...")
                kwargs["thinking"] = {"type": "enabled", "budget_tokens": 10000}
                kwargs["max_tokens"] = 16000
                kwargs["tools"] = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]
            elif use_web:
                if on_status:
                    on_status("Searching the web...")
                kwargs["tools"] = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]
            else:
                if on_status:
                    on_status("Generating response...")

            text_parts = []
            thinking_parts = []

            with client.messages.stream(**kwargs) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            text = getattr(event.delta, "text", None)
                            if text:
                                if on_token:
                                    on_token(text)
                                text_parts.append(text)
                        elif event.delta.type == "thinking_delta":
                            text = getattr(event.delta, "thinking", None)
                            if text:
                                if on_thinking:
                                    on_thinking(text)
                                thinking_parts.append(text)

            final_message = stream.get_final_message()

            result = {
                "provider": "Anthropic",
                "response": "".join(text_parts),
                "model": final_message.model if final_message else self.models["anthropic"],
                "web_search": use_web or use_deep,
                "deep_research": use_deep,
                "success": True,
            }
            if thinking_parts:
                result["thinking"] = "".join(thinking_parts)
            return result
        except Exception as e:
            return {"provider": "Anthropic", "error": str(e)}

    def _stream_perplexity(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        context_messages: Optional[list[dict]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> dict:
        if "perplexity" not in self.configured_providers:
            return {"provider": "Perplexity", "error": "Not configured"}

        use_deep = deep_research if deep_research is not None else self.deep_research["perplexity"]
        model = "sonar-deep-research" if use_deep else self.models["perplexity"]

        if use_deep:
            # Deep research — non-streaming fallback
            if on_status:
                on_status("Starting deep research (this may take several minutes)...")
            return self._test_perplexity(prompt, request_sources, web_search, deep_research)

        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_keys["perplexity"],
                base_url="https://api.perplexity.ai",
            )
            if on_status:
                on_status("Searching the web...")
            enhanced = self._enhance_prompt(prompt, request_sources)
            if context_messages:
                messages = list(context_messages)
                if request_sources or self.request_sources:
                    last = messages[-1]
                    messages[-1] = {**last, "content": self._enhance_prompt(last["content"], True)}
            else:
                messages = [{"role": "user", "content": enhanced}]
            parts = []
            model_name = model
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=self.max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.model:
                    model_name = chunk.model
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    if on_token:
                        on_token(text)
                    parts.append(text)
            return {
                "provider": "Perplexity",
                "response": "".join(parts),
                "model": model_name,
                "web_search": True,
                "deep_research": use_deep,
                "success": True,
            }
        except Exception as e:
            return {"provider": "Perplexity", "error": str(e)}

    def _stream_google(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        context_messages: Optional[list[dict]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> dict:
        if "google" not in self.configured_providers or not self.has_google:
            return {"provider": "Google", "error": "Not configured or library not installed"}

        use_web = web_search if web_search is not None else self.web_search["google"]
        use_deep = deep_research if deep_research is not None else self.deep_research["google"]

        if use_deep:
            # Deep research — uses Interactions API (non-streaming, polling)
            if on_status:
                on_status("Starting deep research (this may take several minutes)...")
            return self._google_deep_research_with_status(
                prompt, request_sources, on_status,
            )

        try:
            from google import genai
            client = genai.Client(api_key=self.api_keys["google"])

            # Google doesn't support messages array; use context prefix for follow-ups
            if context_messages and len(context_messages) > 1:
                ctx_parts = ["Previous conversation:\n"]
                # Include all prior turns but NOT the last message (the current query)
                for msg in context_messages[:-1]:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    content = msg["content"]
                    if len(content) > 2000:
                        content = content[:2000] + "..."
                    ctx_parts.append(f"{role}: {content}")
                ctx_parts.append(f"\nNow answer this follow-up question:\n{prompt}")
                enhanced = "\n".join(ctx_parts)
                if request_sources or self.request_sources:
                    enhanced = self._enhance_prompt(enhanced, True)
            else:
                enhanced = self._enhance_prompt(prompt, request_sources)

            model = self.models["google"]
            config_kwargs = {}

            if use_web:
                if on_status:
                    on_status("Searching the web with Gemini...")
                config_kwargs["tools"] = [genai.types.Tool(google_search=genai.types.GoogleSearch())]
            else:
                if on_status:
                    on_status("Generating response...")

            parts = []
            if config_kwargs:
                config = genai.types.GenerateContentConfig(**config_kwargs)
                stream = client.models.generate_content_stream(
                    model=model, contents=enhanced, config=config,
                )
            else:
                stream = client.models.generate_content_stream(
                    model=model, contents=enhanced,
                )

            for chunk in stream:
                text = chunk.text if hasattr(chunk, "text") and chunk.text else None
                if text:
                    if on_token:
                        on_token(text)
                    parts.append(text)

            return {
                "provider": "Google",
                "response": "".join(parts),
                "model": model,
                "web_search": use_web,
                "deep_research": False,
                "success": True,
            }
        except ImportError:
            # Fall back to legacy library (no streaming support)
            return self._test_google(prompt, request_sources, web_search, deep_research)
        except Exception as e:
            return {"provider": "Google", "error": str(e)}

    def _stream_xai(
        self, prompt: str, request_sources: bool = False,
        web_search: Optional[bool] = None, deep_research: Optional[bool] = None,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        context_messages: Optional[list[dict]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> dict:
        if "xai" not in self.configured_providers:
            return {"provider": "Grok", "error": "Not configured"}

        use_web = web_search if web_search is not None else self.web_search.get("xai", False)

        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_keys["xai"],
                base_url="https://api.x.ai/v1",
            )
            enhanced = self._enhance_prompt(prompt, request_sources)

            if use_web:
                # Responses API with web_search — streaming
                if on_status:
                    on_status("Searching the web...")
                # Prepend conversation context for follow-ups
                web_input = enhanced
                if context_messages and len(context_messages) > 1:
                    ctx_parts = ["Previous conversation:\n"]
                    for msg in context_messages[:-1]:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        content = msg["content"]
                        if len(content) > 2000:
                            content = content[:2000] + "..."
                        ctx_parts.append(f"{role}: {content}")
                    ctx_parts.append(f"\nNow answer this follow-up question:\n{enhanced}")
                    web_input = "\n".join(ctx_parts)
                parts = []
                stream = client.responses.create(
                    model=self.models["xai"],
                    tools=[{"type": "web_search"}],
                    input=web_input,
                    stream=True,
                )
                for event in stream:
                    if event.type == "response.output_text.delta":
                        text = event.delta
                        if text and on_token:
                            on_token(text)
                        if text:
                            parts.append(text)
                return {
                    "provider": "Grok",
                    "response": "".join(parts),
                    "model": self.models["xai"],
                    "web_search": True,
                    "success": True,
                }
            else:
                # Chat Completions — streaming
                if on_status:
                    on_status("Generating response...")
                if context_messages:
                    messages = list(context_messages)
                    if request_sources or self.request_sources:
                        last = messages[-1]
                        messages[-1] = {**last, "content": self._enhance_prompt(last["content"], True)}
                else:
                    messages = [{"role": "user", "content": enhanced}]

                parts = []
                model_name = self.models["xai"]
                stream = client.chat.completions.create(
                    model=self.models["xai"],
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stream=True,
                )
                for chunk in stream:
                    if chunk.model:
                        model_name = chunk.model
                    if chunk.choices and chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        if on_token:
                            on_token(text)
                        parts.append(text)
                return {
                    "provider": "Grok",
                    "response": "".join(parts),
                    "model": model_name,
                    "web_search": False,
                    "success": True,
                }
        except Exception as e:
            return {"provider": "Grok", "error": str(e)}

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
