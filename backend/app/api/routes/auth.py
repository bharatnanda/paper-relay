from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.services.email import email_service
from app.schemas.auth import MagicLinkRequest, MagicLinkResponse, AuthVerifyRequest, AuthVerifyResponse, AuthSessionResponse
from app.core.limiter import limiter

router = APIRouter()

@router.post("/request-link", response_model=MagicLinkResponse)
@limiter.limit("3/hour")
async def request_magic_link(request: Request, data: MagicLinkRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    token, expires_at = auth_service.request_magic_link(data.email)

    # Send via email (NOT in API response)
    sent = await email_service.send_magic_link(data.email, token)
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return MagicLinkResponse(
        message="Check your email for the magic link",
        status="link_sent"
    )

@router.post("/verify", response_model=AuthVerifyResponse)
@limiter.limit("5/minute")
async def verify_magic_link(request: Request, data: AuthVerifyRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.verify_magic_link(data.token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    papers = auth_service.get_user_papers(user)
    session_token = auth_service.create_session_token(user)
    return AuthVerifyResponse(
        user_id=str(user.id),
        email=user.email,
        token=session_token,
        papers_count=len(papers),
    )


@router.get("/me", response_model=AuthSessionResponse)
async def get_session_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    papers = auth_service.get_user_papers(current_user)
    return AuthSessionResponse(
        user_id=str(current_user.id),
        email=current_user.email,
        papers_count=len(papers),
    )
