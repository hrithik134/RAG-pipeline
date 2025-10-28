"""
FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import SessionLocal, get_db
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.security import add_security_headers

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")

    # Create upload directory if not exists
    try:
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Upload directory created/verified: {upload_dir}")
    except Exception as e:
        logger.error(f"Failed to create upload directory: {e}")

    # TODO: Initialize database connections
    # from app.database import init_db, engine
    # try:
    #     await init_db()
    #     logger.info("Database initialized successfully")
    # except Exception as e:
    #     logger.error(f"Failed to initialize database: {e}")

    # TODO: Initialize Pinecone client
    # from app.services.vector_store import init_pinecone
    # try:
    #     await init_pinecone()
    #     logger.info("Pinecone client initialized successfully")
    # except Exception as e:
    #     logger.error(f"Failed to initialize Pinecone: {e}")

    # TODO: Initialize LLM clients
    # from app.services.llm import init_llm_clients
    # try:
    #     init_llm_clients()
    #     logger.info("LLM clients initialized successfully")
    # except Exception as e:
    #     logger.error(f"Failed to initialize LLM clients: {e}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application")
    
    # TODO: Close database connections
    # try:
    #     await engine.dispose()
    #     logger.info("Database connections closed")
    # except Exception as e:
    #     logger.error(f"Error closing database connections: {e}")

    # TODO: Close other resources
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
# RAG Pipeline API

A professional **Retrieval-Augmented Generation (RAG)** system that allows you to:

- 📤 **Upload documents** (PDF, DOCX, TXT, MD)
- 🔍 **Ask questions** about your documents
- 🤖 **Get AI-powered answers** with accurate citations
- 📊 **Track processing** and query history

## Features

### Document Management
- Upload up to 20 files per batch
- Support for PDF, DOCX, TXT, and Markdown files
- Automatic text extraction and chunking
- Duplicate detection via file hashing
- Background embedding generation

### Intelligent Querying
- Hybrid search (semantic + keyword matching)
- MMR (Maximal Marginal Relevance) for diverse results
- Automatic citation generation
- Support for OpenAI and Google AI models
- Query history tracking

### Production-Ready
- Rate limiting to prevent abuse
- Input validation and error handling
- Pagination for large result sets
- Security headers
- Health checks and metrics
- Comprehensive API documentation

## Quick Start

1. **Upload Documents**
   ```bash
   POST /v1/documents/upload
   ```

2. **Ask Questions**
   ```bash
   POST /v1/query
   {
     "query": "What are the main topics in these documents?"
   }
   ```

3. **View Results**
   - Get answers with citations
   - Review source documents
   - Track query history

## Rate Limits

- Uploads: 10 per hour
- Queries: 20 per minute
- Read operations: 100 per minute
- Delete operations: 20 per minute

## Authentication

Currently, the API uses IP-based rate limiting. API key authentication can be added for production use.
    """,
    docs_url="/docs" if settings.docsenabled else None,
    redoc_url="/redoc" if settings.docsenabled else None,
    lifespan=lifespan,
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "System",
            "description": "Health checks, metrics, and system status endpoints"
        },
        {
            "name": "Documents",
            "description": "Upload, manage, and retrieve documents"
        },
        {
            "name": "Query",
            "description": "Ask questions and get AI-powered answers from your documents"
        }
    ],
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.middleware("http")(add_security_headers)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with detailed error messages.
    """
    logger.warning(f"Validation error for {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": str(exc.body) if hasattr(exc, 'body') else None
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(f"Unhandled exception for {request.url}: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


# Health check endpoint
@app.get("/health", tags=["System"])
@limiter.limit(settings.rate_limit_health)
async def health_check(request: Request):
    """
    Health check endpoint to verify service is running.
    Returns service status and configuration information.
    
    Checks the status of:
    - API service (always healthy if responding)
    - Database connection
    - Redis connection (if rate limiting enabled)
    - Pinecone connection (if configured)
    
    Rate limited to 300 requests per minute.
    """
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "services": {}
    }
    
    # Check database
    try:
        from sqlalchemy import text
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis (if rate limiting enabled)
    if settings.rate_limit_enabled:
        try:
            import redis
            r = redis.from_url(settings.rate_limit_storage_url)
            r.ping()
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
    
    # Check Pinecone (if configured)
    if settings.pinecone_api_key:
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=settings.pinecone_api_key)
            # Just check if we can list indexes
            pc.list_indexes()
            health_status["services"]["pinecone"] = "healthy"
        except Exception as e:
            health_status["services"]["pinecone"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status


@app.get("/metrics", tags=["System"])
@limiter.limit(settings.rate_limit_metrics)
async def get_metrics(request: Request):
    """
    Get system metrics and statistics.
    
    Returns:
    - Total documents processed
    - Total queries handled
    - Total uploads
    - Active processing status
    - Average response times
    
    Rate limited to 30 requests per minute.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app.database import SessionLocal
    from app.models.document import Document
    from app.models.upload import Upload
    from app.models.query import Query
    
    db = SessionLocal()
    try:
        # Get total counts
        total_documents = db.query(func.count(Document.id)).scalar() or 0
        total_uploads = db.query(func.count(Upload.id)).scalar() or 0
        total_queries = db.query(func.count(Query.id)).scalar() or 0
        
        # Get recent activity (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_documents = db.query(func.count(Document.id)).filter(
            Document.created_at >= one_hour_ago
        ).scalar() or 0
        recent_queries = db.query(func.count(Query.id)).filter(
            Query.created_at >= one_hour_ago
        ).scalar() or 0
        
        # Get average query latency
        avg_latency = db.query(func.avg(Query.latency_ms)).scalar() or 0
        
        # Get processing status counts
        from app.models.document import DocumentStatus
        processing_count = db.query(func.count(Document.id)).filter(
            Document.status == DocumentStatus.PROCESSING
        ).scalar() or 0
        
        completed_count = db.query(func.count(Document.id)).filter(
            Document.status == DocumentStatus.COMPLETED
        ).scalar() or 0
        
        failed_count = db.query(func.count(Document.id)).filter(
            Document.status == DocumentStatus.FAILED
        ).scalar() or 0
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "totals": {
                "documents": total_documents,
                "uploads": total_uploads,
                "queries": total_queries
            },
            "recent_activity": {
                "documents_last_hour": recent_documents,
                "queries_last_hour": recent_queries
            },
            "document_status": {
                "processing": processing_count,
                "completed": completed_count,
                "failed": failed_count
            },
            "performance": {
                "average_query_latency_ms": round(float(avg_latency), 2) if avg_latency else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving metrics: {str(e)}"
        )
    finally:
        db.close()


# Include routers
from app.routers import upload, query

app.include_router(upload.router)
app.include_router(query.router)


# Root endpoint
@app.get("/", tags=["System"], summary="API Root", description="Returns API information and available endpoints")
async def root():
    """
    Root endpoint - Returns API information and available endpoints.
    
    This endpoint provides a quick overview of the API, its version, and links to documentation.
    """
    return {
        "message": "Welcome to RAG Pipeline API 🚀",
        "version": settings.app_version,
        "environment": settings.app_env,
        "status": "running",
        "documentation": {
            "swagger_ui": f"{settings.app_name} - Swagger UI at /docs",
            "redoc": f"{settings.app_name} - ReDoc at /redoc",
            "openapi_json": "OpenAPI schema at /openapi.json"
        },
        "endpoints": {
            "health": "GET /health - Health check with service status",
            "metrics": "GET /metrics - System metrics and statistics",
            "upload": "POST /v1/documents/upload - Upload and process documents",
            "documents": "GET /v1/documents - List all documents",
            "query": "POST /v1/query - Ask questions to your documents"
        },
        "features": {
            "rate_limiting": settings.rate_limit_enabled,
            "embedding_provider": settings.embedding_provider,
            "llm_provider": settings.llm_provider,
            "retrieval_method": settings.retrieval_method
        }
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting application in development mode")
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )