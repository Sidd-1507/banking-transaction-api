"""Account business logic — creation, retrieval, validation."""

import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Account, AccountType, AuditLog, User


def create_account(
    db: Session, user: User, account_type: str, ip_address: str = "unknown"
) -> Account:
    """Create a new bank account for the given user."""
    account = Account(
        user_id=user.id,
        account_type=AccountType(account_type),
        balance=0.0,
    )
    db.add(account)
    db.flush()  # Get the generated ID and account_number

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="ACCOUNT_CREATED",
        resource="account",
        details=json.dumps({
            "account_id": account.id,
            "account_number": account.account_number,
            "account_type": account_type,
        }),
        ip_address=ip_address,
    )
    db.add(audit)
    db.commit()
    db.refresh(account)
    return account


def get_user_accounts(db: Session, user_id: int) -> list[Account]:
    """Retrieve all accounts belonging to a user."""
    return (
        db.query(Account)
        .filter(Account.user_id == user_id, Account.is_active == True)
        .all()
    )


def get_account_by_id(db: Session, account_id: int, user_id: int) -> Account:
    """Retrieve a specific account, ensuring it belongs to the requesting user."""
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.user_id == user_id,
            Account.is_active == True,
        )
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found or access denied",
        )
    return account
