from pydantic import BaseModel, EmailStr

class MagicLinkRequest(BaseModel):
    email: EmailStr

class MagicLinkResponse(BaseModel):
    message: str
    status: str = "link_sent"

class AuthVerifyRequest(BaseModel):
    token: str

class AuthVerifyResponse(BaseModel):
    user_id: str
    email: str
    token: str
    papers_count: int = 0


class AuthSessionResponse(BaseModel):
    user_id: str
    email: str
    papers_count: int = 0
