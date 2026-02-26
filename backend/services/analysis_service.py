"""Wraps ResponseAnalyzer and HistoricalTracker for API use."""

import json
import sqlite3
from typing import Optional

from backend.config import DATABASE_PATH, PROJECT_ROOT

# Import the existing modules (they're safe to import — no module-level side effects)
try:
    from analyzer import ResponseAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False

try:
    from tracker import HistoricalTracker
    TRACKER_AVAILABLE = True
except ImportError:
    TRACKER_AVAILABLE = False

try:
    from reporter import WeeklyReporter
    REPORTER_AVAILABLE = True
except ImportError:
    REPORTER_AVAILABLE = False


def get_analyzer() -> Optional["ResponseAnalyzer"]:
    if not ANALYZER_AVAILABLE:
        return None
    return ResponseAnalyzer()


def get_tracker() -> Optional["HistoricalTracker"]:
    if not TRACKER_AVAILABLE:
        return None
    return HistoricalTracker(str(DATABASE_PATH))


def get_historical_trends(weeks: int = 4) -> list[dict]:
    tracker = get_tracker()
    if not tracker:
        return []
    return tracker.get_historical_trends(weeks)


def get_analysis_history(
    page: int = 1,
    limit: int = 20,
    provider: Optional[str] = None,
    query_search: Optional[str] = None,
) -> dict:
    """Query analysis_history from tracking.db."""
    if not DATABASE_PATH.exists():
        return {"items": [], "total": 0, "page": page, "limit": limit}

    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if provider:
        where_clauses.append("provider = ?")
        params.append(provider)
    if query_search:
        where_clauses.append("query LIKE ?")
        params.append(f"%{query_search}%")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    cursor.execute(f"SELECT COUNT(*) FROM analysis_history {where_sql}", params)
    total = cursor.fetchone()[0]

    offset = (page - 1) * limit
    cursor.execute(
        f"""SELECT id, timestamp, query, provider, companies_mentioned,
                   sentiment, ugc_percentage, owned_percentage, authority_percentage
            FROM analysis_history {where_sql}
            ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
        params + [limit, offset],
    )

    items = []
    for row in cursor.fetchall():
        items.append(
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "query": row["query"],
                "provider": row["provider"],
                "companies_mentioned": json.loads(row["companies_mentioned"] or "[]"),
                "sentiment": row["sentiment"],
                "ugc_percentage": row["ugc_percentage"],
                "owned_percentage": row["owned_percentage"],
                "authority_percentage": row["authority_percentage"],
            }
        )

    conn.close()
    return {"items": items, "total": total, "page": page, "limit": limit}


def get_domain_trends() -> list[dict]:
    """Get domain trend data."""
    if not DATABASE_PATH.exists():
        return []

    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """SELECT week_start, domain, category, platform, appearance_count, percentage, wow_change
           FROM domain_trends ORDER BY week_start DESC, appearance_count DESC LIMIT 100"""
    )

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_competitor_mentions() -> list[dict]:
    """Get competitor mention data."""
    if not DATABASE_PATH.exists():
        return []

    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """SELECT timestamp, query, provider, competitor_name, mention_context, sentiment
           FROM competitor_mentions ORDER BY timestamp DESC LIMIT 100"""
    )

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def generate_weekly_report() -> Optional[str]:
    """Generate a weekly report. Returns the report path or None."""
    if not ANALYZER_AVAILABLE or not TRACKER_AVAILABLE or not REPORTER_AVAILABLE:
        return None

    import os
    os.environ["ENABLE_ENHANCED_ANALYSIS"] = "true"
    os.environ["TRACK_HISTORY"] = "true"
    os.environ["WEEKLY_REPORTING"] = "true"

    analyzer = ResponseAnalyzer()
    if analyzer.tracker and analyzer.reporter:
        return analyzer.generate_weekly_report()
    return None
