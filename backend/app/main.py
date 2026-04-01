from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.limiter import limiter
from app.api.routes import auth, papers, export, share
from app.core.config import settings

try:
    from slowapi.extension import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
except ImportError:  # pragma: no cover - local fallback when dependency is absent
    _rate_limit_exceeded_handler = None
    RateLimitExceeded = None
    SlowAPIMiddleware = None

app = FastAPI(title="PaperRelay API", version="0.1.0")

# Add rate limiter
app.state.limiter = limiter
if RateLimitExceeded and _rate_limit_exceeded_handler:
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
if SlowAPIMiddleware:
    app.add_middleware(SlowAPIMiddleware)

app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(export.router, prefix="/api/papers", tags=["export"])
app.include_router(share.router, prefix="/api", tags=["share"])

def get_llm_runtime_info():
    provider = settings.LLM_PROVIDER.lower().strip()
    if provider == "azure":
        return {
            "provider": "azure",
            "model": settings.AZURE_OPENAI_MODEL or None,
            "base_url_configured": bool(settings.AZURE_OPENAI_BASE_URL),
        }
    return {
        "provider": "openai",
        "model": settings.OPENAI_MODEL or None,
        "base_url_configured": False,
    }

@app.get("/health")
async def health_check():
    """Health check with dependency status."""
    health = {
        "status": "healthy",
        "version": "0.1.0",
        "dependencies": {},
        "llm": get_llm_runtime_info(),
    }
    
    # Check database
    try:
        from app.models.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["dependencies"]["database"] = "ok"
    except Exception as e:
        health["dependencies"]["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    # Check Redis
    try:
        from app.core.config import settings
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health["dependencies"]["redis"] = "ok"
    except Exception as e:
        health["dependencies"]["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    return health

@app.get("/")
def root():
    return {
        "message": "PaperRelay API",
        "docs": "/docs",
        "health": "/health",
        "llm": get_llm_runtime_info(),
    }
