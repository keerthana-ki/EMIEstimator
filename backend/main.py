from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException

from . import auth, bootstrap, database
from .loan_math import compute_emi
from .models import (
    AdminPasswordReset,
    BootstrapStatus,
    ChangePasswordRequest,
    LoanInput,
    LoanResult,
    LoginRequest,
    LoginResponse,
    PasswordChangeLogEntry,
    PermissionUpdate,
    SavedCalculation,
    UserCreate,
    UserOut,
)

app = FastAPI(title="EMI Estimator API")


@app.on_event("startup")
def on_startup():
    database.init_db()
    bootstrap.run_bootstrap_if_needed()


@app.get("/auth/bootstrap-status", response_model=BootstrapStatus)
def bootstrap_status():
    info = bootstrap.BOOTSTRAP_INFO
    if info is None:
        return BootstrapStatus(just_created=False)
    return BootstrapStatus(just_created=True, username=info["username"], password=info["password"])


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = database.get_user_by_username(payload.username)
    if user is None or not auth.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_session(user)
    session = auth.SESSIONS[token]
    return LoginResponse(
        token=token,
        username=session["username"],
        role=session["role"],
        loan_types=session["loan_types"],
    )


@app.post("/auth/change-password")
def change_password(payload: ChangePasswordRequest, current_user: dict = Depends(auth.get_current_user)):
    user = database.get_user_by_id(current_user["user_id"])
    if user is None or not auth.verify_password(payload.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    database.update_password(current_user["user_id"], auth.hash_password(payload.new_password))
    database.log_password_change(
        target_username=current_user["username"],
        changed_by_username=current_user["username"],
        changed_by_role=current_user["role"],
        changed_at=datetime.now(timezone.utc).isoformat(),
    )
    return {"ok": True}


@app.post("/calculate", response_model=LoanResult)
def calculate(payload: LoanInput, current_user: dict = Depends(auth.get_current_user)):
    """Compute EMI without persisting it — used for live preview."""
    auth.check_loan_permission(current_user, payload.loan_type)
    figures = compute_emi(payload.amount, payload.rate, payload.tenure_years)
    return LoanResult(
        amount=payload.amount,
        rate=payload.rate,
        tenure_years=payload.tenure_years,
        loan_type=payload.loan_type,
        **figures,
    )


@app.post("/calculations", response_model=SavedCalculation)
def save_calculation(payload: LoanInput, current_user: dict = Depends(auth.get_current_user)):
    """Compute EMI and persist it to history."""
    auth.check_loan_permission(current_user, payload.loan_type)
    figures = compute_emi(payload.amount, payload.rate, payload.tenure_years)
    record = {
        "amount": payload.amount,
        "rate": payload.rate,
        "tenure_years": payload.tenure_years,
        "loan_type": payload.loan_type,
        "user_id": current_user["user_id"],
        **figures,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    new_id = database.insert_calculation(record)
    return SavedCalculation(id=new_id, **record)


@app.get("/calculations", response_model=list[SavedCalculation])
def get_history(current_user: dict = Depends(auth.get_current_user)):
    allowed_types = auth.ALL_LOAN_TYPES if current_user["role"] == "admin" else current_user["loan_types"]
    return database.list_calculations(loan_types=allowed_types)


@app.delete("/calculations/{calc_id}")
def remove_calculation(calc_id: int, current_user: dict = Depends(auth.get_current_user)):
    record = database.get_calculation(calc_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Calculation not found")
    auth.check_loan_permission(current_user, record["loan_type"])
    database.delete_calculation(calc_id)
    return {"ok": True}


@app.post("/admin/users", response_model=UserOut)
def create_user(payload: UserCreate, _admin: dict = Depends(auth.require_admin)):
    if database.get_user_by_username(payload.username) is not None:
        raise HTTPException(status_code=409, detail="Username already exists")
    user_id = database.create_user(
        username=payload.username,
        password_hash=auth.hash_password(payload.password),
        role="user",
        loan_types=payload.loan_types,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return UserOut(id=user_id, username=payload.username, role="user", loan_types=payload.loan_types)


@app.get("/admin/users", response_model=list[UserOut])
def get_users(_admin: dict = Depends(auth.require_admin)):
    return [
        UserOut(id=u["id"], username=u["username"], role=u["role"], loan_types=u["loan_types"])
        for u in database.list_users()
    ]


@app.patch("/admin/users/{user_id}/permissions", response_model=UserOut)
def update_permissions(user_id: int, payload: PermissionUpdate, _admin: dict = Depends(auth.require_admin)):
    user = database.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    database.set_user_permissions(user_id, payload.loan_types)
    return UserOut(id=user_id, username=user["username"], role=user["role"], loan_types=payload.loan_types)


@app.patch("/admin/users/{user_id}/password")
def admin_reset_password(user_id: int, payload: AdminPasswordReset, admin: dict = Depends(auth.require_admin)):
    user = database.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    database.update_password(user_id, auth.hash_password(payload.new_password))
    auth.invalidate_sessions_for_user(user_id)
    database.log_password_change(
        target_username=user["username"],
        changed_by_username=admin["username"],
        changed_by_role=admin["role"],
        changed_at=datetime.now(timezone.utc).isoformat(),
    )
    return {"ok": True}


@app.get("/admin/password-log", response_model=list[PasswordChangeLogEntry])
def get_password_log(_admin: dict = Depends(auth.require_admin)):
    return database.list_password_change_log()


@app.delete("/admin/users/{user_id}")
def delete_user(user_id: int, _admin: dict = Depends(auth.require_admin)):
    user = database.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] == "admin":
        raise HTTPException(status_code=403, detail="Admin accounts cannot be deleted")
    auth.invalidate_sessions_for_user(user_id)
    database.delete_user(user_id)
    return {"ok": True}
