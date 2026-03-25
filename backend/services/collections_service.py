"""Saved searches / collections persistence using SQLite."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional

from backend.config import COLLECTIONS_DB

DB_PATH = str(COLLECTIONS_DB)


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_searches (
            id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            result_filename TEXT NOT NULL,
            tags TEXT DEFAULT '[]',
            pinned INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    return conn


def list_saved(tag: Optional[str] = None, pinned_only: bool = False) -> list[dict]:
    conn = _get_db()
    try:
        sql = "SELECT * FROM saved_searches"
        params: list = []
        conditions = []

        if pinned_only:
            conditions.append("pinned = 1")
        if tag:
            conditions.append("tags LIKE ?")
            params.append(f'%"{tag}"%')

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY pinned DESC, updated_at DESC"
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def save_search(result_filename: str, query: str, tags: list[str] = None, notes: str = "", pinned: bool = False) -> dict:
    conn = _get_db()
    try:
        # Check if already saved
        existing = conn.execute(
            "SELECT id FROM saved_searches WHERE result_filename = ?",
            (result_filename,),
        ).fetchone()
        if existing:
            return update_search(existing["id"], tags=tags, notes=notes, pinned=pinned)

        item_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO saved_searches (id, query, result_filename, tags, pinned, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (item_id, query, result_filename, json.dumps(tags or []), int(pinned), notes, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM saved_searches WHERE id = ?", (item_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def update_search(item_id: str, tags: list[str] = None, notes: str = None, pinned: bool = None) -> dict:
    conn = _get_db()
    try:
        updates = []
        params: list = []
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if pinned is not None:
            updates.append("pinned = ?")
            params.append(int(pinned))

        if not updates:
            row = conn.execute("SELECT * FROM saved_searches WHERE id = ?", (item_id,)).fetchone()
            return _row_to_dict(row) if row else {}

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(item_id)

        conn.execute(f"UPDATE saved_searches SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        row = conn.execute("SELECT * FROM saved_searches WHERE id = ?", (item_id,)).fetchone()
        return _row_to_dict(row) if row else {}
    finally:
        conn.close()


def delete_search(item_id: str) -> bool:
    conn = _get_db()
    try:
        cursor = conn.execute("DELETE FROM saved_searches WHERE id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_all_tags() -> list[str]:
    conn = _get_db()
    try:
        rows = conn.execute("SELECT tags FROM saved_searches").fetchall()
        tag_set: set[str] = set()
        for row in rows:
            for tag in json.loads(row["tags"]):
                tag_set.add(tag)
        return sorted(tag_set)
    finally:
        conn.close()


def is_saved(result_filename: str) -> Optional[str]:
    """Return the saved search id if the filename is saved, else None."""
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT id FROM saved_searches WHERE result_filename = ?",
            (result_filename,),
        ).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "query": row["query"],
        "result_filename": row["result_filename"],
        "tags": json.loads(row["tags"]),
        "pinned": bool(row["pinned"]),
        "notes": row["notes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
