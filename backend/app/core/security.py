from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import secrets

from app.core.config import settings

ALGORITHM = "HS256"
SERVER_SESSION_EPOCH = int(datetime.utcnow().timestamp())

def generate_magic_token() -> str:
    return secrets.token_urlsafe(32)

def create_magic_link_token(email: str) -> tuple[str, datetime]:
    expire = datetime.utcnow() + timedelta(hours=settings.MAGIC_LINK_EXPIRY_HOURS)
    to_encode = {"email": email, "exp": expire, "type": "magic_link"}
    encoded_jwt = jwt.encode(to_encode, settings.MAGIC_LINK_SECRET, algorithm=ALGORITHM)
    return encoded_jwt, expire

def create_session_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {
        "email": email,
        "exp": expire,
        "type": "session",
        "server_session_epoch": SERVER_SESSION_EPOCH,
    }
    return jwt.encode(to_encode, settings.MAGIC_LINK_SECRET, algorithm=ALGORITHM)

def verify_magic_link_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.MAGIC_LINK_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "magic_link":
            return None
        return payload.get("email")
    except JWTError:
        return None

def verify_session_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.MAGIC_LINK_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "session":
            return None
        if payload.get("server_session_epoch") != SERVER_SESSION_EPOCH:
            return None
        return payload.get("email")
    except JWTError:
        return None
