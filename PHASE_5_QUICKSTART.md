# Phase 5 Quick Start Guide

## 🚀 Getting Started with Phase 5 Features

This guide shows you how to use the new Phase 5 features: rate limiting, enhanced errors, pagination, and more.

---

## Prerequisites

1. **Redis** (required for rate limiting)
2. **Existing Phase 0-4 setup** (database, Pinecone, API keys)

---

## 1️⃣ Start Redis

### Using Docker:
```bash
docker run -d -p 6379:6379 --name rag-redis redis:7-alpine
```

### Check Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

---

## 2️⃣ Configure Rate Limiting

Add to your `.env` file:

```bash
# Rate Limiting (Phase 5)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE_URL="redis://localhost:6379/0"
RATE_LIMIT_UPLOAD="10/hour"
RATE_LIMIT_QUERY="20/minute"
RATE_LIMIT_READ="100/minute"
RATE_LIMIT_DELETE="20/minute"
RATE_LIMIT_HEALTH="300/minute"
RATE_LIMIT_METRICS="30/minute"
```

---

## 3️⃣ Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 4️⃣ Test Phase 5 Features

### A. Health Check with Service Status

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-27T10:30:00Z",
  "service": "RAG Pipeline",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "pinecone": "healthy"
  }
}
```

### B. System Metrics

```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "timestamp": "2025-10-27T10:30:00Z",
  "totals": {
    "documents": 150,
    "uploads": 25,
    "queries": 89
  },
  "recent_activity": {
    "documents_last_hour": 5,
    "queries_last_hour": 12
  },
  "document_status": {
    "processing": 2,
    "completed": 145,
    "failed": 3
  },
  "performance": {
    "average_query_latency_ms": 1234.56
  }
}
```

### C. List Uploads with Pagination

```bash
# Page 1
curl "http://localhost:8000/v1/documents/uploads?page=1&limit=10"

# Page 2
curl "http://localhost:8000/v1/documents/uploads?page=2&limit=10"
```

**Response:**
```json
{
  "items": [
    {
      "id": "123e4567-...",
      "upload_batch_id": "abc123",
      "status": "completed",
      "total_documents": 5,
      "successful_documents": 5,
      "failed_documents": 0,
      "created_at": "2025-10-27T10:00:00Z",
      "completed_at": "2025-10-27T10:05:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  },
  "success": true
}
```

### D. Test Rate Limiting

Try making more than 20 queries in a minute:

```bash
# This script will trigger rate limiting
for i in {1..25}; do
  curl -X POST "http://localhost:8000/v1/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "test query"}' && echo
done
```

**After 20 requests, you'll get:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "endpoint": "/v1/query",
      "limit": "20 per minute",
      "suggestion": "Please wait before making more requests"
    },
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "retry_after": 60,
  "limit": "20 per minute",
  "success": false
}
```

### E. Enhanced Error Responses

Try uploading an invalid file:

```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@invalid.exe"
```

**Response (enhanced error):**
```json
{
  "error": {
    "code": "FILE_VALIDATION_ERROR",
    "message": "Invalid file type",
    "details": {
      "filename": "invalid.exe",
      "allowed_types": [".pdf", ".docx", ".txt", ".md"],
      "suggestion": "Please upload only PDF, DOCX, TXT, or MD files"
    },
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "success": false
}
```

### F. Security Headers

Check response headers:

```bash
curl -I http://localhost:8000/health
```

**You'll see:**
```
HTTP/1.1 200 OK
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
X-API-Version: 1.0.0
```

---

## 5️⃣ Interactive API Documentation

### Swagger UI
Visit: **http://localhost:8000/docs**

Features:
- Try out endpoints directly
- See request/response schemas
- View rate limits
- Copy code examples

### ReDoc
Visit: **http://localhost:8000/redoc**

Features:
- Clean, readable documentation
- Searchable
- Downloadable OpenAPI spec

---

## 6️⃣ Test Complete Workflow

### Full workflow with Phase 5 features:

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Upload documents (rate limited: 10/hour)
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"

# 3. List uploads with pagination
curl "http://localhost:8000/v1/documents/uploads?page=1&limit=10"

# 4. Query documents (rate limited: 20/minute)
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main topics?"
  }'

# 5. Get query history with pagination
curl "http://localhost:8000/v1/queries?skip=0&limit=10"

# 6. Check metrics
curl http://localhost:8000/metrics
```

---

## 🔧 Troubleshooting

### Redis Connection Error

**Error:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Fix:**
```bash
# Make sure Redis is running
docker ps | grep redis

# If not running, start it
docker run -d -p 6379:6379 --name rag-redis redis:7-alpine

# Test connection
redis-cli ping
```

### Rate Limiting Not Working

**Check:**
1. Redis is running and accessible
2. `RATE_LIMIT_ENABLED=true` in `.env`
3. `RATE_LIMIT_STORAGE_URL` points to correct Redis instance

**Disable rate limiting (for testing):**
```bash
# In .env
RATE_LIMIT_ENABLED=false
```

### Rate Limit Too Strict

**Adjust limits in `.env`:**
```bash
# Increase query limit to 50/minute
RATE_LIMIT_QUERY="50/minute"

# Increase upload limit to 20/hour
RATE_LIMIT_UPLOAD="20/hour"
```

---

## 📊 Rate Limit Reference

| Endpoint Type | Default Limit | Adjust Via |
|--------------|---------------|------------|
| Upload | 10/hour | `RATE_LIMIT_UPLOAD` |
| Query | 20/minute | `RATE_LIMIT_QUERY` |
| Read (GET) | 100/minute | `RATE_LIMIT_READ` |
| Delete | 20/minute | `RATE_LIMIT_DELETE` |
| Health | 300/minute | `RATE_LIMIT_HEALTH` |
| Metrics | 30/minute | `RATE_LIMIT_METRICS` |

---

## 🎯 Testing Checklist

- [ ] Redis is running
- [ ] Health endpoint returns service status
- [ ] Metrics endpoint returns statistics
- [ ] Rate limiting triggers after limit
- [ ] Error responses are structured
- [ ] Pagination works on list endpoints
- [ ] Security headers are present
- [ ] Swagger UI is accessible
- [ ] Upload endpoint has rate limit
- [ ] Query endpoint has rate limit

---

## 📚 Next Steps

1. **Explore API Documentation**: http://localhost:8000/docs
2. **Review Error Handling**: Try invalid requests to see error responses
3. **Test Pagination**: List documents/uploads/queries with different page sizes
4. **Monitor Metrics**: Track system performance via `/metrics`
5. **Check Rate Limits**: Understand your API usage patterns

---

## 💡 Pro Tips

### 1. Monitor Rate Limit Headers

Responses include rate limit information in headers:
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1635350400
```

### 2. Use Pagination Efficiently

Always paginate large lists:
```bash
# Small page size for quick responses
curl "http://localhost:8000/v1/documents?page=1&limit=5"

# Large page size for bulk operations
curl "http://localhost:8000/v1/documents?page=1&limit=50"
```

### 3. Handle Rate Limit Errors

In your client code:
```python
import requests
import time

def query_with_retry(query, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(
            "http://localhost:8000/v1/query",
            json={"query": query}
        )
        
        if response.status_code == 429:
            # Rate limited
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        
        return response.json()
    
    raise Exception("Max retries exceeded")
```

### 4. Use Health Check for Monitoring

Set up a monitoring tool to ping `/health` every minute:
```bash
# Simple monitoring script
while true; do
  STATUS=$(curl -s http://localhost:8000/health | jq -r .status)
  echo "$(date): $STATUS"
  sleep 60
done
```

---

## 🎉 You're Ready!

You now have a production-ready RAG API with:
- ✅ Rate limiting
- ✅ Enhanced error handling
- ✅ Pagination
- ✅ Security headers
- ✅ Health checks
- ✅ Metrics
- ✅ Professional API docs

Happy coding! 🚀

