# Phase 5 Verification Checklist

Use this checklist to verify that Phase 5 has been correctly implemented and is working as expected.

---

## ✅ Pre-Deployment Checklist

### 1. Dependencies Installed
- [ ] All packages from `requirements.txt` installed
- [ ] Redis server available (local or Docker)
- [ ] PostgreSQL database running
- [ ] Pinecone account configured

### 2. Environment Configuration
- [ ] `.env` file created with all required variables
- [ ] `RATE_LIMIT_ENABLED=true` set
- [ ] `RATE_LIMIT_STORAGE_URL` points to Redis
- [ ] Rate limit values configured for your needs
- [ ] All API keys present (OpenAI/Google, Pinecone)

### 3. Services Running
- [ ] Redis running on port 6379
- [ ] PostgreSQL running on port 5432
- [ ] Pinecone index exists and is accessible

---

## ✅ Feature Verification

### Rate Limiting

#### Test Upload Rate Limit (10/hour)
```bash
# Should succeed for first 10 requests
for i in {1..10}; do
  curl -X POST "http://localhost:8000/v1/documents/upload" \
    -F "files=@test.pdf"
  echo "Request $i completed"
done

# 11th request should return 429
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@test.pdf"
```

- [ ] First 10 uploads succeed
- [ ] 11th upload returns 429 status
- [ ] Response includes `retry_after` field
- [ ] Response has proper error structure

#### Test Query Rate Limit (20/minute)
```bash
# Should trigger after 20 requests
for i in {1..25}; do
  curl -X POST "http://localhost:8000/v1/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}' \
    -w "\nStatus: %{http_code}\n"
done
```

- [ ] First 20 queries succeed
- [ ] 21st query returns 429 status
- [ ] Error message is clear and helpful
- [ ] `Retry-After` header present

#### Test Read Rate Limit (100/minute)
```bash
# Should trigger after 100 requests
for i in {1..105}; do
  curl "http://localhost:8000/health" -w "\nStatus: %{http_code}\n"
done
```

- [ ] First 100 requests succeed
- [ ] 101st request returns 429
- [ ] Rate limit resets after waiting

---

### Enhanced Error Handling

#### Test Validation Error
```bash
# Query too short (< 3 characters)
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hi"}'
```

- [ ] Returns 400 or 422 status
- [ ] Error has `code` field
- [ ] Error has `message` field
- [ ] Error has `details` field
- [ ] Error has `timestamp` field
- [ ] Error has `request_id` field

#### Test Rate Limit Error
```bash
# Make 25 requests quickly to trigger rate limit
for i in {1..25}; do
  curl -X POST "http://localhost:8000/v1/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "test query"}' \
    -w "\nStatus: %{http_code}\n"
done
```

- [ ] 429 status after exceeding limit
- [ ] Error structure includes `retry_after`
- [ ] Error structure includes `limit`
- [ ] Error code is "RATE_LIMIT_EXCEEDED"

#### Test Not Found Error
```bash
curl "http://localhost:8000/v1/documents/00000000-0000-0000-0000-000000000000"
```

- [ ] Returns 404 status
- [ ] Clear error message
- [ ] Proper error structure

---

### Pagination

#### Test Upload List Pagination
```bash
# Page 1
curl "http://localhost:8000/v1/documents/uploads?page=1&limit=5" | jq .

# Page 2
curl "http://localhost:8000/v1/documents/uploads?page=2&limit=5" | jq .
```

- [ ] Response has `items` array
- [ ] Response has `pagination` object
- [ ] `pagination.page` matches request
- [ ] `pagination.limit` matches request
- [ ] `pagination.total` shows total count
- [ ] `pagination.pages` calculated correctly
- [ ] `pagination.has_next` is accurate
- [ ] `pagination.has_prev` is accurate
- [ ] `pagination.next_page` and `prev_page` present

#### Test Document List Pagination
```bash
curl "http://localhost:8000/v1/documents?page=1&limit=10" | jq .
```

- [ ] Pagination works correctly
- [ ] Items returned match limit
- [ ] Total count is accurate

#### Test Query History Pagination
```bash
curl "http://localhost:8000/v1/queries?skip=0&limit=10" | jq .
```

- [ ] Pagination works correctly
- [ ] Skip/limit parameters work

#### Test Invalid Pagination
```bash
# Invalid page (< 1)
curl "http://localhost:8000/v1/documents/uploads?page=0&limit=10"

# Invalid limit (> 100)
curl "http://localhost:8000/v1/documents/uploads?page=1&limit=200"
```

- [ ] Returns 400 status for invalid page
- [ ] Returns 400 status for invalid limit
- [ ] Error messages are clear

---

### Security Headers

#### Test Security Headers Present
```bash
curl -I "http://localhost:8000/health"
```

Check for these headers:
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Content-Security-Policy: default-src 'self'`
- [ ] `X-API-Version: <version>`

#### Test HSTS (Production Only)
```bash
# Set APP_ENV=production and restart
curl -I "http://localhost:8000/health"
```

- [ ] `Strict-Transport-Security` header present in production
- [ ] Header NOT present in development

---

### Health Check

#### Test Basic Health
```bash
curl "http://localhost:8000/health" | jq .
```

- [ ] Returns 200 status
- [ ] `status` field present
- [ ] `timestamp` field present
- [ ] `service` field present
- [ ] `version` field present
- [ ] `environment` field present
- [ ] `services` object present

#### Test Service Status
- [ ] `services.database` shows status
- [ ] `services.redis` shows status (if enabled)
- [ ] `services.pinecone` shows status (if configured)
- [ ] Status is "healthy" when all services up
- [ ] Status is "degraded" when any service down

#### Test Unhealthy Scenario
```bash
# Stop Redis
docker stop rag-redis

# Check health
curl "http://localhost:8000/health" | jq .

# Start Redis
docker start rag-redis
```

- [ ] Health check detects Redis down
- [ ] Status changes to "degraded"
- [ ] Specific service shows "unhealthy"
- [ ] Health recovers when Redis back up

---

### Metrics Endpoint

#### Test Metrics Response
```bash
curl "http://localhost:8000/metrics" | jq .
```

- [ ] Returns 200 status
- [ ] `timestamp` field present
- [ ] `totals` object with counts
- [ ] `totals.documents` is a number
- [ ] `totals.uploads` is a number
- [ ] `totals.queries` is a number
- [ ] `recent_activity` object present
- [ ] `document_status` object present
- [ ] `performance` object present
- [ ] `average_query_latency_ms` is a number

#### Test Metrics Accuracy
- [ ] Document count matches database
- [ ] Upload count matches database
- [ ] Query count matches database
- [ ] Status counts add up correctly

---

### API Documentation

#### Test Swagger UI
```bash
# Open in browser
http://localhost:8000/docs
```

- [ ] Swagger UI loads without errors
- [ ] All endpoints are listed
- [ ] Endpoints organized by tags
- [ ] Each endpoint has description
- [ ] Request/response schemas visible
- [ ] "Try it out" functionality works
- [ ] Examples are helpful
- [ ] Rate limits are documented

#### Test ReDoc
```bash
# Open in browser
http://localhost:8000/redoc
```

- [ ] ReDoc loads without errors
- [ ] Documentation is readable
- [ ] Search functionality works
- [ ] All endpoints documented
- [ ] Schemas are expandable

#### Test OpenAPI Spec
```bash
curl "http://localhost:8000/openapi.json" | jq .
```

- [ ] Returns valid JSON
- [ ] OpenAPI version specified
- [ ] API info present (title, version)
- [ ] All paths listed
- [ ] Schemas defined
- [ ] Tags defined

---

### New Endpoints

#### Test List Uploads Endpoint
```bash
curl "http://localhost:8000/v1/documents/uploads?page=1&limit=10" | jq .
```

- [ ] Endpoint exists (not 404)
- [ ] Returns paginated response
- [ ] Items have correct structure
- [ ] Pagination metadata correct
- [ ] Ordered by creation date (newest first)
- [ ] Rate limit applied (100/minute)

---

## ✅ Integration Tests

### Full Workflow Test

#### 1. Upload Documents
```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@test1.pdf" \
  -F "files=@test2.pdf"
```

- [ ] Upload succeeds
- [ ] Returns upload_id
- [ ] Processing starts

#### 2. Check Upload Status
```bash
curl "http://localhost:8000/v1/documents/uploads/<upload_id>" | jq .
```

- [ ] Status endpoint works
- [ ] Shows processing progress
- [ ] Documents listed

#### 3. List All Uploads
```bash
curl "http://localhost:8000/v1/documents/uploads?page=1&limit=10" | jq .
```

- [ ] New upload appears in list
- [ ] Pagination works
- [ ] Data is accurate

#### 4. Query Documents
```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic?"}' | jq .
```

- [ ] Query succeeds
- [ ] Returns answer
- [ ] Includes citations
- [ ] Metadata present

#### 5. Check Query History
```bash
curl "http://localhost:8000/v1/queries?skip=0&limit=10" | jq .
```

- [ ] Recent query appears
- [ ] Pagination works
- [ ] Query details accurate

#### 6. Check Metrics
```bash
curl "http://localhost:8000/metrics" | jq .
```

- [ ] Counts updated
- [ ] Recent activity shows new items
- [ ] Performance metrics accurate

---

## ✅ Error Handling Tests

### Test Various Error Scenarios

#### File Too Large
- [ ] Returns appropriate error
- [ ] Error includes file size info
- [ ] Suggests solution

#### Invalid File Type
- [ ] Returns appropriate error
- [ ] Lists allowed types
- [ ] Helpful message

#### Too Many Files
- [ ] Returns appropriate error
- [ ] Shows max limit
- [ ] Clear message

#### Query Too Short
- [ ] Returns validation error
- [ ] Shows min length
- [ ] Clear message

#### Query Too Long
- [ ] Returns validation error
- [ ] Shows max length
- [ ] Clear message

#### Invalid UUID
- [ ] Returns 404 or 400
- [ ] Clear message
- [ ] Request ID included

---

## ✅ Performance Tests

### Response Time
- [ ] Health check < 500ms
- [ ] Metrics < 2s
- [ ] Document list < 2s
- [ ] Upload list < 2s
- [ ] Query < 5s (with embedding + LLM)

### Concurrency
```bash
# Test 10 concurrent requests
for i in {1..10}; do
  curl "http://localhost:8000/health" &
done
wait
```

- [ ] All requests succeed
- [ ] No timeouts
- [ ] No database locks

---

## ✅ Code Quality

### Linting
```bash
# Run linter (if configured)
ruff check app/
# or
pylint app/
```

- [ ] No linter errors
- [ ] No linter warnings (or acceptable)
- [ ] Code style consistent

### Type Checking
```bash
# Run type checker (if configured)
mypy app/
```

- [ ] No type errors
- [ ] All functions typed
- [ ] Return types specified

---

## ✅ Documentation

### Code Documentation
- [ ] All new functions have docstrings
- [ ] Complex logic has comments
- [ ] Type hints present
- [ ] Examples in docstrings

### User Documentation
- [ ] PHASE_5_COMPLETE.md exists
- [ ] PHASE_5_QUICKSTART.md exists
- [ ] PHASE_5_SUMMARY.md exists
- [ ] All guides are clear and complete
- [ ] Examples are accurate
- [ ] Troubleshooting section helpful

---

## ✅ Deployment Readiness

### Configuration
- [ ] All environment variables documented
- [ ] Default values sensible
- [ ] Production values different from dev
- [ ] Secrets not committed to git

### Dependencies
- [ ] requirements.txt up to date
- [ ] No unnecessary dependencies
- [ ] Version pins appropriate
- [ ] Compatible versions

### Security
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Input validation comprehensive
- [ ] Error messages don't leak secrets
- [ ] HTTPS enforced in production

### Monitoring
- [ ] Health checks working
- [ ] Metrics collecting
- [ ] Logs structured
- [ ] Request IDs trackable

---

## 📊 Final Verification Score

Count your checkmarks:

- **180-200 checks**: ✅ Excellent - Production Ready
- **160-179 checks**: 🟢 Good - Minor issues to fix
- **140-159 checks**: 🟡 Fair - Significant work needed
- **< 140 checks**: 🔴 Poor - Major issues present

---

## 🚀 Sign-Off

When all critical checks pass:

**Verified by**: _________________
**Date**: _________________
**Environment**: ☐ Development ☐ Staging ☐ Production
**Status**: ☐ Approved ☐ Needs Work

**Notes**:
_________________________________
_________________________________
_________________________________

---

**Phase 5 Status**: ☐ Ready for Deployment

