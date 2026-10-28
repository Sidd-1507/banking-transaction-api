"""Tests for account management endpoints."""


class TestCreateAccount:
    """Tests for POST /accounts/."""

    def test_create_savings_account(self, client, auth_headers):
        """Creating a savings account returns 201 with zero balance."""
        response = client.post(
            "/accounts/",
            json={"account_type": "SAVINGS"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "SAVINGS"
        assert data["balance"] == 0.0
        assert data["is_active"] is True
        assert len(data["account_number"]) == 12

    def test_create_checking_account(self, client, auth_headers):
        """Creating a checking account works correctly."""
        response = client.post(
            "/accounts/",
            json={"account_type": "CHECKING"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["account_type"] == "CHECKING"

    def test_create_account_invalid_type(self, client, auth_headers):
        """Invalid account type returns 422."""
        response = client.post(
            "/accounts/",
            json={"account_type": "INVALID"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_account_unauthenticated(self, client):
        """Creating an account without auth returns 401."""
        response = client.post("/accounts/", json={"account_type": "SAVINGS"})
        assert response.status_code == 401


class TestListAccounts:
    """Tests for GET /accounts/."""

    def test_list_accounts(self, client, auth_headers, savings_account):
        """Listing accounts returns the user's accounts."""
        response = client.get("/accounts/", headers=auth_headers)
        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) >= 1
        assert accounts[0]["account_type"] == "SAVINGS"

    def test_list_accounts_unauthenticated(self, client):
        """Listing accounts without auth returns 401."""
        response = client.get("/accounts/")
        assert response.status_code == 401


class TestGetAccount:
    """Tests for GET /accounts/{account_id}."""

    def test_get_account_by_id(self, client, auth_headers, savings_account):
        """Fetching a specific account returns its details."""
        account_id = savings_account["id"]
        response = client.get(f"/accounts/{account_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == account_id

    def test_get_nonexistent_account(self, client, auth_headers):
        """Fetching a non-existent account returns 404."""
        response = client.get("/accounts/99999", headers=auth_headers)
        assert response.status_code == 404
