from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.database import engine
from sqlalchemy import text


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Core transactionnel de démonstration ProFin : portefeuille, instruments, transactions, comptabilité et audit.",
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=settings.ALLOW_CREDENTIALS, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["System"])
def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "docs": f"{settings.API_V1_PREFIX}/docs"}


@app.get("/health", tags=["System"])
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        return {"status": "degraded", "database": "unavailable"}
