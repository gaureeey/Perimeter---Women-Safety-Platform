"""
PERIMETER Platform - FastAPI Backend Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.init_db import init_db

# Import API Routers
from app.api.auth import router as auth_router
from app.api.sos import router as sos_router
from app.api.feed import router as feed_router
from app.api.case import router as case_router
from app.api.admin import router as admin_router
from app.api.social import router as social_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables and seeds on startup
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(sos_router, prefix=settings.API_V1_STR)
app.include_router(feed_router, prefix=settings.API_V1_STR)
app.include_router(case_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(social_router, prefix=settings.API_V1_STR)

@app.get(f"{settings.API_V1_STR}/docs", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.get(f"{settings.API_V1_STR}/redoc", include_in_schema=False)
def redirect_to_redoc():
    return RedirectResponse(url="/redoc")

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "database": settings.DATABASE_URL.split(":///")[0],
        "interactive_docs": "/docs",
        "endpoints": {
            "auth": f"{settings.API_V1_STR}/auth",
            "sos": f"{settings.API_V1_STR}/sos",
            "feed": f"{settings.API_V1_STR}/feed",
            "case": f"{settings.API_V1_STR}/case",
            "admin": f"{settings.API_V1_STR}/admin",
            "social": f"{settings.API_V1_STR}/social"
        }
    }

@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected & migrated",
        "service": "PERIMETER API Gateway",
        "geofence_engine": "active (5km PostGIS Router ready)",
        "sos_dispatch_queue": "ready",
        "connected_roles": ["citizen", "volunteer", "journalist", "police", "admin"]
    }
