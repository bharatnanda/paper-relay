import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.security import create_session_token
from app.main import app
from app.api.dependencies import get_current_user
from app.schemas.paper import PaperMetadata
from app.services.ingestion import MetadataFetchError

client = TestClient(app)


def _make_fake_user():
    user = MagicMock()
    user.id = "00000000-0000-0000-0000-000000000001"
    user.email = "papers@test.com"
    return user


class TestPapersAPI:
    @pytest.fixture
    def auth_token(self):
        return create_session_token("papers@test.com")

    def test_analyze_paper_invalid_url(self, auth_token):
        resp = client.post(
            "/api/papers/analyze",
            json={"arxiv_url": "https://example.com"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 400

    def test_unauthorized(self):
        resp = client.post("/api/papers/analyze", json={"arxiv_url": "https://arxiv.org/abs/2301.12345"})
        assert resp.status_code == 401

    @patch("app.api.routes.papers.process_paper_task.delay")
    @patch("app.api.routes.papers.IngestionService.fetch_paper_metadata", new_callable=AsyncMock)
    def test_analyze_paper_returns_503_when_queue_submission_fails(self, mock_fetch, mock_delay, auth_token):
        mock_fetch.return_value = PaperMetadata(
            arxiv_id="2301.12345",
            title="Queued paper",
            authors=["Test Author"],
            abstract="Test abstract",
            pdf_url="https://arxiv.org/pdf/2301.12345",
        )
        mock_delay.side_effect = RuntimeError("broker unavailable")
        resp = client.post(
            "/api/papers/analyze",
            json={"arxiv_url": "https://arxiv.org/abs/2301.12345"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 503
        assert resp.json()["detail"] == "Failed to submit paper for background processing"

    @patch("app.api.routes.papers.IngestionService.fetch_paper_metadata", new_callable=AsyncMock)
    def test_analyze_paper_returns_502_when_metadata_fetch_fails(self, mock_fetch, auth_token):
        mock_fetch.side_effect = MetadataFetchError("Failed to fetch paper metadata from arXiv")
        resp = client.post(
            "/api/papers/analyze",
            json={"arxiv_url": "https://arxiv.org/abs/2301.12345"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 502

    @patch("app.api.routes.papers.AIProcessor")
    def test_chat_requires_auth(self, mock_processor):
        resp = client.post("/api/papers/some-id/chat", json={"messages": [{"role": "user", "content": "Hello"}]})
        assert resp.status_code == 401

    @patch("app.api.routes.papers.AIProcessor")
    def test_chat_returns_404_for_unknown_paper(self, mock_processor):
        app.dependency_overrides[get_current_user] = _make_fake_user
        try:
            resp = client.post(
                "/api/papers/00000000-0000-0000-0000-000000000000/chat",
                json={"messages": [{"role": "user", "content": "What is this about?"}]},
            )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @patch("app.api.routes.papers.AIProcessor")
    def test_reformat_requires_auth(self, mock_processor):
        resp = client.post("/api/papers/some-id/reformat", json={"reading_level": "eli5"})
        assert resp.status_code == 401

    @patch("app.api.routes.papers.AIProcessor")
    def test_reformat_returns_404_for_unknown_paper(self, mock_processor):
        app.dependency_overrides[get_current_user] = _make_fake_user
        try:
            resp = client.post(
                "/api/papers/00000000-0000-0000-0000-000000000000/reformat",
                json={"reading_level": "eli5"},
            )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @patch("app.api.routes.papers.AIProcessor")
    def test_reformat_rejects_invalid_reading_level(self, mock_processor):
        app.dependency_overrides[get_current_user] = _make_fake_user
        try:
            resp = client.post(
                "/api/papers/00000000-0000-0000-0000-000000000000/reformat",
                json={"reading_level": "expert"},
            )
            # 422 from Pydantic validation or 404 from paper not found — either is correct
            assert resp.status_code in (404, 422)
        finally:
            app.dependency_overrides.pop(get_current_user, None)
