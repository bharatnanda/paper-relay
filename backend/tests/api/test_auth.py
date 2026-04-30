import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.dependencies import get_current_user
from app.core.security import create_magic_link_token, create_session_token
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


class TestAuthAPI:
    @patch('app.services.email.email_service.send_magic_link', new_callable=AsyncMock)
    def test_request_magic_link_sends_email(self, mock_send):
        mock_send.return_value = True
        with patch("app.api.routes.auth.AuthService") as mock_auth_service_class:
            mock_auth_service = MagicMock()
            mock_auth_service.request_magic_link.return_value = ("magic-token", "2099-01-01T00:00:00Z")
            mock_auth_service_class.return_value = mock_auth_service
            response = client.post("/api/auth/request-link", json={"email": "test@example.com"})

        assert response.status_code == 200
        assert "Check your email" in response.json()["message"]
        assert "token" not in response.json()
        mock_send.assert_called_once()
        mock_auth_service.request_magic_link.assert_called_once_with("test@example.com")

    def test_request_magic_link_invalid_email(self):
        response = client.post("/api/auth/request-link", json={"email": "not-an-email"})
        assert response.status_code == 422

    def test_verify_magic_link_returns_session_token(self):
        token, _ = create_magic_link_token("verify@test.com")
        mock_user = MagicMock()
        mock_user.id = "00000000-0000-0000-0000-000000000001"
        mock_user.email = "verify@test.com"
        with patch("app.api.routes.auth.AuthService") as mock_auth_service_class:
            mock_auth_service = MagicMock()
            mock_auth_service.verify_magic_link.return_value = mock_user
            mock_auth_service.get_user_papers.return_value = []
            mock_auth_service.create_session_token.return_value = "session-token"
            mock_auth_service_class.return_value = mock_auth_service
            verify_resp = client.post("/api/auth/verify", json={"token": token})

        assert verify_resp.status_code == 200
        assert verify_resp.json()["email"] == "verify@test.com"
        assert verify_resp.json()["token"] == "session-token"

    @patch('app.services.email.email_service.send_magic_link', new_callable=AsyncMock)
    def test_get_session_user(self, mock_send):
        mock_send.return_value = True
        token = create_session_token("session@test.com")
        mock_user = MagicMock()
        mock_user.id = "00000000-0000-0000-0000-000000000002"
        mock_user.email = "session@test.com"
        app.dependency_overrides[get_current_user] = lambda: mock_user
        with patch("app.api.routes.auth.AuthService") as mock_auth_service_class:
            mock_auth_service = MagicMock()
            mock_auth_service.get_user_papers.return_value = []
            mock_auth_service_class.return_value = mock_auth_service
            try:
                response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            finally:
                app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        assert response.json()["email"] == "session@test.com"
        assert "token" not in response.json()

    @patch('app.services.email.email_service.send_magic_link', new_callable=AsyncMock)
    def test_request_magic_link_email_send_failure(self, mock_send):
        mock_send.return_value = False
        with patch("app.api.routes.auth.AuthService") as mock_auth_service_class:
            mock_auth_service = MagicMock()
            mock_auth_service.request_magic_link.return_value = ("magic-token", "2099-01-01T00:00:00Z")
            mock_auth_service_class.return_value = mock_auth_service
            response = client.post("/api/auth/request-link", json={"email": "test@example.com"})

        assert response.status_code == 500
        assert "Failed to send email" in response.json()["detail"]


class TestRateLimiting:
    @patch('app.services.email.email_service.send_magic_link', new_callable=AsyncMock)
    def test_rate_limit_magic_link(self, mock_send):
        mock_send.return_value = True
        with patch("app.api.routes.auth.AuthService") as mock_auth_service_class:
            mock_auth_service = MagicMock()
            mock_auth_service.request_magic_link.return_value = ("magic-token", "2099-01-01T00:00:00Z")
            mock_auth_service_class.return_value = mock_auth_service

            for i in range(3):
                response = client.post("/api/auth/request-link", json={"email": f"ratelimit{i}@test.com"})
                assert response.status_code == 200

            response = client.post("/api/auth/request-link", json={"email": "ratelimit-over@test.com"})
            assert response.status_code == 429

    def test_verify_rejects_invalid_token(self):
        response = client.post("/api/auth/verify", json={"token": "invalid_token"})
        assert response.status_code in {401, 429}
