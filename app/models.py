"""SQLAlchemy ORM models for the Banking API."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


def generate_account_number():
    """Generate a unique 12-digit account number."""
    return str(uuid.uuid4().int)[:12]


class AccountType(str, enum.Enum):
    """Types of bank accounts."""
    SAVINGS = "SAVINGS"
    CHECKING = "CHECKING"
    CURRENT = "CURRENT"


class TransactionType(str, enum.Enum):
    """Types of transactions."""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------
class User(Base):
    """Registered user of the banking system."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    accounts = relationship("Account", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")


# ---------------------------------------------------------------------------
# Account model
# ---------------------------------------------------------------------------
class Account(Base):
    """Bank account belonging to a user."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(
        String(12), unique=True, index=True, default=generate_account_number
    )
    account_type = Column(Enum(AccountType), default=AccountType.SAVINGS)
    balance = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="accounts")
    transactions = relationship(
        "Transaction", back_populates="account",
        foreign_keys="[Transaction.account_id]",
    )


# ---------------------------------------------------------------------------
# Transaction model
# ---------------------------------------------------------------------------
class Transaction(Base):
    """Record of a financial transaction on an account."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    description = Column(String(500), default="")
    related_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # Foreign key
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    # Relationships
    account = relationship("Account", back_populates="transactions", foreign_keys=[account_id])


# ---------------------------------------------------------------------------
# Audit Log model — records every significant action for compliance
# ---------------------------------------------------------------------------
class AuditLog(Base):
    """Immutable audit trail for compliance and security monitoring."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)  # e.g., "DEPOSIT", "LOGIN"
    resource = Column(String(100), nullable=False)  # e.g., "account", "user"
    details = Column(Text, default="")  # JSON string with extra context
    ip_address = Column(String(45), default="unknown")
    timestamp = Column(DateTime, default=utcnow)

    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
