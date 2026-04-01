from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.models.user import User
from app.models.paper import Paper
from app.core.security import create_magic_link_token, create_session_token, verify_magic_link_token

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def request_magic_link(self, email: str) -> tuple:
        token, expires_at = create_magic_link_token(email)
        user = self.db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(email=email)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return token, expires_at

    def verify_magic_link(self, token: str) -> Optional[User]:
        email = verify_magic_link_token(token)
        if email is None:
            return None
        user = self.db.query(User).filter(User.email == email).first()
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user

    def create_session_token(self, user: User) -> str:
        return create_session_token(user.email)

    def get_user_papers(self, user: User) -> list:
        return self.db.query(Paper).filter(Paper.user_id == user.id).all()
