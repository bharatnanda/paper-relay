import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock
from app.services.ingestion import IngestionService, MetadataFetchError

class TestIngestionService:

    @pytest.fixture
    def service(self):
        return IngestionService()

    def test_extract_arxiv_id_valid_url(self, service):
        assert service.extract_arxiv_id("https://arxiv.org/abs/2301.12345") == "2301.12345"

    def test_extract_arxiv_id_pdf_url(self, service):
        assert service.extract_arxiv_id("https://arxiv.org/pdf/2301.12345.pdf") == "2301.12345"

    def test_extract_arxiv_id_invalid_url(self, service):
        assert service.extract_arxiv_id("https://example.com/paper") is None

    def test_fetch_paper_metadata_uses_id_list_query(self, service, monkeypatch):
        response = httpx.Response(
            200,
            request=httpx.Request("GET", "https://export.arxiv.org/api/query?id_list=2301.12345&max_results=1"),
            text=(
                '<feed xmlns="http://www.w3.org/2005/Atom">'
                '<entry>'
                '<title>Test Paper</title>'
                '<summary>Test abstract</summary>'
                '<published>2024-01-01T00:00:00Z</published>'
                '<author><name>Test Author</name></author>'
                '<category term="cs.AI" />'
                '</entry>'
                '</feed>'
            ),
        )
        get_mock = AsyncMock(return_value=response)
        monkeypatch.setattr(httpx.AsyncClient, "get", get_mock)

        result = asyncio.run(service.fetch_paper_metadata("2301.12345"))

        assert result is not None
        get_mock.assert_awaited_once_with(
            "https://export.arxiv.org/api/query?id_list=2301.12345&max_results=1"
        )

    def test_fetch_paper_metadata_raises_on_invalid_xml(self, service, monkeypatch):
        response = httpx.Response(
            200,
            request=httpx.Request("GET", "https://export.arxiv.org/api/query?id_list=2301.12345&max_results=1"),
            text="not xml",
        )
        get_mock = AsyncMock(return_value=response)
        monkeypatch.setattr(httpx.AsyncClient, "get", get_mock)

        with pytest.raises(MetadataFetchError, match="metadata response"):
            asyncio.run(service.fetch_paper_metadata("2301.12345"))
