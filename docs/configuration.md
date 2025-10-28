# Configuration Guide

Complete reference for all environment variables and configuration options.

---

## Environment Variables Overview

Configuration is managed via `.env` file. Copy `env.example` to `.env` and fill in your values:

```bash
cp env.example .env
```

---

## Required Configuration

### Pinecone (Required)

Pinecone is used for vector storage. [Get your API key here](https://www.pinecone.io/)

```bash
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=ragingestion-google
PINECONE_DIMENSION=768
PINECONE_METRIC=cosine
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

**Settings**:
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_INDEX_NAME`: Name of the Pinecone index
- `PINECONE_DIMENSION`: Embedding dimension (768 for OpenAI/Google)
- `PINECONE_METRIC`: Similarity metric (cosine, euclidean, dotproduct)
- `PINECONE_CLOUD`: Cloud provider (aws, gcp, azure)
- `PINECONE_REGION`: Region (us-east-1, eu-west-1, etc.)

---

## LLM Provider Selection

You must choose either OpenAI or Google AI as your LLM and embedding provider.

### Option 1: Using OpenAI (Default)

[Get your API key here](https://platform.openai.com/account/api-keys)

```bash
# Provider selection
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai

# OpenAI configuration
OPENAI_API_KEY=sk-your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_MAX_TOKENS=2048
OPENAI_TEMPERATURE=0.1
```

**Settings**:
- `OPENAI_API_KEY`: Your OpenAI API key (starts with `sk-`)
- `OPENAI_MODEL`: LLM model (gpt-4o-mini, gpt-4, etc.)
- `OPENAI_EMBEDDING_MODEL`: Embedding model (text-embedding-3-large, text-embedding-3-small)
- `OPENAI_MAX_TOKENS`: Maximum tokens in response (default: 2048)
- `OPENAI_TEMPERATURE`: Sampling temperature (0.0-2.0, default: 0.1)

### Option 2: Using Google AI

[Get your API key here](https://aistudio.google.com/app/apikey)

```bash
# Provider selection
LLM_PROVIDER=google
EMBEDDING_PROVIDER=google

# Google AI configuration
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL=gemini-2.5-pro
GOOGLE_EMBEDDING_MODEL=models/text-embedding-004
GOOGLE_TEMPERATURE=0.1
GOOGLE_MAX_TOKENS=2048
```

**Settings**:
- `GOOGLE_API_KEY`: Your Google AI API key
- `GOOGLE_MODEL`: LLM model (gemini-2.5-pro, gemini-1.5-pro, etc.)
- `GOOGLE_EMBEDDING_MODEL`: Embedding model (models/text-embedding-004)
- `GOOGLE_MAX_TOKENS`: Maximum tokens in response (default: 2048)
- `GOOGLE_TEMPERATURE`: Sampling temperature (0.0-2.0, default: 0.1)

**Important**: Set `PINECONE_DIMENSION=768` for Google AI embeddings.

---

## Application Configuration

### Basic Settings

```bash
APP_NAME="RAG Pipeline"
APP_VERSION="1.0.0"
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

**Settings**:
- `APP_NAME`: Application name
- `APP_VERSION`: Application version
- `APP_ENV`: Environment (development, production)
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `API_HOST`: Host to bind to (0.0.0.0 for all interfaces)
- `API_PORT`: Port to listen on
- `API_WORKERS`: Number of Gunicorn workers

### Database Configuration

```bash
DATABASE_URL=postgresql://rag_user:rag_password@postgres:5432/rag_db
DB_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

**Settings**:
- `DATABASE_URL`: PostgreSQL connection string
  - Docker: `postgresql://rag_user:rag_password@postgres:5432/rag_db`
  - Local: `postgresql://rag_user:rag_password@localhost:5432/rag_db`
- `DB_ECHO`: Log all SQL queries (false in production)
- `DB_POOL_SIZE`: Connection pool size
- `DB_MAX_OVERFLOW`: Maximum overflow connections

### Redis Configuration

```bash
REDIS_URL=redis://redis:6379/0
```

**Settings**:
- `REDIS_URL`: Redis connection string
  - Docker: `redis://redis:6379/0`
  - Local: `redis://localhost:6379/0`

---

## Document Processing Configuration

### File Upload Limits

```bash
MAX_DOCUMENTS_PER_UPLOAD=20
MAX_PAGES_PER_DOCUMENT=1000
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,txt,md
UPLOAD_DIR=./uploads
```

**Settings**:
- `MAX_DOCUMENTS_PER_UPLOAD`: Maximum files per upload batch (default: 20)
- `MAX_PAGES_PER_DOCUMENT`: Maximum pages per file (default: 1000)
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 50)
- `ALLOWED_EXTENSIONS`: Comma-separated list of allowed extensions
- `UPLOAD_DIR`: Directory to store uploaded files

### Chunking Configuration

```bash
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
MIN_CHUNK_SIZE=100
```

**Settings**:
- `CHUNK_SIZE`: Target chunk size in tokens (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks in tokens (default: 150)
- `MIN_CHUNK_SIZE`: Minimum chunk size (default: 100)

**Recommendations**:
- Smaller `CHUNK_SIZE` (500-750): Better for short documents
- Larger `CHUNK_SIZE` (1500-2000): Better for long documents
- Higher `CHUNK_OVERLAP` (200-250): Preserves more context

---

## Embedding Configuration

### Batch Processing

```bash
EMBED_BATCH_SIZE=64
UPSERT_BATCH_SIZE=100
INDEX_CONCURRENCY=2
EMBED_RETRY_MAX=5
EMBED_RETRY_DELAY=1.0
```

**Settings**:
- `EMBED_BATCH_SIZE`: Number of chunks to embed per API call (default: 64)
- `UPSERT_BATCH_SIZE`: Number of vectors to upsert per Pinecone call (default: 100)
- `INDEX_CONCURRENCY`: Concurrent indexing threads (default: 2)
- `EMBED_RETRY_MAX`: Maximum retry attempts for failed embeddings
- `EMBED_RETRY_DELAY`: Delay between retries in seconds

---

## RAG Configuration

### Retrieval Settings

```bash
RAG_TOP_K=10
RAG_MMR_LAMBDA=0.5
RAG_MAX_CONTEXT_TOKENS=6000
RAG_TEMPERATURE=0.1
```

**Settings**:
- `RAG_TOP_K`: Number of chunks to retrieve (default: 10)
  - Higher values: More context, slower processing
  - Lower values: Less context, faster processing
- `RAG_MMR_LAMBDA`: MMR diversity parameter (0.0-1.0, default: 0.5)
  - 0.0: Pure relevance
  - 1.0: Pure diversity
- `RAG_MAX_CONTEXT_TOKENS`: Maximum tokens in LLM context
- `RAG_TEMPERATURE`: Generation temperature (0.0-2.0)

### Retrieval Method

```bash
RETRIEVAL_METHOD=hybrid
RETRIEVAL_TOP_K=10
MMR_LAMBDA=0.5
USE_HYBRID_SEARCH=true
BM25_K1=1.2
BM25_B=0.75
RRF_K=60
```

**Settings**:
- `RETRIEVAL_METHOD`: hybrid, semantic, or keyword
- `USE_HYBRID_SEARCH`: Enable hybrid search (combines semantic + BM25)
- `BM25_K1`: BM25 k1 parameter (term frequency saturation)
- `BM25_B`: BM25 b parameter (length normalization)
- `RRF_K`: Reciprocal Rank Fusion parameter

---

## Rate Limiting

### Enable Rate Limiting

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE_URL=redis://redis:6379/0
```

### Rate Limits

```bash
RATE_LIMIT_UPLOAD=10/hour
RATE_LIMIT_QUERY=20/minute
RATE_LIMIT_READ=100/minute
RATE_LIMIT_DELETE=20/minute
RATE_LIMIT_HEALTH=300/minute
RATE_LIMIT_METRICS=30/minute
```

**Settings**:
- `RATE_LIMIT_UPLOAD`: Upload endpoint rate limit
- `RATE_LIMIT_QUERY`: Query endpoint rate limit
- `RATE_LIMIT_READ`: Read endpoints rate limit
- `RATE_LIMIT_DELETE`: Delete endpoint rate limit
- `RATE_LIMIT_HEALTH`: Health check rate limit
- `RATE_LIMIT_METRICS`: Metrics endpoint rate limit

**Format**: `limit/period` where period is `second`, `minute`, `hour`, or `day`

---

## LLM Configuration

### Retry Settings

```bash
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SECONDS=30
```

**Settings**:
- `LLM_MAX_RETRIES`: Maximum retry attempts for LLM calls
- `LLM_TIMEOUT_SECONDS`: Timeout for LLM API calls

---

## CORS Configuration

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000
CORS_ALLOW_CREDENTIALS=true
```

**Settings**:
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `CORS_ALLOW_CREDENTIALS`: Allow credentials in CORS requests

---

## Optional Configuration

### Background Tasks (Celery)

```bash
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

### Monitoring

```bash
ENABLE_METRICS=false
SENTRY_DSN=
```

**Settings**:
- `ENABLE_METRICS`: Enable Prometheus metrics
- `SENTRY_DSN`: Sentry error tracking DSN

### Cloud Storage (Optional)

```bash
USE_CLOUD_STORAGE=false
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_REGION=us-east-1
```

### SSL Configuration (Production)

```bash
SSL_KEYFILE=/path/to/keyfile.pem
SSL_CERTFILE=/path/to/certfile.pem
```

---

## Configuration Examples

### Development

```bash
# .env.development
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Use local PostgreSQL
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_db
REDIS_URL=redis://localhost:6379/0

# Relaxed rate limits
RATE_LIMIT_UPLOAD=100/hour
RATE_LIMIT_QUERY=100/minute
```

### Production

```bash
# .env.production
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Use production database
DATABASE_URL=postgresql://user:pass@prod-db:5432/rag_db
REDIS_URL=redis://prod-redis:6379/0

# Strict rate limits
RATE_LIMIT_UPLOAD=10/hour
RATE_LIMIT_QUERY=20/minute

# Enable security
SSL_KEYFILE=/ssl/keyfile.pem
SSL_CERTFILE=/ssl/certfile.pem
```

---

## Switching LLM Providers

### From OpenAI to Google AI

1. Update `.env`:
```bash
LLM_PROVIDER=google
EMBEDDING_PROVIDER=google
GOOGLE_API_KEY=your_google_key
PINECONE_DIMENSION=768
```

2. Restart services:
```bash
docker-compose restart api
```

### From Google AI to OpenAI

1. Update `.env`:
```bash
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your_openai_key
PINECONE_DIMENSION=768
```

2. Restart services:
```bash
docker-compose restart api
```

**Important**: Embeddings from different providers are not compatible. You'll need to re-index all documents when switching providers.

---

## Testing Configuration

### Verify Configuration

```bash
# Check environment variables
docker-compose exec api env | grep PINECONE
docker-compose exec api env | grep LLM_PROVIDER

# Test database connection
docker-compose exec api python -c "from app.config import settings; print(settings.database_url)"

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Test upload (small file)
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@test.pdf"

# Test query
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query"}'
```

---

## Common Configuration Issues

### Issue: Database Connection Error

**Solution**:
1. Check `DATABASE_URL` in `.env`
2. Ensure PostgreSQL container is running: `docker-compose ps`
3. Verify credentials: `docker-compose exec postgres psql -U rag_user -d rag_db`

### Issue: Pinecone Connection Error

**Solution**:
1. Verify `PINECONE_API_KEY` in `.env`
2. Check Pinecone dashboard for index status
3. Ensure correct `PINECONE_DIMENSION` matches embedding model

### Issue: Rate Limiting Too Strict

**Solution**:
1. Adjust rate limits in `.env`:
   ```bash
   RATE_LIMIT_QUERY=50/minute
   ```
2. Restart services: `docker-compose restart api`

### Issue: Memory Issues

**Solution**:
1. Reduce `CHUNK_SIZE` (e.g., 500 instead of 1000)
2. Increase `API_WORKERS` but decrease workers per container
3. Increase Docker memory limits

---

For more information:
- [Architecture](architecture.md)
- [API Examples](api-examples.md)
- [Operations Guide](operations.md)

