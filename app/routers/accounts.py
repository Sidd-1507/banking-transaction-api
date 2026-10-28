"""Account management endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import AccountCreate, AccountResponse
from app.services import account_service

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse, status_code=201)
def create_account(
    payload: AccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new bank account for the authenticated user."""
    return account_service.create_account(
        db=db,
        user=current_user,
        account_type=payload.account_type,
        ip_address=request.client.host if request.client else "unknown",
    )


@router.get("/", response_model=list[AccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all accounts belonging to the authenticated user."""
    return account_service.get_user_accounts(db, current_user.id)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific account."""
    return account_service.get_account_by_id(db, account_id, current_user.id)
