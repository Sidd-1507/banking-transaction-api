"""FastAPI application entry point."""

from fastapi import FastAPI

from app.database import Base, engine
from app.routers.accounts import router as accounts_router
from app.routers.auth import router as auth_router
from app.routers.transactions import audit_router, router as transactions_router

# Create all database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="Banking Transaction API",
    description=(
        "A production-grade REST API for banking operations — account management, "
        "deposits, withdrawals, fund transfers, transaction history, and audit-trail "
        "logging. Built with FastAPI, SQLAlchemy, and JWT authentication."
    ),
    version="1.0.0",
    contact={"name": "Siddharth Sharma", "url": "https://github.com/Sidd-1507"},
)

# Register routers
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(audit_router)


@app.get("/", tags=["Health"])
def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "service": "Banking Transaction API",
        "version": "1.0.0",
    }
