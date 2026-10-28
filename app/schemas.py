"""Pydantic schemas for request validation and response serialization."""

from datetime import datetime
from typing import Optional

import re

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    """Schema for user registration."""
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email address")
        return v.lower()


class UserLogin(BaseModel):
    """Schema for user login."""
    email: str
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user information."""
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Account schemas
# ---------------------------------------------------------------------------
class AccountCreate(BaseModel):
    """Schema for creating a new bank account."""
    account_type: str = Field(
        default="SAVINGS",
        description="Account type: SAVINGS, CHECKING, or CURRENT",
    )

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        allowed = {"SAVINGS", "CHECKING", "CURRENT"}
        if v.upper() not in allowed:
            raise ValueError(f"account_type must be one of: {allowed}")
        return v.upper()


class AccountResponse(BaseModel):
    """Account details returned to the user."""
    id: int
    account_number: str
    account_type: str
    balance: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Transaction schemas
# ---------------------------------------------------------------------------
class DepositRequest(BaseModel):
    """Schema for depositing funds."""
    account_id: int
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")
    description: Optional[str] = "Cash deposit"


class WithdrawRequest(BaseModel):
    """Schema for withdrawing funds."""
    account_id: int
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")
    description: Optional[str] = "Cash withdrawal"


class TransferRequest(BaseModel):
    """Schema for transferring funds between accounts."""
    from_account_id: int
    to_account_id: int
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")
    description: Optional[str] = "Fund transfer"

    @field_validator("to_account_id")
    @classmethod
    def accounts_must_differ(cls, v: int, info) -> int:
        if "from_account_id" in info.data and v == info.data["from_account_id"]:
            raise ValueError("Cannot transfer to the same account")
        return v


class TransactionResponse(BaseModel):
    """Transaction record returned to the user."""
    id: int
    transaction_type: str
    amount: float
    balance_after: float
    description: str
    related_account_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Audit log schemas
# ---------------------------------------------------------------------------
class AuditLogResponse(BaseModel):
    """Audit log entry returned to the user."""
    id: int
    action: str
    resource: str
    details: str
    ip_address: str
    timestamp: datetime

    model_config = {"from_attributes": True}
