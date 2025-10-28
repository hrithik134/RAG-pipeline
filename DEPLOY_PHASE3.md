# Phase 3 Deployment Guide

## 🚀 Deploy Phase 3 to Production

This guide covers deploying Phase 3 (Embeddings & Pinecone Indexing) to production environments.

---

## Prerequisites

- Docker & Docker Compose installed
- OpenAI API key with billing enabled
- Pinecone account with API key
- Phase 2 already deployed and working

---

## Step 1: Prepare Environment Variables

Create or update your `.env` file with Phase 3 variables:

```bash
# Required - Get these from your providers
OPENAI_API_KEY=sk-...your-key...
PINECONE_API_KEY=...your-key...

# Embedding Configuration
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
PINECONE_INDEX_NAME=ragingestion
PINECONE_DIMENSION=3072
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# Provider Selection
EMBEDDING_PROVIDER=openai

# Performance Tuning
EMBED_BATCH_SIZE=64
UPSERT_BATCH_SIZE=100
INDEX_CONCURRENCY=2
EMBED_RETRY_MAX=5
EMBED_RETRY_DELAY=1.0
```

**Important Dimension Matching**:
- `text-embedding-3-large` → `PINECONE_DIMENSION=3072`
- `text-embedding-3-small` → `PINECONE_DIMENSION=1536`

---

## Step 2: Update Docker Compose

Your `docker-compose.yml` should already have Phase 3 variables. Verify:

```bash
grep -A 20 "# Pinecone Configuration" docker-compose.yml
```

Should show all Phase 3 environment variables.

---

## Step 3: Build and Deploy

### Option A: Zero-Downtime Deployment

```bash
# Build new image
docker-compose build app

# Stop old container
docker-compose stop app

# Start new container
docker-compose up -d app

# Verify
docker-compose logs app --tail 50
```

### Option B: Full Restart

```bash
# Stop all services
docker-compose down

# Rebuild
docker-compose build app

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

---

## Step 4: Verify Deployment

### 1. Check Health

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production"
}
```

### 2. Check Logs

```bash
docker-compose logs app --tail 100 --follow
```

Look for:
- `Initialized OpenAI embedding provider`
- `Initialized Pinecone store`
- No dimension mismatch errors

### 3. Test Upload & Indexing

```bash
# Upload a test document
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@test.pdf"

# Note the document ID from response

# Check indexing status (wait 10-30 seconds)
curl "http://localhost:8000/v1/documents/{doc-id}/indexing-status"
```

Expected:
```json
{
  "document_id": "...",
  "total_chunks": 10,
  "indexed_chunks": 10,
  "pending_chunks": 0,
  "completion_percentage": 100.0
}
```

### 4. Verify in Pinecone Dashboard

1. Go to [Pinecone Console](https://app.pinecone.io/)
2. Select your index (`ragingestion`)
3. Check vector count > 0
4. Verify namespace exists: `upload:{upload-id}`

---

## Step 5: Reindex Existing Documents (Optional)

If you have documents from Phase 2, reindex them:

```bash
# Get all document IDs
curl "http://localhost:8000/v1/documents?limit=100" | jq -r '.[] | .id'

# Reindex each (replace {doc-id})
curl -X POST "http://localhost:8000/v1/documents/{doc-id}/embed"
```

Or use this script:

```bash
#!/bin/bash
# reindex_all.sh

API_URL="http://localhost:8000"

# Get all document IDs
DOC_IDS=$(curl -s "$API_URL/v1/documents?limit=1000" | jq -r '.[].id')

# Reindex each
for doc_id in $DOC_IDS; do
  echo "Reindexing $doc_id..."
  curl -X POST "$API_URL/v1/documents/$doc_id/embed"
  sleep 1  # Rate limit
done

echo "Reindexing complete!"
```

---

## Production Configuration

### Performance Tuning

For high-volume production:

```bash
# Increase concurrency
INDEX_CONCURRENCY=5

# Larger batches (if API tier allows)
EMBED_BATCH_SIZE=128
UPSERT_BATCH_SIZE=200

# More aggressive retries
EMBED_RETRY_MAX=10
```

### Cost Optimization

For cost-sensitive deployments:

```bash
# Use smaller model
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
PINECONE_DIMENSION=1536

# Reduce concurrency
INDEX_CONCURRENCY=1

# Smaller batches
EMBED_BATCH_SIZE=32
```

### Rate Limit Management

If hitting rate limits:

```bash
# Reduce batch size
EMBED_BATCH_SIZE=32

# Reduce concurrency
INDEX_CONCURRENCY=1

# Increase retry delay
EMBED_RETRY_DELAY=2.0
```

---

## Monitoring

### Key Metrics to Monitor

1. **Indexing Success Rate**
   ```bash
   docker-compose logs app | grep "Successfully indexed" | wc -l
   ```

2. **Indexing Failures**
   ```bash
   docker-compose logs app | grep "Background indexing failed"
   ```

3. **Rate Limit Errors**
   ```bash
   docker-compose logs app | grep "Rate limit hit"
   ```

4. **Average Indexing Time**
   ```bash
   docker-compose logs app | grep "Background indexing completed"
   ```

### Pinecone Metrics

Check in Pinecone dashboard:
- Total vector count
- Namespace count
- Query latency
- Upsert latency

### OpenAI Usage

Check in OpenAI dashboard:
- API calls per day
- Token usage
- Cost per day

---

## Troubleshooting

### Issue: "Dimension mismatch" on startup

**Cause**: Existing index has different dimension than configured.

**Solution**:
1. Delete existing index in Pinecone dashboard
2. Restart app (will recreate index)
3. Or change `PINECONE_INDEX_NAME` to create new index

### Issue: Indexing stuck at 0%

**Cause**: Background task failed.

**Solution**:
```bash
# Check logs
docker-compose logs app | grep -i error

# Manually trigger reindex
curl -X POST "http://localhost:8000/v1/documents/{doc-id}/embed"
```

### Issue: Rate limit errors

**Cause**: Too many API calls.

**Solution**:
```bash
# Reduce concurrency
INDEX_CONCURRENCY=1

# Reduce batch size
EMBED_BATCH_SIZE=32

# Restart
docker-compose restart app
```

### Issue: High costs

**Cause**: Large embedding model or high volume.

**Solution**:
```bash
# Switch to smaller model
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
PINECONE_DIMENSION=1536

# Delete old index (different dimension)
# Restart and reindex
```

---

## Rollback Plan

If Phase 3 has issues, rollback to Phase 2:

```bash
# Stop services
docker-compose down

# Checkout Phase 2 code
git checkout phase-2

# Rebuild
docker-compose build app

# Start
docker-compose up -d
```

**Note**: Existing documents will still work. Embeddings will just not be generated for new uploads.

---

## Health Checks

Add to your monitoring:

```bash
# API health
curl http://localhost:8000/health

# Indexing status for recent document
curl "http://localhost:8000/v1/documents/{recent-doc-id}/indexing-status"

# Pinecone index stats (via API)
# Add endpoint in Phase 4
```

---

## Backup & Disaster Recovery

### Database Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U rag_user rag_db > backup.sql
```

### Pinecone Backup

Pinecone handles backups automatically. To recreate:

1. Export document IDs from database
2. Trigger reindex for all documents
3. Vectors will be recreated

### Recovery Steps

1. Restore database from backup
2. Restart services
3. Reindex all documents:
   ```bash
   ./reindex_all.sh
   ```

---

## Security Checklist

- [ ] API keys stored in environment variables (not in code)
- [ ] `.env` file not committed to git
- [ ] Docker secrets used in production (not plain env vars)
- [ ] HTTPS enabled (reverse proxy)
- [ ] Rate limiting enabled
- [ ] CORS configured correctly
- [ ] Logs don't contain API keys
- [ ] Error messages don't leak sensitive data

---

## Performance Benchmarks

Expected performance (approximate):

| Metric | Value |
|--------|-------|
| Embedding latency | 2-3s per 100 chunks |
| Upsert latency | 0.5s per 100 vectors |
| End-to-end indexing | 3-5s per 10-chunk doc |
| API response time | <100ms (non-blocking) |
| Throughput | ~20 docs/minute |

---

## Cost Estimation

### OpenAI Costs

| Model | Cost per 1M tokens | 10K docs (avg 10 chunks) |
|-------|-------------------|--------------------------|
| text-embedding-3-large | $0.13 | ~$1.30 |
| text-embedding-3-small | $0.02 | ~$0.20 |

### Pinecone Costs

Serverless pricing:
- Storage: $0.25 per GB/month
- Read: $2.00 per million requests
- Write: $2.00 per million requests

Typical usage (10K docs, 100K vectors):
- Storage: ~$0.50/month
- Writes: ~$0.20 (one-time)

---

## Post-Deployment Checklist

- [ ] Health check passing
- [ ] Test document uploaded and indexed successfully
- [ ] Pinecone dashboard shows vectors
- [ ] Logs show no errors
- [ ] Monitoring set up
- [ ] Alerts configured
- [ ] Team notified of deployment
- [ ] Documentation updated
- [ ] Rollback plan tested

---

## Next Steps

After successful Phase 3 deployment:

1. **Monitor for 24-48 hours**
   - Check logs regularly
   - Monitor costs
   - Watch for errors

2. **Optimize if needed**
   - Adjust batch sizes
   - Tune concurrency
   - Switch models if cost is high

3. **Plan Phase 4**
   - Query & Retrieval
   - LLM integration
   - Answer generation

---

## Support

If issues persist:

1. Check logs: `docker-compose logs app --tail 500`
2. Review documentation: `PHASE_3_COMPLETE.md`
3. Check troubleshooting: `PHASE_3_COMPLETE.md#troubleshooting`
4. Verify configuration: `docker-compose config`

---

**Deployment Guide Complete** ✅  
**Phase 3 Ready for Production** 🚀

