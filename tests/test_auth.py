"""Tests for authentication endpoints."""


class TestRegister:
    """Tests for POST /auth/register."""

    def test_register_success(self, client):
        """New user registration returns 201 with user data."""
        response = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data

    def test_register_duplicate_email(self, client, registered_user):
        """Registering with an existing email returns 409 Conflict."""
        response = client.post("/auth/register", json={
            "email": registered_user["email"],
            "password": "anotherpass123",
            "full_name": "Duplicate User",
        })
        assert response.status_code == 409

    def test_register_short_password(self, client):
        """Password shorter than 8 characters returns 422."""
        response = client.post("/auth/register", json={
            "email": "short@example.com",
            "password": "short",
            "full_name": "Short Pass",
        })
        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        """Invalid email format returns 422."""
        response = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Invalid Email",
        })
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /auth/login."""

    def test_login_success(self, client, registered_user):
        """Valid credentials return a JWT token."""
        response = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        """Wrong password returns 401 Unauthorized."""
        response = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Non-existent email returns 401 Unauthorized."""
        response = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "password123",
        })
        assert response.status_code == 401
