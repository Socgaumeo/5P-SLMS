"""
Health API - Health check endpoints
"""

from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "slms-backend"}


@router.get("/health/db")
async def db_health_check():
    """Database connectivity check"""
    from app.services.data_service import get_data_service
    
    try:
        data_service = get_data_service()
        conn = data_service._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        return {"status": "unhealthy", "database": str(e)}


@router.get("/health/ai")
async def ai_health_check():
    """AI service check"""
    from app.core.config import settings
    
    return {
        "status": "configured",
        "provider": settings.AI_PROVIDER,
        "gemini_configured": bool(settings.GOOGLE_GEMINI_API_KEY),
        "deepseek_configured": bool(settings.DEEPSEEK_API_KEY)
    }
