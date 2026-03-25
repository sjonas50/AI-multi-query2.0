"""Company AISEO configuration — SQLite-backed with .env fallback."""

import json
import os
import sqlite3
from typing import Optional

from backend.config import DATA_DIR


_DB_PATH = DATA_DIR / "company_config.db"


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS company_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                domain TEXT NOT NULL UNIQUE,
                sort_order INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS accuracy_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                field_key TEXT NOT NULL UNIQUE,
                correct_value TEXT NOT NULL
            )
        """)
        conn.commit()

        # Seed defaults from .env if table is empty
        count = conn.execute("SELECT COUNT(*) FROM company_config").fetchone()[0]
        if count == 0:
            _seed_defaults(conn)
            conn.commit()
    finally:
        conn.close()


def _seed_defaults(conn: sqlite3.Connection):
    """Populate initial config from environment variables."""
    from backend.config import MODELS as _ENV_MODELS, MAX_TOKENS as _ENV_MAX_TOKENS, TEMPERATURE as _ENV_TEMP, REQUEST_TIMEOUT as _ENV_TIMEOUT

    defaults = {
        "target_company": os.getenv("TARGET_COMPANY", ""),
        "company_domains": os.getenv("COMPANY_DOMAINS", ""),
        "industry": os.getenv("COMPANY_INDUSTRY", ""),
        "analyze_responses": os.getenv("ANALYZE_RESPONSES", "false"),
        "enable_enhanced_analysis": os.getenv("ENABLE_ENHANCED_ANALYSIS", "false"),
        "track_history": os.getenv("TRACK_HISTORY", "false"),
        "domain_classification": os.getenv("DOMAIN_CLASSIFICATION", "false"),
        "negative_signal_detection": os.getenv("NEGATIVE_SIGNAL_DETECTION", "false"),
        "accuracy_verification": os.getenv("ACCURACY_VERIFICATION", "false"),
        "weekly_reporting": os.getenv("WEEKLY_REPORTING", "false"),
        # Model selections
        "model_openai": _ENV_MODELS.get("openai", "gpt-5.2"),
        "model_anthropic": _ENV_MODELS.get("anthropic", "claude-sonnet-4-6"),
        "model_perplexity": _ENV_MODELS.get("perplexity", "sonar-pro"),
        "model_google": _ENV_MODELS.get("google", "gemini-2.5-flash"),
        "model_xai": _ENV_MODELS.get("xai", "grok-4"),
        # Parameters
        "max_tokens": str(_ENV_MAX_TOKENS),
        "temperature": str(_ENV_TEMP),
        "request_timeout": str(_ENV_TIMEOUT),
    }
    for key, value in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO company_config (key, value) VALUES (?, ?)",
            (key, value),
        )

    # Seed competitors from .env domain list
    competitor_env = os.getenv("COMPETITOR_DOMAINS", "")
    if competitor_env:
        for entry in competitor_env.split(","):
            entry = entry.strip()
            if ":" in entry:
                name, domain = entry.split(":", 1)
            else:
                name = entry.split(".")[0].title()
                domain = entry
            conn.execute(
                "INSERT OR IGNORE INTO competitors (name, domain) VALUES (?, ?)",
                (name.strip(), domain.strip()),
            )

    # Seed accuracy facts
    min_inv = os.getenv("CORRECT_MINIMUM_INVESTMENT", "")
    if min_inv:
        conn.execute(
            "INSERT OR IGNORE INTO accuracy_facts (label, field_key, correct_value) VALUES (?, ?, ?)",
            ("Minimum Investment", "minimum_investment", min_inv),
        )


# --- Config key/value ---


def get_config() -> dict:
    """Return all config as a flat dict."""
    conn = _get_db()
    try:
        rows = conn.execute("SELECT key, value FROM company_config").fetchall()
        return {r["key"]: r["value"] for r in rows}
    finally:
        conn.close()


def get_value(key: str, default: str = "") -> str:
    conn = _get_db()
    try:
        row = conn.execute("SELECT value FROM company_config WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def set_config(updates: dict):
    """Upsert multiple config keys."""
    conn = _get_db()
    try:
        for key, value in updates.items():
            conn.execute(
                "INSERT INTO company_config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
                (key, str(value), str(value)),
            )
        conn.commit()
    finally:
        conn.close()


# --- Competitors ---


def list_competitors() -> list[dict]:
    conn = _get_db()
    try:
        rows = conn.execute("SELECT * FROM competitors ORDER BY sort_order, name").fetchall()
        return [{"id": r["id"], "name": r["name"], "domain": r["domain"]} for r in rows]
    finally:
        conn.close()


def add_competitor(name: str, domain: str) -> dict:
    conn = _get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO competitors (name, domain) VALUES (?, ?)",
            (name.strip(), domain.strip().lower()),
        )
        conn.commit()
        return {"id": cursor.lastrowid, "name": name.strip(), "domain": domain.strip().lower()}
    finally:
        conn.close()


def remove_competitor(competitor_id: int) -> bool:
    conn = _get_db()
    try:
        cursor = conn.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# --- Accuracy facts ---


def list_accuracy_facts() -> list[dict]:
    conn = _get_db()
    try:
        rows = conn.execute("SELECT * FROM accuracy_facts ORDER BY id").fetchall()
        return [{"id": r["id"], "label": r["label"], "field_key": r["field_key"], "correct_value": r["correct_value"]} for r in rows]
    finally:
        conn.close()


def add_accuracy_fact(label: str, field_key: str, correct_value: str) -> dict:
    conn = _get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO accuracy_facts (label, field_key, correct_value) VALUES (?, ?, ?)",
            (label.strip(), field_key.strip(), correct_value.strip()),
        )
        conn.commit()
        return {"id": cursor.lastrowid, "label": label.strip(), "field_key": field_key.strip(), "correct_value": correct_value.strip()}
    finally:
        conn.close()


def update_accuracy_fact(fact_id: int, label: str, field_key: str, correct_value: str) -> bool:
    conn = _get_db()
    try:
        cursor = conn.execute(
            "UPDATE accuracy_facts SET label = ?, field_key = ?, correct_value = ? WHERE id = ?",
            (label.strip(), field_key.strip(), correct_value.strip(), fact_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def remove_accuracy_fact(fact_id: int) -> bool:
    conn = _get_db()
    try:
        cursor = conn.execute("DELETE FROM accuracy_facts WHERE id = ?", (fact_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# --- Full AISEO config for analyzer modules ---


# --- Runtime config getters (DB → .env fallback) ---


def get_models() -> dict[str, str]:
    """Return effective model selections. DB overrides .env defaults."""
    from backend.config import MODELS as _ENV_MODELS
    config = get_config()
    return {
        "openai": config.get("model_openai") or _ENV_MODELS.get("openai", "gpt-5.2"),
        "anthropic": config.get("model_anthropic") or _ENV_MODELS.get("anthropic", "claude-sonnet-4-6"),
        "perplexity": config.get("model_perplexity") or _ENV_MODELS.get("perplexity", "sonar-pro"),
        "google": config.get("model_google") or _ENV_MODELS.get("google", "gemini-2.5-flash"),
        "xai": config.get("model_xai") or _ENV_MODELS.get("xai", "grok-4"),
    }


def get_max_tokens() -> int:
    from backend.config import MAX_TOKENS as _ENV_MAX_TOKENS
    val = get_value("max_tokens", "")
    try:
        return int(val) if val else _ENV_MAX_TOKENS
    except ValueError:
        return _ENV_MAX_TOKENS


def get_temperature() -> float:
    from backend.config import TEMPERATURE as _ENV_TEMP
    val = get_value("temperature", "")
    try:
        return float(val) if val else _ENV_TEMP
    except ValueError:
        return _ENV_TEMP


def get_request_timeout() -> int:
    from backend.config import REQUEST_TIMEOUT as _ENV_TIMEOUT
    val = get_value("request_timeout", "")
    try:
        return int(val) if val else _ENV_TIMEOUT
    except ValueError:
        return _ENV_TIMEOUT


def get_web_search() -> dict[str, bool]:
    """Return effective web search toggles. DB overrides .env defaults."""
    from backend.config import WEB_SEARCH as _ENV_WS
    config = get_config()
    result = {}
    for provider in ("openai", "anthropic", "google", "perplexity", "xai"):
        db_key = f"web_search_{provider}"
        db_val = config.get(db_key)
        if db_val is not None:
            result[provider] = db_val == "true"
        else:
            result[provider] = _ENV_WS.get(provider, False)
    # Perplexity always uses web search
    result["perplexity"] = True
    return result


def get_deep_research() -> dict[str, bool]:
    """Return effective deep research toggles. DB overrides .env defaults."""
    from backend.config import DEEP_RESEARCH as _ENV_DR
    config = get_config()
    result = {}
    for provider in ("openai", "anthropic", "google", "perplexity", "xai"):
        db_key = f"deep_research_{provider}"
        db_val = config.get(db_key)
        if db_val is not None:
            result[provider] = db_val == "true"
        else:
            result[provider] = _ENV_DR.get(provider, False)
    return result


def get_aiseo_config() -> dict:
    """Return structured config for use by analyzer, domain_classifier, negative_detector."""
    config = get_config()
    competitors = list_competitors()
    facts = list_accuracy_facts()

    company_domains = [d.strip() for d in config.get("company_domains", "").split(",") if d.strip()]
    competitor_domains = {c["domain"]: c["name"] for c in competitors}
    facts_dict = {f["field_key"]: f["correct_value"] for f in facts}

    return {
        "target_company": config.get("target_company", ""),
        "company_domains": company_domains,
        "industry": config.get("industry", ""),
        "competitor_domains": competitor_domains,
        "accuracy_facts": facts_dict,
        "features": {
            "analyze_responses": config.get("analyze_responses", "false") == "true",
            "enable_enhanced_analysis": config.get("enable_enhanced_analysis", "false") == "true",
            "track_history": config.get("track_history", "false") == "true",
            "domain_classification": config.get("domain_classification", "false") == "true",
            "negative_signal_detection": config.get("negative_signal_detection", "false") == "true",
            "accuracy_verification": config.get("accuracy_verification", "false") == "true",
            "weekly_reporting": config.get("weekly_reporting", "false") == "true",
        },
    }
