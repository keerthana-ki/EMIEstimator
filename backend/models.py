from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

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


EmployeeStatus = Literal["active", "inactive"]


class EmployeeBase(BaseModel):
    full_name: str = Field(min_length=1)
    employee_code: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_joining: Optional[str] = None
    status: EmployeeStatus = "active"

    @field_validator("full_name")
    @classmethod
    def _strip_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("full_name must not be blank")
        return v

    @field_validator("employee_code", "email", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        if v is None:
            return None
        v = v.strip()
        return v or None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    employee_code: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_joining: Optional[str] = None
    status: Optional[EmployeeStatus] = None

    @field_validator("full_name")
    @classmethod
    def _strip_full_name(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("full_name must not be blank")
        return v

    @field_validator("employee_code", "email", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        if v is None:
            return None
        v = v.strip()
        return v or None


class EmployeeOut(EmployeeBase):
    id: int
    created_by: Optional[int] = None
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None


class EmployeeAttachmentOut(BaseModel):
    id: int
    employee_id: int
    filename: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    uploaded_by: Optional[int] = None
    uploaded_at: str


class EmployeeAuditLogEntry(BaseModel):
    id: int
    employee_id: Optional[int] = None
    action: str
    field_changed: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    performed_by_username: str
    performed_at: str


class EmployeeImportBatchOut(BaseModel):
    id: int
    filename: str
    imported_by: Optional[int] = None
    imported_at: str
    row_count: Optional[int] = None
    status: str
