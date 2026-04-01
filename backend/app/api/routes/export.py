from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.models.paper import Paper
from app.models.analysis import PaperAnalysis
from app.api.dependencies import get_current_user
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/{paper_id}/export")
async def export_paper(
    paper_id: str,
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export paper analysis as PDF or Markdown."""
    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.user_id == current_user.id
    ).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    analysis = db.query(PaperAnalysis).filter(
        PaperAnalysis.paper_id == paper_id
    ).first()
    
    if not analysis or analysis.processing_status != "complete":
        raise HTTPException(status_code=400, detail="Analysis not ready")

    export_service = ExportService()

    if format.lower() == "pdf":
        pdf_bytes = export_service.generate_pdf(
            {
                "title": paper.title,
                "authors": paper.authors,
                "arxiv_id": paper.arxiv_id,
                "source_url": f"https://arxiv.org/abs/{paper.arxiv_id}" if paper.arxiv_id else None,
                "pdf_url": paper.pdf_url
            },
            {
                "summary": analysis.summary_json,
                "knowledge_graph": analysis.knowledge_graph_json
            }
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={paper.arxiv_id}.pdf"}
        )
    elif format.lower() == "md":
        md_content = export_service.generate_markdown(
            {
                "title": paper.title,
                "authors": paper.authors,
                "arxiv_id": paper.arxiv_id,
                "source_url": f"https://arxiv.org/abs/{paper.arxiv_id}" if paper.arxiv_id else None,
                "pdf_url": paper.pdf_url
            },
            {
                "summary": analysis.summary_json,
                "knowledge_graph": analysis.knowledge_graph_json
            }
        )
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={paper.arxiv_id}.md"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
