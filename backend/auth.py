import secrets

import bcrypt
from fastapi import Depends, Header, HTTPException

from . import database

SESSIONS: dict[str, dict] = {}

ALL_LOAN_TYPES = ["home", "car"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_session(user: dict) -> str:
    token = secrets.token_urlsafe(32)
    loan_types = ALL_LOAN_TYPES if user["role"] == "admin" else database.get_user_permissions(user["id"])
    SESSIONS[token] = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "loan_types": loan_types,
    }
    return token


def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    session = SESSIONS.get(token)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return session


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def invalidate_sessions_for_user(user_id: int) -> None:
    stale_tokens = [token for token, session in SESSIONS.items() if session["user_id"] == user_id]
    for token in stale_tokens:
        del SESSIONS[token]


def check_loan_permission(current_user: dict, loan_type: str) -> None:
    """Call this from inside a route body once the request's loan_type is known
    (it lives in the request payload, not the URL/headers, so it can't be a
    Depends(...) dependency the way get_current_user/require_admin are)."""
    if current_user["role"] == "admin":
        return
    if loan_type not in current_user["loan_types"]:
        raise HTTPException(status_code=403, detail=f"No access to {loan_type} loans")
