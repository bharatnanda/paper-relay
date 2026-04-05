from pydantic import BaseModel, Field
from typing import List, Literal, Optional
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


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


class ReformatRequest(BaseModel):
    reading_level: Literal["general", "technical", "eli5"]


class ReformatResponse(BaseModel):
    reformatted_fields: dict[str, str]
