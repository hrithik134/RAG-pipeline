# RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) pipeline that allows users to upload documents and ask questions based on their content. The system leverages Pinecone vector database for efficient retrieval and LLM APIs (OpenAI/Gemini) for generating contextual responses.

## Quick Start

### Prerequisites
- **Docker Desktop** installed and running
- **API Keys**: Pinecone and either OpenAI or Google AI

### 1. Clone Repository
```bash
git clone <repository-url>
cd rag-pipeline
```

### 2. Configure Environment
```bash
# Copy environment template
Copy-Item env.example .env

# Edit .env with your API keys
notepad .env
```

Required keys in `.env`:
```bash
# Pinecone (Required)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=ragingestion-google

# Choose one LLM provider:
# OpenAI
OPENAI_API_KEY=sk-your_openai_key
LLM_PROVIDER=openai

# OR Google AI
GOOGLE_API_KEY=your_google_key
LLM_PROVIDER=google
```

### 3. Start with Docker
```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Verify installation
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "RAG Pipeline",
  "version": "1.0.0",
  "environment": "development"
}
```

### 4. Access API
- **API Base**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Features

- **Document Ingestion**: Upload up to 20 documents (max 1000 pages each) with support for PDF, DOCX, and TXT formats
- **Intelligent Chunking**: Token-aware text chunking with configurable overlap for optimal retrieval
- **Vector Search**: Pinecone-powered semantic search with optional hybrid retrieval
- **Multi-LLM Support**: Configurable LLM providers (OpenAI GPT-4o-mini, Google Gemini)
- **REST API**: FastAPI-based RESTful API with OpenAPI documentation
- **Metadata Storage**: PostgreSQL for document and chunk metadata
- **Containerized**: Docker and Docker Compose for easy deployment
- **Production Ready**: Rate limiting, CORS, health checks, and comprehensive error handling

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (includes Docker Compose v2)
- **Git**
- **Python 3.10+** (for local development)

You'll also need API keys:
- **Pinecone API key** ([Get it here](https://www.pinecone.io/))
- **OpenAI API key** ([Get it here](https://platform.openai.com/account/api-keys)) OR
- **Google AI API key** ([Get it here](https://aistudio.google.com/app/apikey))

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         FastAPI Application         │
│  ┌──────────┐  ┌────────────────┐  │
│  │ Routers  │  │   Services     │  │
│  │          │  │                │  │
│  │ Upload   │──│ Ingestion      │  │
│  │ Query    │  │ Embedding      │  │
│  │ Metadata │  │ Retrieval      │  │
│  └──────────┘  │ Generation     │  │
│                └────────────────┘  │
└───────┬─────────────┬──────────────┘
        │             │
        ▼             ▼
  ┌──────────┐  ┌──────────┐
  │ Postgres │  │ Pinecone │
  │ Metadata │  │  Vectors │
  └──────────┘  └──────────┘
```

## Installation & Setup

### Option 1: Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd rag-pipeline
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file with your API keys:**
   ```bash
   # Required
   PINECONE_API_KEY=your_pinecone_api_key
   OPENAI_API_KEY=your_openai_api_key

   # Optional: for Google Gemini
   GOOGLE_API_KEY=your_google_api_key
   ```

4. **Build and start services:**
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

6. **Verify installation:**
   ```bash
   curl http://localhost:8000/health
   ```

### Option 2: Local Development

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd rag-pipeline
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start PostgreSQL** (via Docker or local installation)
   ```bash
   docker run -d \
     --name postgres \
     -e POSTGRES_USER=rag_user \
     -e POSTGRES_PASSWORD=rag_password \
     -e POSTGRES_DB=rag_db \
     -p 5432:5432 \
     postgres:15
   ```

6. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

7. **Start the application:**
   ```bash
   python -m app.main
   ```

## API Usage

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### cURL Examples

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "RAG Pipeline",
  "version": "1.0.0",
  "environment": "development"
}
```

#### 2. Upload Documents
```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@document.pdf" \
  -F "files=@another.pdf"
```

**Response:**
```json
{
  "upload_batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "total_documents": 2,
  "successful_documents": 2,
  "failed_documents": 0,
  "documents": [...]
}
```

#### 3. Query Documents
```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What is machine learning?\"}"
```

**Response:**
```json
{
  "query": "What is machine learning?",
  "answer": "Machine learning is...",
  "chunks": [...],
  "processing_time": 1.23
}
```

#### 4. List All Documents
```bash
curl http://localhost:8000/v1/documents
```

#### 5. Get Document Details
```bash
curl http://localhost:8000/v1/documents/{document_id}
```

#### 6. Delete Document
```bash
curl -X DELETE http://localhost:8000/v1/documents/{document_id}
```

### For Complete API Reference
See [docs/api-examples.md](docs/api-examples.md) for detailed examples of all endpoints.

## Configuration

### LLM Provider Selection

#### Using OpenAI (Default)
```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

#### Using Google Gemini
```bash
# .env
LLM_PROVIDER=google
GOOGLE_API_KEY=...
GOOGLE_MODEL=gemini-1.5-pro
GOOGLE_EMBEDDING_MODEL=models/text-embedding-004
```

### Pinecone Configuration
```bash
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=rag-documents
PINECONE_DIMENSION=1536  # For text-embedding-3-large
```

### Document Processing
```bash
MAX_DOCUMENTS_PER_UPLOAD=20
MAX_PAGES_PER_DOCUMENT=1000
MAX_FILE_SIZE_MB=50
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```

### Retrieval Configuration
```bash
RETRIEVAL_TOP_K=10
MMR_LAMBDA=0.5
USE_HYBRID_SEARCH=false
```

## Testing

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test types:
```bash
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
```

### View coverage report:
```bash
open htmlcov/index.html  # On macOS
# or
start htmlcov/index.html # On Windows
```

## Deployment

### Local Deployment
```bash
docker-compose up -d
```

### Cloud Deployment
*Detailed cloud deployment guides (AWS, GCP, Azure) will be provided in Phase 9.*

## Project Structure

```
rag-pipeline/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models/              # Database models
│   ├── routers/             # API endpoints
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── utils/               # Utility functions
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── uploads/                 # Uploaded documents (gitignored)
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project metadata
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Multi-container setup (TBD)
└── README.md               # This file
```

## Development

### Code Quality Tools

The project uses:
- **Black**: Code formatting
- **Ruff**: Fast linting
- **mypy**: Type checking
- **pytest**: Testing framework

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

Run manually:
```bash
pre-commit run --all-files
```

### Code Formatting
```bash
black app tests
```

### Linting
```bash
ruff check app tests --fix
```

### Type Checking
```bash
mypy app
```

## Performance & Limits

- **Max documents per upload**: 20
- **Max pages per document**: 1,000
- **Max file size**: 50 MB (configurable)
- **Supported formats**: PDF, DOCX, TXT
- **Default chunk size**: 1,000 tokens
- **Default chunk overlap**: 150 tokens
- **Rate limiting**: 100 requests/minute (configurable)

## Troubleshooting

### Docker Issues
```bash
# Rebuild containers
docker-compose build --no-cache

# View logs
docker-compose logs -f api

# Reset everything
docker-compose down -v
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec api alembic upgrade head
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Contact

[Add contact information here]

---

**Status**: Phase 8 Complete

- [x] Phase 0: Project scaffold with FastAPI
- [x] Phase 1: Database models
- [x] Phase 2: Document ingestion
- [x] Phase 3: Embeddings & Pinecone
- [x] Phase 4: RAG retrieval & generation
- [x] Phase 5: REST API endpoints
- [x] Phase 6: Docker Compose
- [x] Phase 7: Comprehensive tests
- [x] Phase 8: Complete documentation
- [ ] Phase 9: CI/CD & cloud deployment

---

## Documentation

For detailed documentation, see the [docs/](docs/) directory:

- **[Architecture](docs/architecture.md)** - System architecture and design
- **[API Examples](docs/api-examples.md)** - Complete API reference with cURL
- **[Operations](docs/operations.md)** - Operational runbook and troubleshooting
- **[Configuration](docs/configuration.md)** - Environment variables and setup
