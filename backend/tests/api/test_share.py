import pytest
from fastapi.testclient import TestClient

from app.core.security import create_session_token
from app.main import app

client = TestClient(app)


class TestShareAPI:
    @pytest.fixture
    def auth_token(self):
        return create_session_token("share@test.com")

    def test_share_requires_auth(self):
        response = client.post("/api/papers/test/share")
        assert response.status_code == 401

    def test_invalid_share_link_returns_404(self):
        response = client.get("/api/share/not-a-real-token")
        assert response.status_code == 404
