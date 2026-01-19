"""
SLMS Backend - FastAPI Application
Main entry point with Chat UI API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api import chat, jobs, health

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting SLMS Backend...")
    logger.info(f"📊 Database: {settings.DATABASE_URL[:50]}...")
    logger.info(f"🤖 AI Provider: {settings.AI_PROVIDER}")
    yield
    logger.info("👋 Shutting down SLMS Backend...")


app = FastAPI(
    title="SLMS Backend",
    description="Short-haul Logistics Management System - Chat UI API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])


@app.get("/")
async def root():
    return {
        "message": "SLMS Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics"""
    from app.api.jobs import get_dashboard_stats
    return await get_dashboard_stats()


@app.get("/api/services/{service_type}")
async def services_by_type(service_type: str):
    """Get service-specific data (trucking, warehouse, customs, packing)"""
    from app.api.jobs import get_service_data
    return await get_service_data(service_type)


@app.get("/api/customers")
async def list_customers():
    """Get customers for dropdown in job creation form"""
    from app.services.data_service import get_data_service
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT customer_id, customer_code, short_name, full_name 
            FROM customers 
            WHERE is_active = true
            ORDER BY customer_code
        """)
        customers = [dict(row) for row in cursor.fetchall()]
        return {"customers": customers}
    except Exception as e:
        return {"customers": [], "error": str(e)}
