"""Provider configuration endpoint."""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.config import CONFIGURED_PROVIDERS, API_KEYS
from backend.services.company_config_service import (
    get_models, get_max_tokens, get_temperature,
    get_web_search, get_deep_research, set_config,
)

router = APIRouter(prefix="/api", tags=["config"])

PROVIDER_DISPLAY = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "perplexity": "Perplexity",
    "google": "Google",
    "xai": "Grok",
    "google_search": "Google Search",
}

ALL_PROVIDERS = ["openai", "anthropic", "perplexity", "google", "xai", "google_search"]

# Which providers support web search / deep research
WEB_SEARCH_SUPPORTED = {"openai", "anthropic", "google", "perplexity", "xai"}
DEEP_RESEARCH_SUPPORTED = {"openai", "anthropic", "google", "perplexity"}


@router.get("/providers")
async def get_providers(_user=Depends(get_current_user)):
    models = get_models()
    ws = get_web_search()
    dr = get_deep_research()
    providers = []
    for p in ALL_PROVIDERS:
        providers.append(
            {
                "name": PROVIDER_DISPLAY.get(p, p),
                "id": p,
                "configured": p in CONFIGURED_PROVIDERS,
                "model": models.get(p),
                "web_search_supported": p in WEB_SEARCH_SUPPORTED,
                "web_search_default": ws.get(p, False),
                "deep_research_supported": p in DEEP_RESEARCH_SUPPORTED,
                "deep_research_default": dr.get(p, False),
            }
        )
    return {"providers": providers}


@router.get("/config")
async def get_config(_user=Depends(get_current_user)):
    return {
        "models": get_models(),
        "max_tokens": get_max_tokens(),
        "temperature": get_temperature(),
        "configured_providers": [PROVIDER_DISPLAY.get(p, p) for p in CONFIGURED_PROVIDERS],
        "web_search": get_web_search(),
        "deep_research": get_deep_research(),
    }


class ConfigUpdateRequest(BaseModel):
    web_search: Optional[dict[str, bool]] = None
    deep_research: Optional[dict[str, bool]] = None
    models: Optional[dict[str, str]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@router.post("/config/defaults")
async def update_config_defaults(body: ConfigUpdateRequest, _user=Depends(get_current_user)):
    """Update model config, parameters, and feature toggles. Persisted to DB."""
    updates: dict[str, str] = {}

    if body.web_search:
        for provider_id, enabled in body.web_search.items():
            if provider_id in WEB_SEARCH_SUPPORTED:
                updates[f"web_search_{provider_id}"] = "true" if enabled else "false"
    if body.deep_research:
        for provider_id, enabled in body.deep_research.items():
            if provider_id in DEEP_RESEARCH_SUPPORTED:
                updates[f"deep_research_{provider_id}"] = "true" if enabled else "false"
    if body.models:
        for provider_id, model_name in body.models.items():
            if provider_id in ("openai", "anthropic", "perplexity", "google", "xai") and model_name.strip():
                updates[f"model_{provider_id}"] = model_name.strip()
    if body.max_tokens is not None:
        updates["max_tokens"] = str(body.max_tokens)
    if body.temperature is not None:
        updates["temperature"] = str(body.temperature)

    if updates:
        set_config(updates)

    return {
        "models": get_models(),
        "max_tokens": get_max_tokens(),
        "temperature": get_temperature(),
        "web_search": get_web_search(),
        "deep_research": get_deep_research(),
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
                    model=get_models()["anthropic"], max_tokens=1,
                    messages=[{"role": "user", "content": "hi"}],
                )
            await asyncio.wait_for(loop.run_in_executor(None, check), timeout=10)

        elif provider == "perplexity":
            def check():
                from openai import OpenAI
                client = OpenAI(api_key=API_KEYS["perplexity"], base_url="https://api.perplexity.ai")
                client.chat.completions.create(
                    model=get_models()["perplexity"], max_tokens=1,
                    messages=[{"role": "user", "content": "hi"}],
                )
            await asyncio.wait_for(loop.run_in_executor(None, check), timeout=10)

        elif provider == "google":
            def check():
                from google import genai
                client = genai.Client(api_key=API_KEYS["google"])
                client.models.get(model=get_models()["google"])
            await asyncio.wait_for(loop.run_in_executor(None, check), timeout=10)

        elif provider == "xai":
            def check():
                from openai import OpenAI
                client = OpenAI(api_key=API_KEYS["xai"], base_url="https://api.x.ai/v1")
                client.chat.completions.create(
                    model=get_models()["xai"], max_tokens=1,
                    messages=[{"role": "user", "content": "hi"}],
                )
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
