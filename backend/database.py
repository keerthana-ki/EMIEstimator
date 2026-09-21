import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional

if getattr(sys, "frozen", False):
    # Packaged app — keep data in the standard macOS per-user app data folder,
    # not inside the (read-only, ephemeral-on-update) app bundle itself.
    _DATA_DIR = Path(os.path.expanduser("~/Library/Application Support/HomeLoanCalculator"))
else:
    _DATA_DIR = Path(__file__).resolve().parent.parent

_DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = _DATA_DIR / "app_data.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _table_columns(conn, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def init_db():
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            rate REAL NOT NULL,
            tenure_years REAL NOT NULL,
            emi REAL NOT NULL,
            total_interest REAL NOT NULL,
            total_payment REAL NOT NULL,
            created_at TEXT NOT NULL,
            loan_type TEXT NOT NULL DEFAULT 'home',
            user_id INTEGER REFERENCES users(id)
        )
        """
    )
    existing_columns = _table_columns(conn, "calculations")
    if "loan_type" not in existing_columns:
        conn.execute("ALTER TABLE calculations ADD COLUMN loan_type TEXT NOT NULL DEFAULT 'home'")
    if "user_id" not in existing_columns:
        conn.execute("ALTER TABLE calculations ADD COLUMN user_id INTEGER REFERENCES users(id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_permissions (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            loan_type TEXT NOT NULL,
            PRIMARY KEY (user_id, loan_type)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS password_change_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_username TEXT NOT NULL,
            changed_by_username TEXT NOT NULL,
            changed_by_role TEXT NOT NULL,
            changed_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def insert_calculation(record: dict) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO calculations
            (amount, rate, tenure_years, emi, total_interest, total_payment, created_at, loan_type, user_id)
        VALUES
            (:amount, :rate, :tenure_years, :emi, :total_interest, :total_payment, :created_at, :loan_type, :user_id)
        """,
        record,
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def list_calculations(loan_types: Optional[list[str]] = None) -> list[dict]:
    conn = get_connection()
    if loan_types is None:
        rows = conn.execute("SELECT * FROM calculations ORDER BY id DESC").fetchall()
    else:
        placeholders = ",".join("?" for _ in loan_types)
        rows = conn.execute(
            f"SELECT * FROM calculations WHERE loan_type IN ({placeholders}) ORDER BY id DESC",
            loan_types,
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_calculation(calc_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM calculations WHERE id = ?", (calc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_calculation(calc_id: int) -> bool:
    conn = get_connection()
    cursor = conn.execute("DELETE FROM calculations WHERE id = ?", (calc_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def count_users() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    conn.close()
    return row["n"]


def create_user(username: str, password_hash: str, role: str, loan_types: list[str], created_at: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (username, password_hash, role, created_at),
    )
    user_id = cursor.lastrowid
    conn.executemany(
        "INSERT INTO user_permissions (user_id, loan_type) VALUES (?, ?)",
        [(user_id, lt) for lt in loan_types],
    )
    conn.commit()
    conn.close()
    return user_id


def get_user_by_username(username: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_permissions(user_id: int) -> list[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT loan_type FROM user_permissions WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return [row["loan_type"] for row in rows]


def set_user_permissions(user_id: int, loan_types: list[str]) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM user_permissions WHERE user_id = ?", (user_id,))
    conn.executemany(
        "INSERT INTO user_permissions (user_id, loan_type) VALUES (?, ?)",
        [(user_id, lt) for lt in loan_types],
    )
    conn.commit()
    conn.close()


def update_password(user_id: int, password_hash: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
    conn.close()


def log_password_change(target_username: str, changed_by_username: str, changed_by_role: str, changed_at: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO password_change_log (target_username, changed_by_username, changed_by_role, changed_at) "
        "VALUES (?, ?, ?, ?)",
        (target_username, changed_by_username, changed_by_role, changed_at),
    )
    conn.commit()
    conn.close()


def list_password_change_log(limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM password_change_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_user(user_id: int) -> bool:
    conn = get_connection()
    conn.execute("UPDATE calculations SET user_id = NULL WHERE user_id = ?", (user_id,))
    cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def list_users() -> list[dict]:
    conn = get_connection()
    users = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
    result = []
    for user in users:
        perms = conn.execute(
            "SELECT loan_type FROM user_permissions WHERE user_id = ?", (user["id"],)
        ).fetchall()
        result.append({**dict(user), "loan_types": [p["loan_type"] for p in perms]})
    conn.close()
    return result
