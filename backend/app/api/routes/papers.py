from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.models.user import User
from app.models.paper import Paper
from app.models.analysis import PaperAnalysis
from app.api.dependencies import get_current_user
from app.services.ingestion import IngestionService, MetadataFetchError
from app.schemas.paper import PaperAnalysisRequest, PaperAnalysisResponse, PaperAnalysisComplete
from app.workers.tasks import process_paper_task

router = APIRouter()

QUEUE_SUBMISSION_FAILED_DETAIL = "Failed to submit paper for background processing"


def submit_analysis_task(db: Session, analysis: PaperAnalysis, paper_id: str, arxiv_id: str) -> None:
    analysis.processing_status = "pending"
    analysis.progress_step = "Submitting job..."
    analysis.progress_percent = 0
    analysis.error_message = None
    db.commit()

    try:
        process_paper_task.delay(str(paper_id), arxiv_id)
    except Exception as exc:
        analysis.processing_status = "failed"
        analysis.progress_step = "Submission failed"
        analysis.progress_percent = 100
        analysis.error_message = QUEUE_SUBMISSION_FAILED_DETAIL
        db.commit()
        raise HTTPException(status_code=503, detail=QUEUE_SUBMISSION_FAILED_DETAIL) from exc

    analysis.processing_status = "processing"
    analysis.progress_step = "Queued for processing..."
    analysis.progress_percent = 1
    analysis.error_message = None
    db.commit()


@router.post("/analyze", response_model=PaperAnalysisResponse)
async def analyze_paper(request: PaperAnalysisRequest, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    ingestion = IngestionService()
    arxiv_id = ingestion.extract_arxiv_id(request.arxiv_url)

    if arxiv_id is None:
        raise HTTPException(status_code=400, detail="Invalid arXiv URL")

    existing = db.query(Paper).filter(Paper.user_id == current_user.id, Paper.arxiv_id == arxiv_id).first()
    if existing:
        analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == existing.id).first()
        if analysis is None:
            analysis = PaperAnalysis(paper_id=existing.id)
            db.add(analysis)
            db.commit()

        if analysis.processing_status != "complete":
            submit_analysis_task(db, analysis, str(existing.id), arxiv_id)
            return PaperAnalysisResponse(
                paper_id=str(existing.id),
                status="processing",
                message="Existing analysis re-queued",
            )

        return PaperAnalysisResponse(paper_id=str(existing.id), status="already_exists")

    try:
        metadata = await ingestion.fetch_paper_metadata(arxiv_id)
    except MetadataFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if metadata is None:
        raise HTTPException(status_code=404, detail="Paper not found on arXiv")

    paper = Paper(user_id=current_user.id, arxiv_id=arxiv_id, title=metadata.title,
                  authors=metadata.authors, abstract=metadata.abstract, pdf_url=metadata.pdf_url)
    db.add(paper)
    db.commit()
    db.refresh(paper)

    analysis = PaperAnalysis(paper_id=paper.id)
    db.add(analysis)
    db.commit()

    submit_analysis_task(db, analysis, str(paper.id), arxiv_id)
    return PaperAnalysisResponse(paper_id=str(paper.id), status="processing")

@router.get("/{paper_id}", response_model=PaperAnalysisComplete)
async def get_paper_analysis(paper_id: str, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).first()
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
        summary=analysis.summary_json,
        knowledge_graph=analysis.knowledge_graph_json,
    )

@router.get("", response_model=List[dict])
async def list_papers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    papers = db.query(Paper).filter(Paper.user_id == current_user.id).order_by(Paper.created_at.desc()).all()
    return [{"id": str(p.id), "arxiv_id": p.arxiv_id, "title": p.title, "authors": p.authors, "created_at": p.created_at} for p in papers]

@router.delete("/{paper_id}")
async def delete_paper(paper_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    db.delete(paper)
    db.commit()
    return {"message": "Paper deleted"}
