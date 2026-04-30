from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.core.security import create_session_token
from app.main import app
from app.models.database import get_db

client = TestClient(app)


def _make_fake_user():
    user = MagicMock()
    user.id = "00000000-0000-0000-0000-000000000001"
    user.email = "papers@test.com"
    return user


def _make_fake_db(paper, analysis):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [paper, analysis]
    return mock_db


class TestExportAPI:
    def test_export_markdown_normalizes_legacy_summary_shape(self):
        auth_token = create_session_token("papers@test.com")

        mock_paper = MagicMock()
        mock_paper.id = "00000000-0000-0000-0000-000000000001"
        mock_paper.title = "Legacy Export Paper"
        mock_paper.authors = ["Author 1"]
        mock_paper.arxiv_id = "2301.12345"
        mock_paper.pdf_url = "https://arxiv.org/pdf/2301.12345.pdf"

        mock_analysis = MagicMock()
        mock_analysis.processing_status = "complete"
        mock_analysis.summary_json = {
            "quick_summary": "Legacy quick summary",
            "eli5_explanation": "Legacy eli5 summary",
            "technical_summary": "Legacy technical summary",
        }
        mock_analysis.knowledge_graph_json = {"nodes": [], "edges": []}

        mock_db = _make_fake_db(mock_paper, mock_analysis)

        app.dependency_overrides[get_current_user] = _make_fake_user
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get(
                "/api/papers/00000000-0000-0000-0000-000000000001/export?format=md",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/markdown")
        assert "Legacy quick summary" in resp.text
        assert "Legacy eli5 summary" in resp.text
