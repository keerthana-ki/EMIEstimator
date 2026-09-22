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

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT UNIQUE,
            full_name TEXT NOT NULL,
            designation TEXT,
            department TEXT,
            email TEXT,
            phone TEXT,
            date_of_joining TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            extra_json TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS employee_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            content_type TEXT,
            size_bytes INTEGER,
            uploaded_by INTEGER REFERENCES users(id),
            uploaded_at TEXT NOT NULL,
            deleted_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS employee_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER REFERENCES employees(id),
            action TEXT NOT NULL,
            field_changed TEXT,
            old_value TEXT,
            new_value TEXT,
            performed_by_username TEXT NOT NULL,
            performed_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS employee_import_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            imported_by INTEGER REFERENCES users(id),
            imported_at TEXT NOT NULL,
            row_count INTEGER,
            status TEXT NOT NULL
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


_EMPLOYEE_UPDATABLE_FIELDS = [
    "employee_code",
    "full_name",
    "designation",
    "department",
    "email",
    "phone",
    "date_of_joining",
    "status",
]


def _insert_employee_audit_log(
    conn,
    employee_id: Optional[int],
    action: str,
    field_changed: Optional[str],
    old_value: Optional[str],
    new_value: Optional[str],
    performed_by_username: str,
    performed_at: str,
) -> None:
    """Writes one audit row on the caller's connection — the caller commits.
    Never called directly from route bodies; only ever a side effect of the
    employee CRUD functions below, so audit rows stay server-authored."""
    conn.execute(
        """
        INSERT INTO employee_audit_log
            (employee_id, action, field_changed, old_value, new_value, performed_by_username, performed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (employee_id, action, field_changed, old_value, new_value, performed_by_username, performed_at),
    )


def get_employee_by_code(employee_code: str) -> Optional[dict]:
    """Matches the DB-level UNIQUE constraint on employee_code exactly — this
    includes soft-deleted (recycle bin) rows, so a code stays reserved until
    its employee is restored (freeing nothing) or permanently deleted (freeing it)."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM employees WHERE employee_code = ?", (employee_code,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_employee(fields: dict, created_by: Optional[int], performed_by_username: str, created_at: str) -> dict:
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO employees
            (employee_code, full_name, designation, department, email, phone,
             date_of_joining, status, created_by, created_at, updated_at)
        VALUES
            (:employee_code, :full_name, :designation, :department, :email, :phone,
             :date_of_joining, :status, :created_by, :created_at, :updated_at)
        """,
        {**fields, "created_by": created_by, "created_at": created_at, "updated_at": created_at},
    )
    employee_id = cursor.lastrowid
    _insert_employee_audit_log(conn, employee_id, "created", None, None, None, performed_by_username, created_at)
    conn.commit()
    row = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    conn.close()
    return dict(row)


def get_employee(employee_id: int) -> Optional[dict]:
    """Returns the employee regardless of soft-delete state (recycle bin included)."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_employees(search: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM employees WHERE deleted_at IS NULL"
    params: list = []
    if search:
        like = f"%{search}%"
        query += " AND (full_name LIKE ? OR employee_code LIKE ? OR department LIKE ?)"
        params += [like, like, like]
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY full_name ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_deleted_employees() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM employees WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_employee(employee_id: int, changes: dict, performed_by_username: str, updated_at: str) -> Optional[dict]:
    conn = get_connection()
    current_row = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if current_row is None:
        conn.close()
        return None
    current = dict(current_row)

    # Column names come only from this fixed whitelist, never from arbitrary client keys.
    fields_to_set = {k: v for k, v in changes.items() if k in _EMPLOYEE_UPDATABLE_FIELDS}
    diffs = [(k, current.get(k), v) for k, v in fields_to_set.items() if current.get(k) != v]

    if fields_to_set:
        set_clause = ", ".join(f"{col} = ?" for col in fields_to_set)
        values = list(fields_to_set.values()) + [updated_at, employee_id]
        conn.execute(f"UPDATE employees SET {set_clause}, updated_at = ? WHERE id = ?", values)
        for field_changed, old_value, new_value in diffs:
            _insert_employee_audit_log(
                conn,
                employee_id,
                "updated",
                field_changed,
                None if old_value is None else str(old_value),
                None if new_value is None else str(new_value),
                performed_by_username,
                updated_at,
            )

    conn.commit()
    row = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    conn.close()
    return dict(row)


def soft_delete_employee(employee_id: int, performed_by_username: str, deleted_at: str) -> bool:
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE employees SET deleted_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
        (deleted_at, deleted_at, employee_id),
    )
    deleted = cursor.rowcount > 0
    if deleted:
        _insert_employee_audit_log(conn, employee_id, "deleted", None, None, None, performed_by_username, deleted_at)
    conn.commit()
    conn.close()
    return deleted


def restore_employee(employee_id: int, performed_by_username: str, restored_at: str) -> bool:
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE employees SET deleted_at = NULL, updated_at = ? WHERE id = ? AND deleted_at IS NOT NULL",
        (restored_at, employee_id),
    )
    restored = cursor.rowcount > 0
    if restored:
        _insert_employee_audit_log(conn, employee_id, "restored", None, None, None, performed_by_username, restored_at)
    conn.commit()
    conn.close()
    return restored


def permanently_delete_employee(employee_id: int, performed_by_username: str, performed_at: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM employees WHERE id = ? AND deleted_at IS NOT NULL", (employee_id,)
    ).fetchone()
    if row is None:
        conn.close()
        return False

    # Write the final audit entry, then detach ALL of this employee's audit history
    # (including the row just written) by nulling employee_id — otherwise the FK
    # from employee_audit_log to employees (with PRAGMA foreign_keys=ON) would
    # block the DELETE below. Mirrors delete_user()'s calculations.user_id nulling.
    _insert_employee_audit_log(
        conn, employee_id, "permanently_deleted", None, None, None, performed_by_username, performed_at
    )
    conn.execute("UPDATE employee_audit_log SET employee_id = NULL WHERE employee_id = ?", (employee_id,))
    conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    conn.commit()
    conn.close()
    return True


def get_employee_audit_log(employee_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM employee_audit_log WHERE employee_id = ? ORDER BY id DESC", (employee_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_all_employee_audit_log(limit: int = 100) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM employee_audit_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
