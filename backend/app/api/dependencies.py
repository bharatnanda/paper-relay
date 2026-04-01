from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import re

from app.models.database import get_db
from app.models.user import User
from app.core.security import verify_session_token

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    email = verify_session_token(credentials.credentials)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

def validate_arxiv_url(url: str) -> Optional[str]:
    patterns = [r'arxiv\.org/abs/(\d{4}\.\d{4,5})', r'arxiv\.org/pdf/(\d{4}\.\d{4,5})']
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
