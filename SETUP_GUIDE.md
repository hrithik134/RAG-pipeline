# RAG Pipeline - Complete Setup Guide

This guide covers setup for both Docker and local development with all Phase 5 features.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Docker - Recommended)](#quick-start-docker---recommended)
- [Local Development Setup](#local-development-setup)
- [Phase 5 Features](#phase-5-features)
- [Configuration](#configuration)
- [Testing the API](#testing-the-api)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required for Both Setups:
- **Python 3.10+**
- **Docker Desktop** (running)
- **API Keys**:
  - Google AI API Key (for embeddings and LLM)
  - Pinecone API Key (for vector storage)

### Additional for Local Development:
- **Redis** (optional, for rate limiting)
- **PostgreSQL** (via Docker is fine)

---

## Quick Start (Docker - Recommended)

### 1. Clone and Configure

```powershell
# Navigate to project directory
cd "D:\RAG pipeline"

# Copy environment template
Copy-Item .env.example .env

# Edit .env and add your API keys
notepad .env
```

Add your keys to `.env`:
```bash
GOOGLE_API_KEY=your_google_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_index_name
```

### 2. Start with Docker

```powershell
# Use the provided startup script
.\START_DOCKER.ps1

# OR manually:
docker-compose up -d --build
```

### 3. Verify It's Running

```powershell
# Check container status
docker-compose ps

# Test the API
curl http://localhost:8000/

# Check health
curl http://localhost:8000/health
```

### 4. Access the API

- **API Root**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

---

## Local Development Setup

### 1. Setup Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Database

```powershell
# Start PostgreSQL in Docker
docker-compose up -d postgres

# Wait for it to be ready (check with):
docker-compose ps

# Run migrations
alembic upgrade head
```

### 3. Configure Environment

```powershell
# Copy and edit .env
Copy-Item .env.example .env
notepad .env
```

**For local development**, rate limiting is disabled by default. If you want to enable it:

```bash
# Add to .env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/0
```

Then start Redis:
```powershell
docker-compose up -d redis
```

### 4. Start the Application

```powershell
# Use the provided script
.\start_local.ps1

# OR manually:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Phase 5 Features

Your RAG Pipeline now includes:

### ✅ Rate Limiting
- **Endpoint-specific limits**:
  - Upload: 10 requests/hour
  - Query: 20 requests/minute
  - Read operations: 100 requests/minute
  - Delete: 20 requests/minute
  - Health: 300 requests/minute
  - Metrics: 30 requests/minute
- **Redis-backed** (in Docker) for distributed rate limiting
- **Disabled by default** in local development

### ✅ Enhanced Error Handling
- Consistent error response format
- Detailed validation errors
- Request tracing with unique IDs
- Proper HTTP status codes

### ✅ Pagination
- All list endpoints support pagination
- Query parameters: `page` (default: 1) and `limit` (default: 10, max: 100)
- Response includes metadata: total items, total pages, has_next, has_prev

### ✅ Input Validation
- Pydantic models with field validators
- Query string validation (length, content)
- File upload validation (type, size)
- Parameter range validation (top_k, temperature, etc.)

### ✅ Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- Content Security Policy
- API version headers

### ✅ API Documentation
- **Swagger UI** at `/docs` with examples
- **ReDoc** at `/redoc` with detailed schemas
- OpenAPI 3.0 specification
- Request/response examples
- Endpoint descriptions and tags

### ✅ Health & Metrics
- **Health Check** (`/health`):
  - Service status
  - Database connectivity
  - Redis connectivity (if enabled)
  - Pinecone connectivity
  - Configuration info
- **Metrics** (`/metrics`):
  - Total documents, uploads, queries
  - Recent activity
  - Processing status
  - Average query latency

---

## Configuration

### Environment Variables

#### Core Settings
```bash
# App Configuration
APP_NAME=RAG Pipeline
APP_VERSION=0.1.0
APP_ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_db

# File Upload
UPLOAD_DIR=./uploads
MAX_DOCUMENTS_PER_UPLOAD=20
MAX_PAGES_PER_DOCUMENT=1000
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,txt,md
```

#### API Keys (Required)
```bash
# Google AI
GOOGLE_API_KEY=your_key_here
GOOGLE_MODEL=gemini-2.0-flash-exp
GOOGLE_EMBEDDING_MODEL=models/text-embedding-004

# Pinecone
PINECONE_API_KEY=your_key_here
PINECONE_INDEX_NAME=your_index_name
PINECONE_DIMENSION=768
```

#### Phase 5 Settings
```bash
# Rate Limiting
RATE_LIMIT_ENABLED=false  # Set to true to enable
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/0
RATE_LIMIT_UPLOAD=10/hour
RATE_LIMIT_QUERY=20/minute
RATE_LIMIT_READ=100/minute
RATE_LIMIT_DELETE=20/minute
RATE_LIMIT_HEALTH=300/minute
RATE_LIMIT_METRICS=30/minute
```

### Docker vs Local Configuration

| Feature | Docker | Local (Default) |
|---------|--------|----------------|
| Database | PostgreSQL (Docker) | PostgreSQL (Docker) |
| Redis | Running (for rate limits) | Not required |
| Rate Limiting | **Enabled** | **Disabled** |
| Hot Reload | Yes (with volume mount) | Yes (uvicorn --reload) |
| Port | 8000 | 8000 |

---

## Testing the API

### 1. Root Endpoint
```powershell
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "Welcome to RAG Pipeline API 🚀",
  "version": "0.1.0",
  "status": "running",
  "documentation": {
    "swagger_ui": "RAG Pipeline - Swagger UI at /docs",
    "redoc": "RAG Pipeline - ReDoc at /redoc"
  },
  "endpoints": { ... },
  "features": {
    "rate_limiting": true,
    "embedding_provider": "google",
    "llm_provider": "google",
    "retrieval_method": "hybrid"
  }
}
```

### 2. Health Check
```powershell
curl http://localhost:8000/health
```

### 3. Metrics
```powershell
curl http://localhost:8000/metrics
```

### 4. Upload Documents
```powershell
# Using Swagger UI (recommended)
# Navigate to http://localhost:8000/docs
# Find POST /v1/documents/upload
# Click "Try it out"
# Upload your PDF files

# Or use curl:
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@path/to/your/file.pdf"
```

### 5. Query Documents
```powershell
curl -X POST "http://localhost:8000/v1/query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic of the documents?",
    "top_k": 5,
    "upload_id": "your-upload-id-here"
  }'
```

### 6. Test Pagination
```powershell
# Get documents with pagination
curl "http://localhost:8000/v1/documents?page=1&limit=10"
```

### 7. Test Rate Limiting (Docker only)
```powershell
# Make multiple requests quickly to trigger rate limit
for ($i=1; $i -le 25; $i++) {
    curl http://localhost:8000/v1/documents
    Write-Host "Request $i"
}
```

---

## Troubleshooting

### ❌ Localhost Page is Blank

**Solution**: Make sure you're accessing the correct URL:
- ✅ Correct: `http://localhost:8000/` (with trailing slash)
- ✅ Correct: `http://localhost:8000/docs`
- ❌ Wrong: `http://localhost:8000` (without trailing slash in some browsers)

Or use the root endpoint which now returns JSON with API information.

### ❌ Connection Refused Error

**Problem**: Redis connection error in local development.

**Solution**:
```powershell
# Check if rate limiting is enabled
python -c "from app.config import settings; print(settings.rate_limit_enabled)"

# If True, either:
# Option 1: Disable rate limiting (recommended for local dev)
# Set RATE_LIMIT_ENABLED=false in .env

# Option 2: Start Redis
docker-compose up -d redis
```

### ❌ Docker Container Won't Start

```powershell
# Check container logs
docker-compose logs app

# Check specific service
docker-compose logs postgres
docker-compose logs redis

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### ❌ Database Migration Errors

```powershell
# Reset database
docker-compose down -v postgres
docker-compose up -d postgres

# Wait a few seconds, then migrate
alembic upgrade head
```

### ❌ Import Errors

```powershell
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### ❌ Port 8000 Already in Use

```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with the number you see)
taskkill /PID <PID> /F

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### ❌ API Keys Not Working

1. Check `.env` file exists and has your keys
2. Restart the application/container after adding keys
3. Verify keys are correct (no extra spaces, quotes, etc.)
4. For Docker, make sure docker-compose.yml passes the env vars

---

## Useful Commands

### Docker Management
```powershell
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart app

# View logs
docker-compose logs -f app

# Check status
docker-compose ps

# Clean everything (including volumes)
docker-compose down -v
```

### Local Development
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run tests
pytest

# Check code style
black app/ --check
flake8 app/

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Next Steps

1. ✅ **Explore the API**: Open http://localhost:8000/docs
2. ✅ **Upload Documents**: Try the upload endpoint with sample PDFs
3. ✅ **Test Querying**: Ask questions about your documents
4. ✅ **Check Metrics**: Monitor your API usage
5. ✅ **Read Documentation**: See `PHASE_5_QUICKSTART.md` for examples

---

## Additional Resources

- **Phase 5 Quick Start**: `PHASE_5_QUICKSTART.md`
- **Phase 5 Complete Documentation**: `PHASE_5_COMPLETE.md`
- **Docker Guide**: `DOCKER_GUIDE.md`
- **Main README**: `README.md`

---

## Support

If you encounter issues:

1. Check this troubleshooting section
2. Review the logs: `docker-compose logs -f`
3. Verify your `.env` configuration
4. Check that all API keys are correct
5. Ensure Docker Desktop is running

For Phase 5 specific issues, see `PHASE_5_COMPLETE.md` for detailed feature documentation.

