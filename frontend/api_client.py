import requests

BASE_URL = "http://127.0.0.1:8731"

_session = {"token": None}


def set_token(token):
    _session["token"] = token


def _auth_headers():
    return {"Authorization": f"Bearer {_session['token']}"}


def get_bootstrap_status() -> dict:
    resp = requests.get(f"{BASE_URL}/auth/bootstrap-status", timeout=3)
    resp.raise_for_status()
    return resp.json()


def login(username: str, password: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=3,
    )
    resp.raise_for_status()
    data = resp.json()
    set_token(data["token"])
    return data


def calculate_preview(amount: float, rate: float, tenure_years: float, loan_type: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/calculate",
        json={"amount": amount, "rate": rate, "tenure_years": tenure_years, "loan_type": loan_type},
        headers=_auth_headers(),
        timeout=3,
    )
    resp.raise_for_status()
    return resp.json()


def save_calculation(amount: float, rate: float, tenure_years: float, loan_type: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/calculations",
        json={"amount": amount, "rate": rate, "tenure_years": tenure_years, "loan_type": loan_type},
        headers=_auth_headers(),
        timeout=3,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_history() -> list:
    resp = requests.get(f"{BASE_URL}/calculations", headers=_auth_headers(), timeout=3)
    resp.raise_for_status()
    return resp.json()


def delete_calculation(calc_id: int) -> None:
    resp = requests.delete(f"{BASE_URL}/calculations/{calc_id}", headers=_auth_headers(), timeout=3)
    resp.raise_for_status()


def list_users() -> list:
    resp = requests.get(f"{BASE_URL}/admin/users", headers=_auth_headers(), timeout=3)
    resp.raise_for_status()
    return resp.json()


def create_user(username: str, password: str, loan_types: list) -> dict:
    resp = requests.post(
        f"{BASE_URL}/admin/users",
        json={"username": username, "password": password, "loan_types": loan_types},
        headers=_auth_headers(),
        timeout=3,
    )
    resp.raise_for_status()
    return resp.json()


def update_user_permissions(user_id: int, loan_types: list) -> dict:
    resp = requests.patch(
        f"{BASE_URL}/admin/users/{user_id}/permissions",
        json={"loan_types": loan_types},
        headers=_auth_headers(),
        timeout=3,
    )
    resp.raise_for_status()
    return resp.json()


def delete_user(user_id: int) -> None:
    resp = requests.delete(f"{BASE_URL}/admin/users/{user_id}", headers=_auth_headers(), timeout=3)
    resp.raise_for_status()


def change_password(current_password: str, new_password: str) -> None:
    resp = requests.post(
        f"{BASE_URL}/auth/change-password",
        json={"current_password": current_password, "new_password": new_password},
        headers=_auth_headers(),
        timeout=3,
    )
    resp.raise_for_status()


def admin_reset_password(user_id: int, new_password: str) -> None:
    resp = requests.patch(
        f"{BASE_URL}/admin/users/{user_id}/password",
        json={"new_password": new_password},
        headers=_auth_headers(),
        timeout=3,
    )
    resp.raise_for_status()


def get_password_log() -> list:
    resp = requests.get(f"{BASE_URL}/admin/password-log", headers=_auth_headers(), timeout=3)
    resp.raise_for_status()
    return resp.json()
