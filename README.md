# Banking Transaction REST API

A production-grade **Banking Transaction REST API** built with **Python, FastAPI, SQLAlchemy, and SQLite/PostgreSQL** — featuring account management, fund transfers, transaction history, JWT authentication, audit-trail logging, and comprehensive test coverage.

## Features

- **Account Management** — Create, view, and manage bank accounts
- **Fund Operations** — Deposit, withdraw, and transfer funds with validation
- **Transaction History** — Full audit trail with timestamps, types, and descriptions
- **JWT Authentication** — Secure endpoints with token-based auth
- **Input Validation** — Pydantic schemas enforce data integrity (can't overdraw, negative amounts blocked)
- **Audit Logging** — Every operation logged with timestamp, actor, and details
- **Error Handling** — Proper HTTP status codes (400, 401, 403, 404, 409, 422)
- **Unit Tests** — pytest test suite covering all business logic and edge cases
- **API Documentation** — Auto-generated Swagger UI at `/docs`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (PyJWT + bcrypt) |
| Validation | Pydantic v2 |
| Testing | pytest + httpx |
| Docs | Swagger UI (auto-generated) |

## Project Structure

```
banking-transaction-api/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration & environment settings
│   ├── database.py          # Database connection & session management
│   ├── models.py            # SQLAlchemy ORM models (User, Account, Transaction, AuditLog)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # JWT token creation & verification
│   ├── routers/
│   │   ├── auth.py          # POST /auth/register, POST /auth/login
│   │   ├── accounts.py      # CRUD for bank accounts
│   │   └── transactions.py  # Deposit, withdraw, transfer, history
│   └── services/
│       ├── account_service.py     # Account business logic
│       └── transaction_service.py # Transaction business logic + audit
├── tests/
│   ├── conftest.py          # Test fixtures & test database setup
│   ├── test_auth.py         # Authentication tests
│   ├── test_accounts.py     # Account endpoint tests
│   └── test_transactions.py # Transaction endpoint tests
├── requirements.txt
├── .gitignore
└── README.md
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Login, get JWT token | No |
| POST | `/accounts` | Create a new bank account | Yes |
| GET | `/accounts` | List user's accounts | Yes |
| GET | `/accounts/{id}` | Get account details | Yes |
| POST | `/transactions/deposit` | Deposit funds | Yes |
| POST | `/transactions/withdraw` | Withdraw funds | Yes |
| POST | `/transactions/transfer` | Transfer between accounts | Yes |
| GET | `/transactions/history/{account_id}` | Transaction history | Yes |
| GET | `/audit/logs` | View audit trail | Yes |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Sidd-1507/banking-transaction-api.git
cd banking-transaction-api

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload

# Open API docs
# http://localhost:8000/docs
```

## Run Tests

```bash
pytest tests/ -v --tb=short
```

## Database Schema

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    users      │     │    accounts       │     │  transactions    │
├──────────────┤     ├──────────────────┤     ├──────────────────┤
│ id (PK)      │──┐  │ id (PK)          │──┐  │ id (PK)          │
│ email        │  └──│ user_id (FK)     │  └──│ account_id (FK)  │
│ hashed_pass  │     │ account_number   │     │ type (enum)      │
│ full_name    │     │ account_type     │     │ amount           │
│ created_at   │     │ balance          │     │ balance_after    │
└──────────────┘     │ is_active        │     │ description      │
                     │ created_at       │     │ related_account  │
                     └──────────────────┘     │ created_at       │
                                              └──────────────────┘
┌──────────────────┐
│   audit_logs     │
├──────────────────┤
│ id (PK)          │
│ user_id (FK)     │
│ action           │
│ resource         │
│ details (JSON)   │
│ ip_address       │
│ timestamp        │
└──────────────────┘
```

## Author

**Siddharth Sharma** — [GitHub](https://github.com/Sidd-1507) | [LinkedIn](https://linkedin.com/in/siddharth-sharma-555486306)
