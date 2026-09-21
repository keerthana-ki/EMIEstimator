from typing import Literal, Optional

from pydantic import BaseModel, Field

LoanType = Literal["home", "car"]
Role = Literal["admin", "user"]


class LoanInput(BaseModel):
    amount: float = Field(gt=0)
    rate: float = Field(ge=0)
    tenure_years: float = Field(gt=0, le=40)
    loan_type: LoanType


class LoanResult(BaseModel):
    amount: float
    rate: float
    tenure_years: float
    loan_type: LoanType
    emi: float
    total_interest: float
    total_payment: float


class SavedCalculation(LoanResult):
    id: int
    created_at: str
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: Role
    loan_types: list[LoanType]


class BootstrapStatus(BaseModel):
    just_created: bool
    username: Optional[str] = None
    password: Optional[str] = None


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    loan_types: list[LoanType]


class UserOut(BaseModel):
    id: int
    username: str
    role: Role
    loan_types: list[LoanType]


class PermissionUpdate(BaseModel):
    loan_types: list[LoanType]


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=1)


class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=1)


class PasswordChangeLogEntry(BaseModel):
    target_username: str
    changed_by_username: str
    changed_by_role: Role
    changed_at: str
