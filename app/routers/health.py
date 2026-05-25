from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import SessionLocal
from app.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Verificar saúde do módulo")
async def health_check():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))

    settings = get_settings()
    return {
        "status": "ok",
        "module": "compras",
        "core_url": settings.core_base_url,
        "database": "sqlite",
    }
