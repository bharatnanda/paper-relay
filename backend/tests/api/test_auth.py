import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.core.security import create_magic_link_token, create_session_token
from app.main import app

client = TestClient(app)


class TestAuthAPI:
    @patch('app.services.email.email_service.send_magic_link', new_callable=AsyncMock)
    async def test_request_magic_link_sends_email(self, mock_send):
        mock_send.return_value = True
        response = client.post("/api/auth/request-link", json={"email": "test@example.com"})
        assert response.status_code == 200
        assert "Check your email" in response.json()["message"]
        assert "token" not in response.json()
        mock_send.assert_called_once()

    def test_request_magic_link_invalid_email(self):
        response = client.post("/api/auth/request-link", json={"email": "not-an-email"})
        assert response.status_code == 422

    def test_verify_magic_link_returns_session_token(self):
        token, _ = create_magic_link_token("verify@test.com")
        verify_resp = client.post("/api/auth/verify", json={"token": token})
        assert verify_resp.status_code == 200
        assert verify_resp.json()["email"] == "verify@test.com"
        assert "token" in verify_resp.json()

    @patch('app.services.email.email_service.send_magic_link', new_callable=AsyncMock)
    async def test_get_session_user(self, mock_send):
        mock_send.return_value = True
        client.post("/api/auth/request-link", json={"email": "session@test.com"})
        token = create_session_token("session@test.com")
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "session@test.com"
        assert "token" not in response.json()

    @patch('app.services.email.email_service.send_magic_link', new_callable=AsyncMock)
    async def test_request_magic_link_email_send_failure(self, mock_send):
        mock_send.return_value = False
        response = client.post("/api/auth/request-link", json={"email": "test@example.com"})
        assert response.status_code == 500
        assert "Failed to send email" in response.json()["detail"]


class TestRateLimiting:
    @patch('app.services.email.email_service.send_magic_link', new_callable=AsyncMock)
    async def test_rate_limit_magic_link(self, mock_send):
        mock_send.return_value = True
        for i in range(3):
            response = client.post("/api/auth/request-link", json={"email": f"ratelimit{i}@test.com"})
            assert response.status_code == 200

    def test_verify_rejects_invalid_token(self):
        response = client.post("/api/auth/verify", json={"token": "invalid_token"})
        assert response.status_code in {401, 429}
