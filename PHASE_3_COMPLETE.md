# Phase 3 - Embeddings and Pinecone Indexing

## ✅ Implementation Complete

Phase 3 adds automatic embedding generation and vector indexing to the RAG pipeline. Documents uploaded in Phase 2 are now automatically embedded and indexed in Pinecone for semantic search.

---

## 🎯 What Was Built

### 1. **Embedding Providers** (Pluggable Architecture)

**Base Interface** (`app/services/embeddings/base.py`):
- `EmbeddingProvider` abstract class
- `embed_texts()` - Generate embeddings with batching
- `dimension()` - Get embedding dimension
- `model_name()` - Get model identifier
- Helper utilities: text truncation, token counting, dimension validation

**OpenAI Provider** (`app/services/embeddings/openai_provider.py`):
- Default provider using `text-embedding-3-large` (3072D) or `-small` (1536D)
- Automatic batching (default: 64 texts per batch)
- Exponential backoff retry on rate limits (429) and server errors (5xx)
- Token counting for cost tracking
- Input truncation to 8191 tokens

**Vertex AI Provider** (`app/services/embeddings/vertex_provider.py`):
- Stub implementation (behind `EMBEDDING_PROVIDER=vertex` flag)
- Ready for future Google Cloud integration

### 2. **Pinecone Vector Store** (`app/services/vectorstore/pinecone_store.py`)

**Features**:
- Automatic index creation with serverless spec
- Namespace-based multi-tenancy: `upload:{upload_id}` or `tenant:{tenant_id}|upload:{upload_id}`
- Deterministic vector IDs: `chunk:{chunk_id}` (idempotent upserts)
- Batched upserts (default: 100 vectors per batch)
- Flexible deletion: by IDs, by metadata filter, or entire namespace
- Dimension validation (prevents index/provider mismatches)

**Operations**:
- `upsert_vectors()` - Batch upsert with retry
- `delete_by_ids()` - Delete specific vectors
- `delete_by_filter()` - Delete by metadata (e.g., `doc_id`)
- `delete_namespace()` - Delete all vectors in namespace
- `query()` - Semantic search
- `get_index_stats()` - Index statistics

### 3. **Indexing Service** (`app/services/indexing_service.py`)

**Orchestration**:
- Loads chunks from database
- Generates embeddings via provider
- Builds vector metadata: `{doc_id, chunk_id, page, file, upload_id, hash, created_at}`
- Upserts to Pinecone with deterministic IDs
- Updates `chunk.embedding_id` in database

**Methods**:
- `index_document()` - Index all chunks for a document
- `reindex_document()` - Force reindexing (even if already indexed)
- `delete_document_vectors()` - Remove vectors for a document
- `delete_upload_vectors()` - Remove entire upload namespace
- `get_indexing_stats()` - Get indexing progress

### 4. **Pipeline Integration**

**Automatic Background Indexing**:
- After Phase 2 saves chunks, FastAPI `BackgroundTasks` schedules embedding generation
- Non-blocking: API returns immediately, indexing happens asynchronously
- Logs progress and errors

**Deletion Propagation**:
- Deleting a document also deletes its vectors from Pinecone
- Deleting an upload batch deletes the entire namespace

### 5. **New API Endpoints** (`app/routers/upload.py`)

**POST `/v1/documents/{id}/embed`**:
- Force reindex a document
- Returns 202 Accepted (background task)

**DELETE `/v1/documents/{id}/vectors`**:
- Delete vectors from Pinecone (keeps DB records)
- Returns 204 No Content

**GET `/v1/documents/{id}/indexing-status`**:
- Get indexing statistics
- Returns: `{total_chunks, indexed_chunks, pending_chunks, completion_percentage}`

---

## 📦 Files Created

```
app/services/embeddings/
├── __init__.py
├── base.py                    # EmbeddingProvider interface
├── openai_provider.py         # OpenAI implementation
└── vertex_provider.py         # Vertex AI stub

app/services/vectorstore/
├── __init__.py
└── pinecone_store.py          # Pinecone wrapper

app/services/
└── indexing_service.py        # Indexing orchestrator

tests/
├── test_embeddings.py         # Unit tests for providers
├── test_pinecone_store.py     # Unit tests for Pinecone
└── test_indexing_integration.py  # Integration tests with fakes
```

## 📝 Files Modified

- `app/config.py` - Added Phase 3 settings
- `app/services/ingestion_service.py` - Added vector deletion on doc/upload delete
- `app/routers/upload.py` - Added background indexing and new endpoints
- `docker-compose.yml` - Added Phase 3 environment variables

---

## ⚙️ Configuration

### Environment Variables

```bash
# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=ragingestion
PINECONE_DIMENSION=3072              # 3072 for text-embedding-3-large, 1536 for -small
PINECONE_METRIC=cosine
PINECONE_CLOUD=aws                   # aws, gcp, or azure
PINECONE_REGION=us-east-1

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-large  # or text-embedding-3-small

# Provider Selection
EMBEDDING_PROVIDER=openai            # openai or vertex

# Embedding Configuration
EMBED_BATCH_SIZE=64                  # Texts per embedding API call
UPSERT_BATCH_SIZE=100                # Vectors per Pinecone upsert
INDEX_CONCURRENCY=2                  # Concurrent indexing tasks
EMBED_RETRY_MAX=5                    # Max retry attempts
EMBED_RETRY_DELAY=1.0                # Initial retry delay (seconds)
```

### Dimension Matching

**Critical**: `PINECONE_DIMENSION` must match your embedding model:

| Model | Dimension |
|-------|-----------|
| `text-embedding-3-large` | 3072 |
| `text-embedding-3-small` | 1536 |
| `text-embedding-ada-002` | 1536 |

Mismatch will cause startup error with actionable message.

---

## 🚀 Usage

### 1. **Automatic Indexing** (Default)

Upload documents normally - indexing happens automatically:

```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@document.pdf"
```

Response includes document ID. Indexing starts in background.

### 2. **Check Indexing Status**

```bash
curl "http://localhost:8000/v1/documents/{document_id}/indexing-status"
```

Response:
```json
{
  "document_id": "uuid",
  "total_chunks": 10,
  "indexed_chunks": 8,
  "pending_chunks": 2,
  "completion_percentage": 80.0
}
```

### 3. **Force Reindex**

```bash
curl -X POST "http://localhost:8000/v1/documents/{document_id}/embed"
```

Useful for:
- Switching embedding models
- Fixing corrupted embeddings
- Testing

### 4. **Delete Vectors**

```bash
curl -X DELETE "http://localhost:8000/v1/documents/{document_id}/vectors"
```

Removes vectors from Pinecone but keeps document and chunks in database.

---

## 🔒 Error Handling & Reliability

### Retry Logic

**OpenAI Embeddings**:
- Exponential backoff on 429 (rate limit) and 5xx errors
- Max 5 attempts (configurable via `EMBED_RETRY_MAX`)
- Jitter to avoid thundering herd

**Pinecone Upserts**:
- Exponential backoff on transient errors
- Max 5 attempts
- Automatic batching to avoid payload limits

### Idempotency

- Vector IDs are deterministic: `chunk:{chunk_id}`
- Safe to re-run indexing - upserts overwrite existing vectors
- `chunk.embedding_id` tracks indexing state

### Dimension Validation

On startup, validates:
1. Provider dimension matches config
2. Existing index dimension matches provider
3. Fails fast with actionable error message if mismatch

### Partial Failures

- Background indexing logs errors but doesn't crash app
- Failed documents can be reindexed via `/embed` endpoint
- Deletion failures are logged but don't block DB deletion

---

## 🧪 Testing

### Unit Tests

```bash
# Test embedding providers
pytest tests/test_embeddings.py -v

# Test Pinecone store
pytest tests/test_pinecone_store.py -v
```

**Coverage**:
- Provider initialization and configuration
- Batching logic
- Retry behavior (mocked)
- Text truncation and token counting
- Dimension validation
- Pinecone operations (mocked)

### Integration Tests

```bash
# Test full indexing pipeline with fakes
pytest tests/test_indexing_integration.py -v
```

**Coverage**:
- End-to-end: chunks → embeddings → Pinecone → DB update
- Skip already-indexed chunks
- Force reindexing
- Vector deletion
- Metadata population
- Error scenarios

**No External Calls**: Uses `FakeEmbeddingProvider` and `FakePineconeStore`

### Manual Testing (with Real APIs)

1. Set API keys in `.env`:
   ```bash
   PINECONE_API_KEY=your-real-key
   OPENAI_API_KEY=your-real-key
   ```

2. Start services:
   ```bash
   docker-compose up -d
   ```

3. Upload a small PDF:
   ```bash
   curl -X POST "http://localhost:8000/v1/documents/upload" \
     -F "files=@test.pdf"
   ```

4. Check Pinecone dashboard:
   - Index: `ragingestion`
   - Namespace: `upload:{upload_id}`
   - Vectors: One per chunk

---

## 📊 Performance

### Benchmarks (Approximate)

| Operation | Time | Notes |
|-----------|------|-------|
| Embed 100 chunks | ~2-3s | OpenAI API latency |
| Upsert 100 vectors | ~0.5s | Pinecone serverless |
| Full document (10 chunks) | ~3-5s | Background, non-blocking |

### Optimization

- **Batching**: Reduces API calls (64 texts/batch, 100 vectors/batch)
- **Concurrency**: Limited to avoid rate limits (default: 2)
- **Background Tasks**: API returns immediately, indexing is async
- **Namespace Deletion**: Faster than deleting by IDs

---

## 🔄 Upgrade Path

### From Phase 2

1. **Update environment variables** (see Configuration above)
2. **Rebuild Docker image**:
   ```bash
   docker-compose down
   docker-compose build app
   docker-compose up -d
   ```
3. **Reindex existing documents** (optional):
   ```bash
   # Get all document IDs
   curl "http://localhost:8000/v1/documents?limit=100"
   
   # Reindex each
   curl -X POST "http://localhost:8000/v1/documents/{id}/embed"
   ```

### No Database Migration Required

Phase 3 uses existing `chunks.embedding_id` column (already in schema from Phase 1).

---

## 🐛 Troubleshooting

### "Dimension mismatch" Error

**Symptom**: Startup fails with dimension mismatch message.

**Fix**:
1. Check `OPENAI_EMBEDDING_MODEL` and `PINECONE_DIMENSION` match
2. Or delete existing index and let it recreate
3. Or use different `PINECONE_INDEX_NAME`

### "OpenAI API key is required"

**Symptom**: Startup or indexing fails.

**Fix**: Set `OPENAI_API_KEY` in `.env` or docker-compose environment.

### "Pinecone API key is required"

**Symptom**: Startup or indexing fails.

**Fix**: Set `PINECONE_API_KEY` in `.env` or docker-compose environment.

### Indexing Stuck at 0%

**Symptom**: `indexing-status` shows 0% completion.

**Possible Causes**:
1. Background task failed (check logs: `docker-compose logs app`)
2. API keys invalid
3. Rate limit exceeded

**Fix**:
1. Check logs for errors
2. Verify API keys
3. Manually trigger reindex: `POST /v1/documents/{id}/embed`

### Rate Limit Errors

**Symptom**: Logs show 429 errors.

**Fix**:
1. Reduce `EMBED_BATCH_SIZE`
2. Reduce `INDEX_CONCURRENCY`
3. Add delay between uploads
4. Upgrade OpenAI tier

---

## 📈 Next Steps (Phase 4)

Phase 3 provides the foundation for semantic search. Phase 4 will add:

1. **Query Endpoint**: `/v1/query` - Ask questions about documents
2. **Retrieval Service**: Semantic search in Pinecone
3. **LLM Integration**: Generate answers using retrieved context
4. **Hybrid Search**: Combine vector and keyword search
5. **Reranking**: Improve result relevance

---

## ✅ Success Criteria

- [x] Embedding provider interface with OpenAI implementation
- [x] Pinecone store with index management and CRUD operations
- [x] Indexing service orchestrating chunk → embedding → vector flow
- [x] Background indexing integrated into upload pipeline
- [x] Vector deletion on document/upload removal
- [x] Reindex and purge endpoints
- [x] Comprehensive unit and integration tests
- [x] Docker environment variables configured
- [x] Documentation complete

**Phase 3 is production-ready!** 🎉

---

## 📚 API Reference

### Background Indexing

Triggered automatically on document upload. No action required.

### Manual Endpoints

**POST `/v1/documents/{document_id}/embed`**
- **Description**: Force reindex document embeddings
- **Status**: 202 Accepted
- **Response**:
  ```json
  {
    "message": "Document reindexing scheduled",
    "document_id": "uuid",
    "status": "processing"
  }
  ```

**DELETE `/v1/documents/{document_id}/vectors`**
- **Description**: Delete document vectors from Pinecone
- **Status**: 204 No Content

**GET `/v1/documents/{document_id}/indexing-status`**
- **Description**: Get indexing statistics
- **Status**: 200 OK
- **Response**:
  ```json
  {
    "document_id": "uuid",
    "total_chunks": 10,
    "indexed_chunks": 8,
    "pending_chunks": 2,
    "completion_percentage": 80.0
  }
  ```

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                                                              │
│  ┌────────────────┐                                         │
│  │ Upload Router  │                                         │
│  │  (Phase 2+3)   │                                         │
│  └────────┬───────┘                                         │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────┐      ┌──────────────────┐             │
│  │   Ingestion    │──────│  Background      │             │
│  │    Service     │      │  Tasks Queue     │             │
│  │   (Phase 2)    │      └────────┬─────────┘             │
│  └────────┬───────┘               │                        │
│           │                        │                        │
│           ▼                        ▼                        │
│  ┌────────────────┐      ┌──────────────────┐             │
│  │   Database     │      │   Indexing       │             │
│  │  (chunks)      │◄─────│   Service        │             │
│  └────────────────┘      │  (Phase 3)       │             │
│                           └────────┬─────────┘             │
│                                    │                        │
│                           ┌────────┴─────────┐             │
│                           │                  │             │
│                           ▼                  ▼             │
│                  ┌─────────────────┐  ┌──────────────┐    │
│                  │   Embedding     │  │  Pinecone    │    │
│                  │   Provider      │  │   Store      │    │
│                  │  (OpenAI API)   │  │  (Wrapper)   │    │
│                  └─────────────────┘  └──────┬───────┘    │
└──────────────────────────────────────────────┼────────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │   Pinecone      │
                                       │  Vector DB      │
                                       │  (Cloud)        │
                                       └─────────────────┘
```

---

**Phase 3 Complete** ✅  
**Ready for Phase 4: Query & Retrieval** 🚀

