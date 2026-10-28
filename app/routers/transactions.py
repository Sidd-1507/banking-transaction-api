"""Transaction endpoints — deposit, withdraw, transfer, and history."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import AuditLog, User
from app.schemas import (
    AuditLogResponse,
    DepositRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawRequest,
)
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/deposit", response_model=TransactionResponse, status_code=201)
def deposit(
    payload: DepositRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deposit funds into an account."""
    return transaction_service.deposit(
        db=db,
        user_id=current_user.id,
        account_id=payload.account_id,
        amount=payload.amount,
        description=payload.description or "Cash deposit",
        ip_address=request.client.host if request.client else "unknown",
    )


@router.post("/withdraw", response_model=TransactionResponse, status_code=201)
def withdraw(
    payload: WithdrawRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Withdraw funds from an account. Fails if insufficient balance."""
    return transaction_service.withdraw(
        db=db,
        user_id=current_user.id,
        account_id=payload.account_id,
        amount=payload.amount,
        description=payload.description or "Cash withdrawal",
        ip_address=request.client.host if request.client else "unknown",
    )


@router.post("/transfer", response_model=list[TransactionResponse], status_code=201)
def transfer(
    payload: TransferRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transfer funds between two accounts owned by the authenticated user."""
    txn_out, txn_in = transaction_service.transfer(
        db=db,
        user_id=current_user.id,
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payload.amount,
        description=payload.description or "Fund transfer",
        ip_address=request.client.host if request.client else "unknown",
    )
    return [txn_out, txn_in]


@router.get("/history/{account_id}", response_model=list[TransactionResponse])
def transaction_history(
    account_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get transaction history for a specific account (most recent first)."""
    return transaction_service.get_transaction_history(
        db=db, user_id=current_user.id, account_id=account_id, limit=limit
    )


# ---------------------------------------------------------------------------
# Audit log endpoint
# ---------------------------------------------------------------------------
audit_router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@audit_router.get("/logs", response_model=list[AuditLogResponse])
def get_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View the audit trail for the authenticated user's actions."""
    return (
        db.query(AuditLog)
        .filter(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
