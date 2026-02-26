"""Provider configuration endpoint."""

import asyncio
from fastapi import APIRouter, Depends

from backend.auth import get_current_user
from backend.config import CONFIGURED_PROVIDERS, MODELS, WEB_SEARCH, DEEP_RESEARCH, MAX_TOKENS, TEMPERATURE, API_KEYS

router = APIRouter(prefix="/api", tags=["config"])

PROVIDER_DISPLAY = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "perplexity": "Perplexity",
    "google": "Google",
    "google_search": "Google Search",
}

ALL_PROVIDERS = ["openai", "anthropic", "perplexity", "google", "google_search"]

# Which providers support web search / deep research
WEB_SEARCH_SUPPORTED = {"openai", "anthropic", "google", "perplexity"}
DEEP_RESEARCH_SUPPORTED = {"google", "perplexity"}


@router.get("/providers")
async def get_providers(_user=Depends(get_current_user)):
    providers = []
    for p in ALL_PROVIDERS:
        providers.append(
            {
                "name": PROVIDER_DISPLAY.get(p, p),
                "id": p,
                "configured": p in CONFIGURED_PROVIDERS,
                "model": MODELS.get(p),
                "web_search_supported": p in WEB_SEARCH_SUPPORTED,
                "web_search_default": WEB_SEARCH.get(p, False),
                "deep_research_supported": p in DEEP_RESEARCH_SUPPORTED,
                "deep_research_default": DEEP_RESEARCH.get(p, False),
            }
        )
    return {"providers": providers}


@router.get("/config")
async def get_config(_user=Depends(get_current_user)):
    return {
        "models": MODELS,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "configured_providers": [PROVIDER_DISPLAY.get(p, p) for p in CONFIGURED_PROVIDERS],
        "web_search": WEB_SEARCH,
        "deep_research": DEEP_RESEARCH,
    }


async def _check_provider_health(provider: str) -> dict:
    """Quick connectivity check for a provider."""
    import time
    name = PROVIDER_DISPLAY.get(provider, provider)
    if provider not in CONFIGURED_PROVIDERS:
        return {"provider": name, "status": "not_configured"}

    start = time.time()
    try:
        loop = asyncio.get_event_loop()

        if provider == "openai":
            def check():
                from openai import OpenAI
                client = OpenAI(api_key=API_KEYS["openai"])
                client.models.list()
            await asyncio.wait_for(loop.run_in_executor(None, check), timeout=10)

        elif provider == "anthropic":
            def check():
                import anthropic
                client = anthropic.Anthropic(api_key=API_KEYS["anthropic"])
                client.messages.create(
                    model=MODELS["anthropic"], max_tokens=1,
                    messages=[{"role": "user", "content": "hi"}],
                )
            await asyncio.wait_for(loop.run_in_executor(None, check), timeout=10)

        elif provider == "perplexity":
            def check():
                from openai import OpenAI
                client = OpenAI(api_key=API_KEYS["perplexity"], base_url="https://api.perplexity.ai")
                client.chat.completions.create(
                    model=MODELS["perplexity"], max_tokens=1,
                    messages=[{"role": "user", "content": "hi"}],
                )
            await asyncio.wait_for(loop.run_in_executor(None, check), timeout=10)

        elif provider == "google":
            def check():
                from google import genai
                client = genai.Client(api_key=API_KEYS["google"])
                client.models.get(model=MODELS["google"])
            await asyncio.wait_for(loop.run_in_executor(None, check), timeout=10)

        elif provider == "google_search":
            def check():
                import requests
                resp = requests.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={"key": API_KEYS["google_search"], "cx": API_KEYS["google_cx"], "q": "test", "num": 1},
                    timeout=10,
                )
                resp.raise_for_status()
            await asyncio.wait_for(loop.run_in_executor(None, check), timeout=10)

        latency = round(time.time() - start, 2)
        return {"provider": name, "status": "ok", "latency": latency}

    except Exception as e:
        latency = round(time.time() - start, 2)
        return {"provider": name, "status": "error", "error": str(e)[:200], "latency": latency}


@router.get("/providers/health")
async def check_providers_health(_user=Depends(get_current_user)):
    """Check connectivity for all configured providers."""
    tasks = [_check_provider_health(p) for p in ALL_PROVIDERS]
    results = await asyncio.gather(*tasks)
    return {"results": results}
