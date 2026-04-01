from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PaperMetadata(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: str
    published: Optional[datetime] = None
    categories: List[str] = []

class PaperAnalysisRequest(BaseModel):
    arxiv_url: str

class PaperAnalysisResponse(BaseModel):
    paper_id: str
    status: str = "pending"
    message: str = "Processing started"

class PaperAnalysisComplete(BaseModel):
    paper_id: str
    status: str = "complete"
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    progress_step: Optional[str] = None
    progress_percent: Optional[int] = None
    error_message: Optional[str] = None
    summary: Optional[dict] = None
    knowledge_graph: Optional[dict] = None
