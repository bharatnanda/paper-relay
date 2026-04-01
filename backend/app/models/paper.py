from sqlalchemy import Column, String, DateTime, ForeignKey, ARRAY, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base
import uuid

class Paper(Base):
    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    arxiv_id = Column(String(50), nullable=False)
    title = Column(String, nullable=True)
    authors = Column(ARRAY(String), nullable=True)
    abstract = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="papers")
    analyses = relationship("PaperAnalysis", backref="paper", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", back_populates="paper", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('user_id', 'arxiv_id', name='unique_user_paper'),
    )

    def __repr__(self):
        return f"<Paper(id={self.id}, arxiv_id={self.arxiv_id}, title={self.title})>"
