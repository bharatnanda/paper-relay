import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.api.dependencies import get_current_user
from app.core.security import create_session_token
from app.main import app
from app.models.database import get_db

client = TestClient(app)


def _make_fake_db(share_link, paper, analysis):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [share_link, paper, analysis]
    return mock_db


class TestShareAPI:
    @pytest.fixture
    def auth_token(self):
        return create_session_token("share@test.com")

    def test_share_requires_auth(self):
        response = client.post("/api/papers/test/share")
        assert response.status_code == 401

    def test_invalid_share_link_returns_404(self):
        mock_db = _make_fake_db(None, None, None)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            response = client.get("/api/share/not-a-real-token")
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 404

    def test_shared_paper_normalizes_legacy_summary_shape(self):
        share_link = MagicMock()
        share_link.paper_id = "00000000-0000-0000-0000-000000000001"
        share_link.is_expired.return_value = False

        paper = MagicMock()
        paper.id = "00000000-0000-0000-0000-000000000001"
        paper.arxiv_id = "2301.12345"
        paper.title = "Shared Paper"
        paper.authors = ["Author 1"]
        paper.pdf_url = "https://arxiv.org/pdf/2301.12345.pdf"

        analysis = MagicMock()
        analysis.processing_status = "complete"
        analysis.summary_json = {
            "quick_summary": "Legacy quick summary",
            "eli5_explanation": "Legacy eli5 summary",
            "technical_summary": "Legacy technical summary",
        }
        analysis.knowledge_graph_json = {"nodes": [], "edges": []}

        mock_db = _make_fake_db(share_link, paper, analysis)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            response = client.get("/api/share/test-token")
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["analysis"]["summary"]["quick"] == "Legacy quick summary"
        assert payload["analysis"]["summary"]["eli5"] == "Legacy eli5 summary"
        assert payload["analysis"]["summary"]["technical"] == "Legacy technical summary"
