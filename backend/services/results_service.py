"""Reads results/ JSON files and tracking.db for historical browsing."""

import json
import os
from pathlib import Path
from typing import Optional

from backend.config import RESULTS_DIR, REPORTS_DIR, DATABASE_PATH


def list_results(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
) -> dict:
    """List result files with metadata, paginated."""
    if not RESULTS_DIR.exists():
        return {"items": [], "total": 0, "page": page, "limit": limit}

    files = sorted(RESULTS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)

    items = []
    for f in files:
        try:
            with open(f) as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, IOError):
            continue

        name = f.stem
        is_batch = name.startswith("batch_summary_")

        if is_batch:
            query_text = ", ".join(data.get("queries_run", ["Batch"])[:2])
            if len(data.get("queries_run", [])) > 2:
                query_text += f" (+{len(data['queries_run']) - 2} more)"
            results_list = data.get("all_results", [])
            provider_count = len(results_list[0].get("results", [])) if results_list else 0
            has_analysis = any(
                r.get("analysis")
                for batch in results_list
                for r in batch.get("results", [])
            )
        else:
            query_text = data.get("query", "Unknown")
            results_list = data.get("results", [])
            provider_count = len(results_list)
            has_analysis = any(r.get("analysis") for r in results_list)

        items.append(
            {
                "filename": f.name,
                "query": query_text,
                "timestamp": data.get("timestamp", data.get("batch_timestamp")),
                "is_batch": is_batch,
                "provider_count": provider_count,
                "has_analysis": has_analysis,
            }
        )

    if search:
        search_lower = search.lower()
        items = [i for i in items if search_lower in i["query"].lower()]

    total = len(items)
    start = (page - 1) * limit
    return {
        "items": items[start : start + limit],
        "total": total,
        "page": page,
        "limit": limit,
    }


def get_result(filename: str) -> Optional[dict]:
    """Get a specific result file's contents."""
    filepath = RESULTS_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        return None
    # Prevent path traversal
    if not filepath.resolve().parent == RESULTS_DIR.resolve():
        return None
    with open(filepath) as f:
        return json.load(f)


def list_reports() -> list[dict]:
    """List generated report files."""
    if not REPORTS_DIR.exists():
        return []

    reports = []
    for f in sorted(REPORTS_DIR.glob("*.md"), key=os.path.getmtime, reverse=True):
        reports.append({"filename": f.name, "size": f.stat().st_size})
    return reports


def get_report(filename: str) -> Optional[str]:
    """Get a specific report's markdown content."""
    filepath = REPORTS_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        return None
    if not filepath.resolve().parent == REPORTS_DIR.resolve():
        return None
    return filepath.read_text()
