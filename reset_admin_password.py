"""
Standalone password recovery tool.

Resets a user's password directly in the database — completely independent
of the running app, the backend API, or any login. Use this if the sole
admin account ever gets locked out (forgotten password) with no other admin
around to reset it through the normal Admin tab.

Run from Terminal, from the project folder:
    ./venv/bin/python3 reset_admin_password.py

Quit the real app first if it's currently running, so nothing is writing to
the database at the same time as this script.
"""
import argparse
import getpass
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import bcrypt

PACKAGED_DB = Path(os.path.expanduser("~/Library/Application Support/HomeLoanCalculator/app_data.db"))
DEV_DB = Path(__file__).resolve().parent / "app_data.db"


def resolve_db_path(explicit: Optional[str]) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.exists():
            sys.exit(f"No database found at {path}")
        return path
    if PACKAGED_DB.exists():
        print(f"Using your real Desktop app's database:\n  {PACKAGED_DB}\n")
        return PACKAGED_DB
    if DEV_DB.exists():
        print(f"Using the dev/test database:\n  {DEV_DB}\n")
        return DEV_DB
    sys.exit(
        "No database found in either the packaged app location or the project folder.\n"
        "Have you run the app at least once?"
    )


def main():
    parser = argparse.ArgumentParser(description="Reset a user's password directly in the database.")
    parser.add_argument("--db", help="Explicit path to loan_history.db (overrides auto-detection)")
    args = parser.parse_args()

    print("Make sure the Home Loan Calculator app is fully quit before continuing.\n")

    db_path = resolve_db_path(args.db)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    users = conn.execute("SELECT id, username, role FROM users ORDER BY id").fetchall()
    if not users:
        sys.exit("No users found in this database.")

    print("Existing accounts:")
    for user in users:
        print(f"  [{user['id']}] {user['username']}  ({user['role']})")
    print()

    choice = input("Enter the exact username to reset: ").strip()
    target = next((u for u in users if u["username"] == choice), None)
    if target is None:
        sys.exit(f'No user named "{choice}" found.')

    new_password = getpass.getpass(f"New password for {target['username']}: ")
    confirm = getpass.getpass("Confirm new password: ")
    if not new_password:
        sys.exit("Password cannot be empty — nothing was changed.")
    if new_password != confirm:
        sys.exit("Passwords didn't match — nothing was changed.")

    password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, target["id"]))
    conn.commit()
    print(f'\nDone — password for "{target["username"]}" has been reset.')
    print("Launch the app and log in with the new password.")

    # Best-effort audit trail — the password reset above already succeeded and
    # was committed, so a problem here must never look like the reset failed.
    try:
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
            "INSERT INTO password_change_log (target_username, changed_by_username, changed_by_role, changed_at) "
            "VALUES (?, ?, ?, ?)",
            (target["username"], "[recovery script]", "admin", datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        print('This was recorded in the Admin tab\'s password log as "[recovery script]".')
    except sqlite3.Error as exc:
        print(f"(Note: could not write to the password audit log — {exc}. The password reset itself is unaffected.)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
