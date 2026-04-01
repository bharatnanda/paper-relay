import re
import xml.etree.ElementTree as ET
from typing import Optional

import httpx

from app.schemas.paper import PaperMetadata


class MetadataFetchError(Exception):
    pass


class IngestionService:
    ARXIV_API_BASE = "https://export.arxiv.org/api/query"

    def __init__(self):
        self.timeout = httpx.Timeout(30.0)

    async def fetch_paper_metadata(self, arxiv_id: str) -> Optional[PaperMetadata]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            url = f"{self.ARXIV_API_BASE}?id_list={arxiv_id}&max_results=1"
            try:
                response = await client.get(url)
                response.raise_for_status()
                return self._parse_arxiv_response(response.text, arxiv_id)
            except httpx.HTTPError as exc:
                raise MetadataFetchError("Failed to fetch paper metadata from arXiv") from exc
            except ET.ParseError as exc:
                raise MetadataFetchError("Received an invalid metadata response from arXiv") from exc

    async def download_pdf(self, pdf_url: str) -> Optional[bytes]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(pdf_url)
                response.raise_for_status()
                return response.content
            except httpx.HTTPError:
                return None

    def _parse_arxiv_response(self, xml_content: str, arxiv_id: str) -> Optional[PaperMetadata]:
        root = ET.fromstring(xml_content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        entry = root.find('atom:entry', ns)
        if entry is None:
            return None

        title = entry.find('atom:title', ns)
        abstract = entry.find('atom:summary', ns)
        published = entry.find('atom:published', ns)
        pdf_link = entry.find("atom:link[@title='pdf']", ns)

        authors = [name.text for author in entry.findall('atom:author', ns)
                  if (name := author.find('atom:name', ns)) is not None]

        categories = [cat.get('term') for cat in entry.findall('atom:category', ns) if cat.get('term')]
        pdf_url = pdf_link.get('href') if pdf_link is not None and pdf_link.get('href') else f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        return PaperMetadata(
            arxiv_id=arxiv_id,
            title=title.text.strip() if title is not None else "",
            authors=authors,
            abstract=abstract.text.strip() if abstract is not None else "",
            pdf_url=pdf_url,
            published=published.text if published is not None else None,
            categories=categories
        )

    def extract_arxiv_id(self, url: str) -> Optional[str]:
        patterns = [r'arxiv\.org/abs/(\d{4}\.\d{4,5})', r'arxiv\.org/pdf/(\d{4}\.\d{4,5})']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
