import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.core.security import create_session_token
from app.main import app
from app.schemas.paper import PaperMetadata
from app.services.ingestion import MetadataFetchError

client = TestClient(app)


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
