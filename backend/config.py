"""Centralized configuration — loads .env and builds provider config without side effects."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Project root is the parent of backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Add project root to sys.path so we can import analyzer, tracker, etc.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _check_import(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


# Library availability
HAS_OPENAI = _check_import("openai")
HAS_ANTHROPIC = _check_import("anthropic")
HAS_GOOGLE = _check_import("google.genai") or _check_import("google.generativeai")

# API keys
API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY", ""),
    "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
    "perplexity": os.getenv("PERPLEXITY_API_KEY", ""),
    "google": os.getenv("GOOGLE_API_KEY", ""),
    "google_search": os.getenv("GOOGLE_SEARCH_API_KEY", ""),
    "google_cx": os.getenv("GOOGLE_SEARCH_CX", ""),
}

# Template prefixes to detect unconfigured keys
_TEMPLATE_PREFIXES = ("your-", "sk-your", "pplx-your")


def _is_configured(key: str) -> bool:
    return bool(key) and not any(key.startswith(p) for p in _TEMPLATE_PREFIXES)


def get_configured_providers() -> list[str]:
    providers = []
    for name in ("openai", "anthropic", "perplexity", "google"):
        if _is_configured(API_KEYS[name]):
            providers.append(name)
    if _is_configured(API_KEYS["google_search"]) and _is_configured(API_KEYS["google_cx"]):
        providers.append("google_search")
    return providers


CONFIGURED_PROVIDERS = get_configured_providers()

# Model defaults
MODELS = {
    "openai": os.getenv("OPENAI_MODEL", "gpt-5.2"),
    "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
    "perplexity": os.getenv("PERPLEXITY_MODEL", "sonar-pro"),
    "google": os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),
}

# Per-provider web search toggle
WEB_SEARCH = {
    "openai": os.getenv("OPENAI_WEB_SEARCH", "false").lower() == "true",
    "anthropic": os.getenv("ANTHROPIC_WEB_SEARCH", "false").lower() == "true",
    "google": os.getenv("GOOGLE_WEB_SEARCH", "false").lower() == "true",
    "perplexity": True,  # Perplexity always searches the web
}

# Per-provider deep research toggle (uses different model/mode)
DEEP_RESEARCH = {
    "openai": os.getenv("OPENAI_DEEP_RESEARCH", "false").lower() == "true",
    "anthropic": False,  # No deep research API for Anthropic yet
    "google": os.getenv("GOOGLE_DEEP_RESEARCH", "false").lower() == "true",
    "perplexity": os.getenv("PERPLEXITY_DEEP_RESEARCH", "false").lower() == "true",
}

# Settings
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Analysis settings
ANALYZE_RESPONSES = os.getenv("ANALYZE_RESPONSES", "false").lower() == "true"
ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", "gpt-5.2")

# Auth
AUTH_SECRET = os.getenv("AUTH_SECRET", "change-me")
JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-change-me")

# Paths
RESULTS_DIR = PROJECT_ROOT / "results"
REPORTS_DIR = PROJECT_ROOT / "reports"
DATABASE_PATH = PROJECT_ROOT / os.getenv("DATABASE_PATH", "tracking.db")
