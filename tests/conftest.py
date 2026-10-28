"""Shared test fixtures and test database configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Use a single shared in-memory SQLite database for tests.
# StaticPool ensures the same connection is reused across threads,
# which is required for in-memory SQLite to share state.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override the database dependency for tests."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """Provide a test HTTP client."""
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    """Register a test user and return the user data."""
    payload = {
        "email": "test@example.com",
        "password": "securepass123",
        "full_name": "Test User",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    return payload


@pytest.fixture
def auth_headers(client, registered_user):
    """Login the test user and return authorization headers."""
    response = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def savings_account(client, auth_headers):
    """Create a savings account and return its data."""
    response = client.post(
        "/accounts/",
        json={"account_type": "SAVINGS"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()
