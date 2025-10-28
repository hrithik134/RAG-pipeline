# Phase 3 Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

- Docker & Docker Compose installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Pinecone API key ([Get one here](https://www.pinecone.io/))

---

## Step 1: Configure Environment

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-...your-key...
PINECONE_API_KEY=...your-key...

# Optional (defaults shown)
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
PINECONE_INDEX_NAME=ragingestion
PINECONE_DIMENSION=3072
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

**Important**: If using `text-embedding-3-small`, set `PINECONE_DIMENSION=1536`

---

## Step 2: Start Services

```bash
docker-compose down
docker-compose build app
docker-compose up -d
```

Wait ~30 seconds for services to start.

---

## Step 3: Verify Setup

```bash
# Check health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs
```

---

## Step 4: Upload & Index a Document

```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@your-document.pdf"
```

**Response**:
```json
{
  "id": "upload-uuid",
  "status": "completed",
  "documents": [
    {
      "id": "doc-uuid",
      "filename": "your-document.pdf",
      "status": "completed",
      "page_count": 5,
      ...
    }
  ]
}
```

**Note the document ID** - you'll need it for the next step.

---

## Step 5: Check Indexing Status

```bash
curl "http://localhost:8000/v1/documents/{doc-uuid}/indexing-status"
```

**Response**:
```json
{
  "document_id": "doc-uuid",
  "total_chunks": 10,
  "indexed_chunks": 10,
  "pending_chunks": 0,
  "completion_percentage": 100.0
}
```

---

## Step 6: Verify in Pinecone Dashboard

1. Go to [Pinecone Console](https://app.pinecone.io/)
2. Select your index (`ragingestion`)
3. Check the "Indexes" tab - you should see vectors
4. Namespace will be `upload:{upload-uuid}`

---

## 🎉 Success!

Your document is now:
- ✅ Uploaded and stored
- ✅ Extracted and chunked
- ✅ Embedded with OpenAI
- ✅ Indexed in Pinecone

**Ready for Phase 4: Query & Retrieval!**

---

## 🔧 Common Issues

### "Dimension mismatch" Error

**Problem**: `PINECONE_DIMENSION` doesn't match embedding model.

**Solution**:
- For `text-embedding-3-large`: `PINECONE_DIMENSION=3072`
- For `text-embedding-3-small`: `PINECONE_DIMENSION=1536`

### Indexing Stuck at 0%

**Problem**: Background task failed.

**Solution**:
```bash
# Check logs
docker-compose logs app | grep -i error

# Manually trigger reindex
curl -X POST "http://localhost:8000/v1/documents/{doc-uuid}/embed"
```

### Rate Limit Errors

**Problem**: Too many API calls.

**Solution**: Add to `.env`:
```bash
EMBED_BATCH_SIZE=32
INDEX_CONCURRENCY=1
```

---

## 📚 Next Steps

- **Test reindexing**: `POST /v1/documents/{id}/embed`
- **Delete vectors**: `DELETE /v1/documents/{id}/vectors`
- **Upload more documents**: Repeat Step 4
- **Read full docs**: See `PHASE_3_COMPLETE.md`

---

## 🆘 Need Help?

Check the logs:
```bash
docker-compose logs app --tail 100 --follow
```

Common log patterns:
- `Background indexing started` - Indexing in progress
- `Successfully indexed document` - Indexing complete
- `Rate limit hit` - Slow down API calls
- `Dimension mismatch` - Fix configuration

---

## 🧪 Test Commands

```bash
# Upload
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@test.pdf"

# Check status
curl "http://localhost:8000/v1/documents/{doc-id}/indexing-status"

# Reindex
curl -X POST "http://localhost:8000/v1/documents/{doc-id}/embed"

# Delete vectors
curl -X DELETE "http://localhost:8000/v1/documents/{doc-id}/vectors"

# List documents
curl "http://localhost:8000/v1/documents?limit=10"
```

---

**Phase 3 Quick Start Complete!** 🚀

