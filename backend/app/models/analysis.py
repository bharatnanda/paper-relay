from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.models.database import Base
import uuid

class PaperAnalysis(Base):
    __tablename__ = "paper_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False)
    summary_json = Column(JSONB, nullable=True)
    knowledge_graph_json = Column(JSONB, nullable=True)
    processing_status = Column(String(50), default="pending")
    progress_step = Column(String(100), nullable=True)  # Current step name
    progress_percent = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)  # Store specific errors
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<PaperAnalysis(id={self.id}, paper_id={self.paper_id}, status={self.processing_status})>"
