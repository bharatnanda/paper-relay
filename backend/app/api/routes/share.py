from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets
from datetime import datetime, timedelta
from app.models.database import get_db
from app.models.user import User
from app.models.paper import Paper
from app.models.analysis import PaperAnalysis
from app.models.share import ShareLink
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("/papers/{paper_id}/share")
async def create_share_link(paper_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    existing = db.query(ShareLink).filter(ShareLink.paper_id == paper_id, ShareLink.is_active == True).first()
    if existing:
        return {"share_url": f"/share/{existing.share_token}"}

    share_token = secrets.token_urlsafe(32)
    share_link = ShareLink(
        paper_id=paper_id, 
        share_token=share_token,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(share_link)
    db.commit()

    return {"share_url": f"/share/{share_token}"}

@router.get("/share/{share_token}")
async def get_shared_paper(share_token: str, db: Session = Depends(get_db)):
    share_link = db.query(ShareLink).filter(ShareLink.share_token == share_token, ShareLink.is_active == True).first()
    if not share_link:
        raise HTTPException(status_code=404, detail="Share link not found or expired")
    
    # Check expiration
    if share_link.is_expired():
        share_link.is_active = False
        db.commit()
        raise HTTPException(status_code=404, detail="Share link has expired")

    paper = db.query(Paper).filter(Paper.id == share_link.paper_id).first()
    analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == share_link.paper_id).first()

    if not paper or not analysis:
        raise HTTPException(status_code=404, detail="Paper not found")

    return {"paper": {"id": str(paper.id), "arxiv_id": paper.arxiv_id, "title": paper.title, "authors": paper.authors, "pdf_url": paper.pdf_url}, "analysis": {"status": analysis.processing_status, "summary": analysis.summary_json, "knowledge_graph": analysis.knowledge_graph_json}}

@router.delete("/papers/{paper_id}/share")
async def revoke_share_link(paper_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    db.query(ShareLink).filter(ShareLink.paper_id == paper_id).update({"is_active": False})
    db.commit()
    return {"message": "Share link revoked"}
