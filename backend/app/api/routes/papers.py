from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.models.paper import Paper
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.ai_processor import AIProcessor
from app.services.paper_analysis import PaperAnalysisService
from app.schemas.paper import (
    AnalysisSummary,
    PaperAnalysisRequest, PaperAnalysisResponse, PaperAnalysisComplete,
    ChatRequest, ChatResponse, ReformatRequest, ReformatResponse,
)
from app.core.limiter import limiter

router = APIRouter()


@router.post("/analyze", response_model=PaperAnalysisResponse)
async def analyze_paper(request: PaperAnalysisRequest, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    service = PaperAnalysisService(db)
    return await service.analyze_paper(request.arxiv_url, current_user)

@router.get("/{paper_id}", response_model=PaperAnalysisComplete)
async def get_paper_analysis(paper_id: str, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    service = PaperAnalysisService(db)
    paper = service.get_user_paper(paper_id, current_user)
    analysis = service.get_analysis(paper_id)
    if analysis is None:
        return PaperAnalysisComplete(paper_id=paper_id, status="pending")

    return PaperAnalysisComplete(
        paper_id=paper_id,
        status=analysis.processing_status,
        title=paper.title,
        authors=paper.authors,
        arxiv_id=paper.arxiv_id,
        pdf_url=paper.pdf_url,
        progress_step=analysis.progress_step,
        progress_percent=analysis.progress_percent,
        error_message=analysis.error_message,
        summary=AnalysisSummary.from_storage(analysis.summary_json),
        knowledge_graph=analysis.knowledge_graph_json,
    )

@router.get("", response_model=List[dict])
async def list_papers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    papers = db.query(Paper).filter(Paper.user_id == current_user.id).order_by(Paper.created_at.desc()).all()
    return [{"id": str(p.id), "arxiv_id": p.arxiv_id, "title": p.title, "authors": p.authors, "created_at": p.created_at} for p in papers]

@router.delete("/{paper_id}")
async def delete_paper(paper_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = PaperAnalysisService(db)
    paper = service.get_user_paper(paper_id, current_user)
    db.delete(paper)
    db.commit()
    return {"message": "Paper deleted"}


@router.post("/{paper_id}/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_with_paper(
    request: Request,
    paper_id: str,
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PaperAnalysisService(db)
    _, analysis = service.get_completed_analysis_for_user(paper_id, current_user)
    summary_json = AnalysisSummary.from_storage(analysis.summary_json).model_dump()
    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    processor = AIProcessor()
    reply = await processor.chat_with_paper(messages, summary_json)
    return ChatResponse(reply=reply)


@router.post("/{paper_id}/reformat", response_model=ReformatResponse)
@limiter.limit("10/minute")
async def reformat_paper(
    request: Request,
    paper_id: str,
    body: ReformatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PaperAnalysisService(db)
    _, analysis = service.get_completed_analysis_for_user(paper_id, current_user)
    summary_json = AnalysisSummary.from_storage(analysis.summary_json).model_dump()
    processor = AIProcessor()
    reformatted = await processor.reformat_for_audience(summary_json, body.reading_level)
    return ReformatResponse(reformatted_fields=reformatted)
