import secrets
from datetime import datetime, timezone
from typing import Optional

from . import database
from .auth import ALL_LOAN_TYPES, hash_password

BOOTSTRAP_INFO: Optional[dict] = None


def run_bootstrap_if_needed() -> None:
    global BOOTSTRAP_INFO
    if database.count_users() > 0:
        return

    password = secrets.token_urlsafe(9)
    database.create_user(
        username="admin",
        password_hash=hash_password(password),
        role="admin",
        loan_types=ALL_LOAN_TYPES,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    BOOTSTRAP_INFO = {"username": "admin", "password": password}
    print(f"[bootstrap] Created first admin account — username: admin, password: {password}")
