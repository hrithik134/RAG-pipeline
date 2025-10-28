# README Update for Phase 5

Add this section to README.md after the Architecture section:

---

## 🆕 Phase 5 Features (Production-Ready API)

### Rate Limiting 🛡️
Protect your API from abuse with built-in rate limiting:
- **10 uploads/hour** - Prevent resource exhaustion
- **20 queries/minute** - Balance throughput and protection
- **100 reads/minute** - Generous data retrieval limits
- **Redis-backed** - Distributed rate limiting support

### Enhanced Error Handling ❌
Get helpful, structured error responses:
```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds 50MB limit",
    "details": {
      "file_size": "75MB",
      "max_size": "50MB",
      "suggestion": "Please compress or split the file"
    },
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "123e4567-..."
  }
}
```

### Pagination 📄
Handle large datasets efficiently:
- Automatic pagination on all list endpoints
- Navigate with `page` and `limit` parameters
- Get pagination metadata (total, pages, has_next, etc.)

### Security Headers 🔒
Production-grade security out of the box:
- X-Content-Type-Options (MIME sniffing protection)
- X-Frame-Options (clickjacking protection)
- X-XSS-Protection (browser XSS protection)
- Content-Security-Policy
- Strict-Transport-Security (HTTPS enforcement)

### Health Checks & Metrics 📊
Monitor your API's health:

**Health Check** - `GET /health`
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "pinecone": "healthy"
  }
}
```

**System Metrics** - `GET /metrics`
```json
{
  "totals": {
    "documents": 150,
    "queries": 89
  },
  "performance": {
    "average_query_latency_ms": 1234.56
  }
}
```

### Interactive API Documentation 📚
Explore and test the API:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- Complete endpoint documentation
- Try-it-out functionality
- Code examples

---

## 🚦 Quick Start (Updated for Phase 5)

### 1. Setup Redis (Required for Rate Limiting)

```bash
# Start Redis using Docker
docker run -d -p 6379:6379 --name rag-redis redis:7-alpine

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Phase 5: Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE_URL="redis://localhost:6379/0"
RATE_LIMIT_UPLOAD="10/hour"
RATE_LIMIT_QUERY="20/minute"
RATE_LIMIT_READ="100/minute"
```

### 3. Start the Application

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or run locally
uvicorn app.main:app --reload
```

### 4. Test Phase 5 Features

```bash
# Check health with service status
curl http://localhost:8000/health

# View system metrics
curl http://localhost:8000/metrics

# List uploads with pagination
curl "http://localhost:8000/v1/documents/uploads?page=1&limit=10"

# Access interactive API documentation
# Open browser: http://localhost:8000/docs
```

---

## 📖 Phase 5 Documentation

Comprehensive guides for Phase 5 features:

- **[PHASE_5_COMPLETE.md](PHASE_5_COMPLETE.md)** - Full implementation details
- **[PHASE_5_QUICKSTART.md](PHASE_5_QUICKSTART.md)** - Quick start guide
- **[PHASE_5_SUMMARY.md](PHASE_5_SUMMARY.md)** - Implementation summary

---

## 🔧 Phase 5 Configuration

### Rate Limiting Options

```bash
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=true

# Redis connection for distributed rate limiting
RATE_LIMIT_STORAGE_URL="redis://localhost:6379/0"

# Customize limits per endpoint type
RATE_LIMIT_UPLOAD="10/hour"      # Document uploads
RATE_LIMIT_QUERY="20/minute"     # Query requests
RATE_LIMIT_READ="100/minute"     # Read operations
RATE_LIMIT_DELETE="20/minute"    # Delete operations
RATE_LIMIT_HEALTH="300/minute"   # Health checks
RATE_LIMIT_METRICS="30/minute"   # Metrics endpoint
```

### Adjust for Your Needs

**High-Traffic Application:**
```bash
RATE_LIMIT_QUERY="100/minute"
RATE_LIMIT_READ="500/minute"
```

**Development/Testing:**
```bash
RATE_LIMIT_ENABLED=false  # Disable rate limiting
```

---

## 📊 Updated API Endpoints

### System Endpoints (Phase 5)
| Method | Endpoint | Rate Limit | Description |
|--------|----------|------------|-------------|
| GET | `/health` | 300/min | Health check with service status ✨ |
| GET | `/metrics` | 30/min | System metrics and statistics ✨ |

### Document Management
| Method | Endpoint | Rate Limit | Description |
|--------|----------|------------|-------------|
| POST | `/v1/documents/upload` | 10/hour | Upload documents |
| GET | `/v1/documents` | 100/min | List documents (paginated) ✨ |
| GET | `/v1/documents/{id}` | 100/min | Get document details |

### Upload Management (Enhanced Phase 5)
| Method | Endpoint | Rate Limit | Description |
|--------|----------|------------|-------------|
| GET | `/v1/documents/uploads` | 100/min | List uploads (paginated) ✨ NEW |
| GET | `/v1/documents/uploads/{id}` | 100/min | Get upload status |

### Query System
| Method | Endpoint | Rate Limit | Description |
|--------|----------|------------|-------------|
| POST | `/v1/query` | 20/min | Ask questions |
| GET | `/v1/queries` | 100/min | Query history (paginated) ✨ |

✨ = New or enhanced in Phase 5

---

## 🧪 Testing Phase 5 Features

### Run the Phase 5 Test Script

```powershell
# Windows PowerShell
.\test_phase5.ps1
```

```bash
# Linux/Mac (convert to bash or use Python)
python test_phase5.py  # If you create a Python version
```

### Manual Testing

**Test Rate Limiting:**
```bash
# Make 25 requests to trigger rate limit (limit is 20/minute)
for i in {1..25}; do
  curl -X POST "http://localhost:8000/v1/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}' && echo
done
```

**Test Pagination:**
```bash
# Get page 1
curl "http://localhost:8000/v1/documents/uploads?page=1&limit=5"

# Get page 2
curl "http://localhost:8000/v1/documents/uploads?page=2&limit=5"
```

**Test Enhanced Errors:**
```bash
# Try an invalid query (too short)
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hi"}'
```

---

## 🐛 Troubleshooting Phase 5

### Redis Connection Error

**Error**: `redis.exceptions.ConnectionError`

**Solution**:
```bash
# Make sure Redis is running
docker ps | grep redis

# Start Redis if not running
docker run -d -p 6379:6379 --name rag-redis redis:7-alpine

# Test connection
redis-cli ping
```

### Rate Limiting Not Working

**Check**:
1. Redis is running and accessible
2. `RATE_LIMIT_ENABLED=true` in `.env`
3. `RATE_LIMIT_STORAGE_URL` points to correct Redis

**Temporary Disable**:
```bash
# In .env
RATE_LIMIT_ENABLED=false
```

### Health Check Showing Degraded

**Check** each service individually:
```bash
# Test database
psql $DATABASE_URL -c "SELECT 1"

# Test Redis
redis-cli ping

# Test Pinecone
curl -X GET "https://api.pinecone.io/indexes" \
  -H "Api-Key: $PINECONE_API_KEY"
```

---

## 📈 Performance Improvements (Phase 5)

- **Rate Limiting**: Protects against abuse, improves stability
- **Pagination**: Reduces response size, faster queries
- **Error Caching**: Prevents repeated failed requests
- **Health Checks**: Proactive issue detection
- **Metrics**: Performance monitoring and optimization

---

## 🔒 Security Enhancements (Phase 5)

- **Rate Limiting**: DDoS protection
- **Input Validation**: Injection prevention
- **Security Headers**: OWASP best practices
- **Error Sanitization**: No sensitive data leakage
- **Request Tracking**: Unique IDs for audit trails

---

## 🎯 What's Next?

After Phase 5, potential future enhancements:

1. **Authentication** - API keys, JWT tokens
2. **Authorization** - Role-based access control
3. **Caching** - Query result caching
4. **Webhooks** - Event notifications
5. **Analytics** - Advanced usage analytics
6. **Multi-tenancy** - Tenant isolation

---

## 📚 Additional Resources

### Phase 5 Specific:
- [Phase 5 Complete Guide](PHASE_5_COMPLETE.md)
- [Phase 5 Quick Start](PHASE_5_QUICKSTART.md)
- [Phase 5 Summary](PHASE_5_SUMMARY.md)

### API Documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Spec: http://localhost:8000/openapi.json

### Previous Phases:
- [Phase 0-1: Document Upload](PHASE_2_COMPLETE.md)
- [Phase 2-3: Processing](PHASE_3_COMPLETE.md)
- [Phase 4: RAG System](PHASE_4_PLAN.md)

---

**Status**: ✅ Phase 5 Complete - Production Ready!

