"""Transaction business logic — deposit, withdraw, transfer with audit trail."""

import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Account, AuditLog, Transaction, TransactionType


def _get_active_account(db: Session, account_id: int, user_id: int) -> Account:
    """Retrieve an active account belonging to the user, or raise 404."""
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


def _log_audit(
    db: Session,
    user_id: int,
    action: str,
    resource: str,
    details: dict,
    ip_address: str = "unknown",
) -> None:
    """Create an immutable audit log entry."""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=json.dumps(details),
        ip_address=ip_address,
    )
    db.add(audit)


# ---------------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------------
def deposit(
    db: Session,
    user_id: int,
    account_id: int,
    amount: float,
    description: str = "Cash deposit",
    ip_address: str = "unknown",
) -> Transaction:
    """Deposit funds into an account."""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit amount must be greater than zero",
        )

    account = _get_active_account(db, account_id, user_id)

    # Update balance
    account.balance += amount
    new_balance = round(account.balance, 2)
    account.balance = new_balance

    # Create transaction record
    txn = Transaction(
        account_id=account.id,
        transaction_type=TransactionType.DEPOSIT,
        amount=amount,
        balance_after=new_balance,
        description=description,
    )
    db.add(txn)

    # Audit trail
    _log_audit(db, user_id, "DEPOSIT", "transaction", {
        "account_id": account_id,
        "amount": amount,
        "balance_after": new_balance,
    }, ip_address)

    db.commit()
    db.refresh(txn)
    return txn


# ---------------------------------------------------------------------------
# Withdraw
# ---------------------------------------------------------------------------
def withdraw(
    db: Session,
    user_id: int,
    account_id: int,
    amount: float,
    description: str = "Cash withdrawal",
    ip_address: str = "unknown",
) -> Transaction:
    """Withdraw funds from an account. Fails if insufficient balance."""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be greater than zero",
        )

    account = _get_active_account(db, account_id, user_id)

    if account.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Available: {account.balance}, Requested: {amount}",
        )

    # Update balance
    account.balance -= amount
    new_balance = round(account.balance, 2)
    account.balance = new_balance

    # Create transaction record
    txn = Transaction(
        account_id=account.id,
        transaction_type=TransactionType.WITHDRAWAL,
        amount=amount,
        balance_after=new_balance,
        description=description,
    )
    db.add(txn)

    # Audit trail
    _log_audit(db, user_id, "WITHDRAWAL", "transaction", {
        "account_id": account_id,
        "amount": amount,
        "balance_after": new_balance,
    }, ip_address)

    db.commit()
    db.refresh(txn)
    return txn


# ---------------------------------------------------------------------------
# Transfer
# ---------------------------------------------------------------------------
def transfer(
    db: Session,
    user_id: int,
    from_account_id: int,
    to_account_id: int,
    amount: float,
    description: str = "Fund transfer",
    ip_address: str = "unknown",
) -> tuple[Transaction, Transaction]:
    """Transfer funds between two accounts. Both must belong to the user."""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount must be greater than zero",
        )

    if from_account_id == to_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to the same account",
        )

    from_account = _get_active_account(db, from_account_id, user_id)
    to_account = _get_active_account(db, to_account_id, user_id)

    if from_account.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Available: {from_account.balance}, Requested: {amount}",
        )

    # Debit source account
    from_account.balance -= amount
    from_balance = round(from_account.balance, 2)
    from_account.balance = from_balance

    # Credit destination account
    to_account.balance += amount
    to_balance = round(to_account.balance, 2)
    to_account.balance = to_balance

    # Transaction records
    txn_out = Transaction(
        account_id=from_account_id,
        transaction_type=TransactionType.TRANSFER_OUT,
        amount=amount,
        balance_after=from_balance,
        description=f"{description} → Account {to_account.account_number}",
        related_account_id=to_account_id,
    )
    txn_in = Transaction(
        account_id=to_account_id,
        transaction_type=TransactionType.TRANSFER_IN,
        amount=amount,
        balance_after=to_balance,
        description=f"{description} ← Account {from_account.account_number}",
        related_account_id=from_account_id,
    )
    db.add(txn_out)
    db.add(txn_in)

    # Audit trail
    _log_audit(db, user_id, "TRANSFER", "transaction", {
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        "amount": amount,
        "from_balance_after": from_balance,
        "to_balance_after": to_balance,
    }, ip_address)

    db.commit()
    db.refresh(txn_out)
    db.refresh(txn_in)
    return txn_out, txn_in


# ---------------------------------------------------------------------------
# Transaction history
# ---------------------------------------------------------------------------
def get_transaction_history(
    db: Session, user_id: int, account_id: int, limit: int = 50
) -> list[Transaction]:
    """Retrieve transaction history for an account (most recent first)."""
    # Verify ownership
    _get_active_account(db, account_id, user_id)

    return (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )
