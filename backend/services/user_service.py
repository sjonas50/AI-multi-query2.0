"""User accounts and invite codes — SQLite + bcrypt."""

import secrets
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt

from backend.config import USERS_DB, ADMIN_EMAIL, ADMIN_PASSWORD


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(USERS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables and seed admin if no users exist."""
    conn = _get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invite_codes (
                code TEXT PRIMARY KEY,
                created_by TEXT NOT NULL,
                email TEXT,
                used_by TEXT,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        conn.commit()

        # Seed admin if no users exist
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0 and ADMIN_EMAIL and ADMIN_PASSWORD:
            _insert_user(conn, ADMIN_EMAIL, ADMIN_PASSWORD, "Admin", "admin")
            conn.commit()
    finally:
        conn.close()


def _insert_user(conn: sqlite3.Connection, email: str, password: str, display_name: str, role: str = "user") -> dict:
    user_id = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO users (id, email, password_hash, display_name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, email.lower().strip(), pw_hash, display_name, role, now),
    )
    return {"id": user_id, "email": email.lower().strip(), "display_name": display_name, "role": role, "created_at": now}


def create_user(email: str, password: str, display_name: str, role: str = "user") -> dict:
    conn = _get_db()
    try:
        user = _insert_user(conn, email, password, display_name, role)
        conn.commit()
        return user
    finally:
        conn.close()


def authenticate(email: str, password: str) -> Optional[dict]:
    """Return user dict if credentials valid, else None."""
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        if not row:
            return None
        if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            return None
        # Update last_login
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))
        conn.commit()
        return _user_to_dict(row)
    finally:
        conn.close()


def get_user(user_id: str) -> Optional[dict]:
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user_to_dict(row) if row else None
    finally:
        conn.close()


def list_users() -> list[dict]:
    conn = _get_db()
    try:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [_user_to_dict(r) for r in rows]
    finally:
        conn.close()


def delete_user(user_id: str) -> bool:
    conn = _get_db()
    try:
        cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# --- Invite codes ---


def create_invite(admin_id: str, email: Optional[str] = None, expires_hours: int = 72) -> str:
    """Generate an invite code. Optionally lock to a specific email."""
    code = secrets.token_urlsafe(8)  # ~11 chars, URL-safe
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=expires_hours)).isoformat()
    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO invite_codes (code, created_by, email, expires_at) VALUES (?, ?, ?, ?)",
            (code, admin_id, email.lower().strip() if email else None, expires_at),
        )
        conn.commit()
        return code
    finally:
        conn.close()


def redeem_invite(code: str, email: str, password: str, display_name: str) -> dict:
    """Redeem an invite code and create a new user. Raises ValueError on failure."""
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM invite_codes WHERE code = ?", (code,)).fetchone()
        if not row:
            raise ValueError("Invalid invite code")
        if row["used_by"]:
            raise ValueError("Invite code already used")
        if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
            raise ValueError("Invite code expired")
        if row["email"] and row["email"] != email.lower().strip():
            raise ValueError("Invite code is locked to a different email")

        # Check if email already exists
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        if existing:
            raise ValueError("Email already registered")

        user = _insert_user(conn, email, password, display_name)
        conn.execute(
            "UPDATE invite_codes SET used_by = ?, used_at = ? WHERE code = ?",
            (user["id"], datetime.now(timezone.utc).isoformat(), code),
        )
        conn.commit()
        return user
    finally:
        conn.close()


def list_invites() -> list[dict]:
    conn = _get_db()
    try:
        rows = conn.execute("""
            SELECT ic.*, u.email as creator_email
            FROM invite_codes ic
            JOIN users u ON ic.created_by = u.id
            ORDER BY ic.expires_at DESC
        """).fetchall()
        return [_invite_to_dict(r) for r in rows]
    finally:
        conn.close()


def delete_invite(code: str) -> bool:
    conn = _get_db()
    try:
        cursor = conn.execute("DELETE FROM invite_codes WHERE code = ? AND used_by IS NULL", (code,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def _user_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "role": row["role"],
        "created_at": row["created_at"],
        "last_login": row["last_login"],
    }


def _invite_to_dict(row: sqlite3.Row) -> dict:
    return {
        "code": row["code"],
        "created_by": row["created_by"],
        "creator_email": row["creator_email"],
        "email": row["email"],
        "used_by": row["used_by"],
        "expires_at": row["expires_at"],
        "used_at": row["used_at"],
        "active": row["used_by"] is None and datetime.fromisoformat(row["expires_at"]) > datetime.now(timezone.utc),
    }
