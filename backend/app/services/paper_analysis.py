from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.analysis import PaperAnalysis
from app.models.paper import Paper
from app.models.user import User
from app.schemas.paper import PaperAnalysisResponse
from app.services.ingestion import IngestionService, MetadataFetchError
from app.workers.tasks import process_paper_task


QUEUE_SUBMISSION_FAILED_DETAIL = "Failed to submit paper for background processing"


class PaperAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService()

    def submit_analysis_task(self, analysis: PaperAnalysis, paper_id: str, arxiv_id: str) -> None:
        analysis.processing_status = "pending"
        analysis.progress_step = "Submitting job..."
        analysis.progress_percent = 0
        analysis.error_message = None
        self.db.commit()

        try:
            process_paper_task.delay(str(paper_id), arxiv_id)
        except Exception as exc:
            analysis.processing_status = "failed"
            analysis.progress_step = "Submission failed"
            analysis.progress_percent = 100
            analysis.error_message = QUEUE_SUBMISSION_FAILED_DETAIL
            self.db.commit()
            raise HTTPException(status_code=503, detail=QUEUE_SUBMISSION_FAILED_DETAIL) from exc

        analysis.processing_status = "processing"
        analysis.progress_step = "Queued for processing..."
        analysis.progress_percent = 1
        analysis.error_message = None
        self.db.commit()

    async def analyze_paper(self, arxiv_url: str, current_user: User) -> PaperAnalysisResponse:
        arxiv_id = self.ingestion.extract_arxiv_id(arxiv_url)
        if arxiv_id is None:
            raise HTTPException(status_code=400, detail="Invalid arXiv URL")

        existing = self.db.query(Paper).filter(
            Paper.user_id == current_user.id,
            Paper.arxiv_id == arxiv_id,
        ).first()
        if existing:
            analysis = self.db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == existing.id).first()
            if analysis is None:
                analysis = PaperAnalysis(paper_id=existing.id)
                self.db.add(analysis)
                self.db.commit()

            if analysis.processing_status != "complete":
                self.submit_analysis_task(analysis, str(existing.id), arxiv_id)
                return PaperAnalysisResponse(
                    paper_id=str(existing.id),
                    status="processing",
                    message="Existing analysis re-queued",
                )

            return PaperAnalysisResponse(paper_id=str(existing.id), status="already_exists")

        try:
            metadata = await self.ingestion.fetch_paper_metadata(arxiv_id)
        except MetadataFetchError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        if metadata is None:
            raise HTTPException(status_code=404, detail="Paper not found on arXiv")

        paper = Paper(
            user_id=current_user.id,
            arxiv_id=arxiv_id,
            title=metadata.title,
            authors=metadata.authors,
            abstract=metadata.abstract,
            pdf_url=metadata.pdf_url,
        )
        self.db.add(paper)
        self.db.commit()
        self.db.refresh(paper)

        analysis = PaperAnalysis(paper_id=paper.id)
        self.db.add(analysis)
        self.db.commit()

        self.submit_analysis_task(analysis, str(paper.id), arxiv_id)
        return PaperAnalysisResponse(paper_id=str(paper.id), status="processing")

    def get_user_paper(self, paper_id: str, current_user: User) -> Paper:
        paper = self.db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
        if paper is None:
            raise HTTPException(status_code=404, detail="Paper not found")
        return paper

    def get_analysis(self, paper_id: str) -> PaperAnalysis | None:
        return self.db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).first()

    def get_completed_analysis_for_user(self, paper_id: str, current_user: User) -> tuple[Paper, PaperAnalysis]:
        paper = self.get_user_paper(paper_id, current_user)
        analysis = self.get_analysis(paper_id)
        if analysis is None or analysis.processing_status != "complete":
            raise HTTPException(status_code=400, detail="Paper analysis is not complete")
        return paper, analysis
