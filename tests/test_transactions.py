"""Tests for transaction endpoints — deposit, withdraw, transfer, history."""


class TestDeposit:
    """Tests for POST /transactions/deposit."""

    def test_deposit_success(self, client, auth_headers, savings_account):
        """Depositing funds increases the account balance."""
        response = client.post(
            "/transactions/deposit",
            json={"account_id": savings_account["id"], "amount": 1000.0},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "DEPOSIT"
        assert data["amount"] == 1000.0
        assert data["balance_after"] == 1000.0

    def test_deposit_negative_amount(self, client, auth_headers, savings_account):
        """Depositing a negative amount returns 422 (Pydantic validation)."""
        response = client.post(
            "/transactions/deposit",
            json={"account_id": savings_account["id"], "amount": -100},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_deposit_zero_amount(self, client, auth_headers, savings_account):
        """Depositing zero returns 422."""
        response = client.post(
            "/transactions/deposit",
            json={"account_id": savings_account["id"], "amount": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_deposit_nonexistent_account(self, client, auth_headers):
        """Depositing to a non-existent account returns 404."""
        response = client.post(
            "/transactions/deposit",
            json={"account_id": 99999, "amount": 100},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestWithdraw:
    """Tests for POST /transactions/withdraw."""

    def test_withdraw_success(self, client, auth_headers, savings_account):
        """Withdrawing within balance succeeds."""
        # First deposit
        client.post(
            "/transactions/deposit",
            json={"account_id": savings_account["id"], "amount": 500.0},
            headers=auth_headers,
        )
        # Then withdraw
        response = client.post(
            "/transactions/withdraw",
            json={"account_id": savings_account["id"], "amount": 200.0},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "WITHDRAWAL"
        assert data["amount"] == 200.0
        assert data["balance_after"] == 300.0

    def test_withdraw_insufficient_balance(self, client, auth_headers, savings_account):
        """Withdrawing more than balance returns 400."""
        response = client.post(
            "/transactions/withdraw",
            json={"account_id": savings_account["id"], "amount": 1000.0},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Insufficient balance" in response.json()["detail"]

    def test_withdraw_from_empty_account(self, client, auth_headers, savings_account):
        """Withdrawing from an empty account returns 400."""
        response = client.post(
            "/transactions/withdraw",
            json={"account_id": savings_account["id"], "amount": 1.0},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_withdraw_negative_amount(self, client, auth_headers, savings_account):
        """Withdrawing a negative amount returns 422."""
        response = client.post(
            "/transactions/withdraw",
            json={"account_id": savings_account["id"], "amount": -50},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestTransfer:
    """Tests for POST /transactions/transfer."""

    def test_transfer_success(self, client, auth_headers):
        """Transferring between two accounts works correctly."""
        # Create two accounts
        acc1 = client.post(
            "/accounts/", json={"account_type": "SAVINGS"}, headers=auth_headers
        ).json()
        acc2 = client.post(
            "/accounts/", json={"account_type": "CHECKING"}, headers=auth_headers
        ).json()

        # Deposit into first account
        client.post(
            "/transactions/deposit",
            json={"account_id": acc1["id"], "amount": 1000.0},
            headers=auth_headers,
        )

        # Transfer
        response = client.post(
            "/transactions/transfer",
            json={
                "from_account_id": acc1["id"],
                "to_account_id": acc2["id"],
                "amount": 400.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        txns = response.json()
        assert len(txns) == 2
        assert txns[0]["transaction_type"] == "TRANSFER_OUT"
        assert txns[0]["balance_after"] == 600.0
        assert txns[1]["transaction_type"] == "TRANSFER_IN"
        assert txns[1]["balance_after"] == 400.0

    def test_transfer_insufficient_balance(self, client, auth_headers):
        """Transferring more than available returns 400."""
        acc1 = client.post(
            "/accounts/", json={"account_type": "SAVINGS"}, headers=auth_headers
        ).json()
        acc2 = client.post(
            "/accounts/", json={"account_type": "SAVINGS"}, headers=auth_headers
        ).json()

        response = client.post(
            "/transactions/transfer",
            json={
                "from_account_id": acc1["id"],
                "to_account_id": acc2["id"],
                "amount": 500.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_transfer_same_account(self, client, auth_headers, savings_account):
        """Transferring to the same account returns 422."""
        response = client.post(
            "/transactions/transfer",
            json={
                "from_account_id": savings_account["id"],
                "to_account_id": savings_account["id"],
                "amount": 100.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestTransactionHistory:
    """Tests for GET /transactions/history/{account_id}."""

    def test_transaction_history(self, client, auth_headers, savings_account):
        """Transaction history returns all transactions for an account."""
        account_id = savings_account["id"]

        # Perform some transactions
        client.post(
            "/transactions/deposit",
            json={"account_id": account_id, "amount": 500},
            headers=auth_headers,
        )
        client.post(
            "/transactions/withdraw",
            json={"account_id": account_id, "amount": 100},
            headers=auth_headers,
        )

        response = client.get(
            f"/transactions/history/{account_id}", headers=auth_headers
        )
        assert response.status_code == 200
        history = response.json()
        assert len(history) == 2
        # Most recent first
        assert history[0]["transaction_type"] == "WITHDRAWAL"
        assert history[1]["transaction_type"] == "DEPOSIT"

    def test_history_empty_account(self, client, auth_headers, savings_account):
        """History for an account with no transactions returns empty list."""
        response = client.get(
            f"/transactions/history/{savings_account['id']}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []


class TestAuditLogs:
    """Tests for GET /audit/logs."""

    def test_audit_trail_records_actions(self, client, auth_headers, savings_account):
        """Every significant action creates an audit log entry."""
        # Deposit (creates audit entry)
        client.post(
            "/transactions/deposit",
            json={"account_id": savings_account["id"], "amount": 100},
            headers=auth_headers,
        )

        response = client.get("/audit/logs", headers=auth_headers)
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) >= 2  # ACCOUNT_CREATED + DEPOSIT
        actions = [log["action"] for log in logs]
        assert "DEPOSIT" in actions
        assert "ACCOUNT_CREATED" in actions
