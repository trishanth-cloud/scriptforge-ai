"""
ScriptForge AI — Main Application Entry Point
FastAPI application configured with CORS, routers, database initialization, and AI pipeline.
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_execution, routes_files, routes_results, routes_tasks
from app.config import settings
from app.database import init_db
from app.models.schemas import HealthResponse
from app.services.ai_engine import AIEngine
from app.services.pipeline import Pipeline

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scriptforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: database initialization and service setup."""
    logger.info("Initializing ScriptForge AI database...")
    init_db()

    logger.info("Initializing AI Engine (Model: %s)...", settings.AI_MODEL)
    ai_engine = AIEngine()
    pipeline = Pipeline(ai_engine)

    app.state.ai_engine = ai_engine
    app.state.pipeline = pipeline

    if ai_engine.mock_mode:
        logger.warning(
            "GEMINI_API_KEY not configured. Running in intelligent template/mock mode. "
            "To use live Gemini AI, set GEMINI_API_KEY in backend/.env"
        )
    else:
        logger.info("Gemini AI Engine active and ready.")

    yield

    logger.info("ScriptForge AI shutting down.")


app = FastAPI(
    title="ScriptForge AI",
    description="Autonomous Text-to-Script AI Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(routes_files.router)
app.include_router(routes_tasks.router)
app.include_router(routes_execution.router)
app.include_router(routes_results.router)


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint to verify backend operational status."""
    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        version="1.0.0",
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
