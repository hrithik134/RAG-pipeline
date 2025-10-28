# Complete API Reference

This document provides complete cURL examples for all API endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. Rate limiting is applied per IP address.

---

## Health & Status

### Health Check

Check if the API is running and healthy.

**Endpoint**: `GET /health`

**cURL**:
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "RAG Pipeline",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## Document Upload

### Upload Documents

Upload one or more documents for processing. Maximum 20 files per request.

**Endpoint**: `POST /v1/documents/upload`

**Rate Limit**: 10 requests per hour

**cURL**:
```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@document.pdf" \
  -F "files=@another.pdf"
```

**Multiple Files**:
```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.docx" \
  -F "files=@doc3.txt"
```

**Response**:
```json
{
  "upload_batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "total_documents": 2,
  "successful_documents": 2,
  "failed_documents": 0,
  "documents": [
    {
      "id": "uuid-1",
      "filename": "document.pdf",
      "status": "completed",
      "page_count": 42,
      "chunk_count": 156
    },
    {
      "id": "uuid-2",
      "filename": "another.pdf",
      "status": "completed",
      "page_count": 15,
      "chunk_count": 23
    }
  ]
}
```

**Error Response** (400):
```json
{
  "error": "File size exceeds limit (50 MB)",
  "status": 400
}
```

---

## Document Management

### List All Documents

Get a paginated list of all uploaded documents.

**Endpoint**: `GET /v1/documents`

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

**cURL**:
```bash
curl http://localhost:8000/v1/documents
```

**With Pagination**:
```bash
curl "http://localhost:8000/v1/documents?page=1&limit=10"
```

**Response**:
```json
{
  "total": 45,
  "page": 1,
  "limit": 20,
  "total_pages": 3,
  "items": [
    {
      "id": "uuid",
      "filename": "document.pdf",
      "upload_batch_id": "batch-uuid",
      "status": "completed",
      "page_count": 42,
      "chunk_count": 156,
      "uploaded_at": "2025-10-28T10:00:00Z"
    }
  ]
}
```

---

### Get Document Details

Get detailed information about a specific document, including chunks.

**Endpoint**: `GET /v1/documents/{document_id}`

**cURL**:
```bash
curl http://localhost:8000/v1/documents/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "upload_batch_id": "batch-uuid",
  "status": "completed",
  "page_count": 42,
  "chunk_count": 156,
  "uploaded_at": "2025-10-28T10:00:00Z",
  "file_size": 2048576,
  "chunks": [
    {
      "id": "chunk-uuid",
      "content": "First chunk content...",
      "page_number": 1,
      "chunk_index": 0
    }
  ]
}
```

---

### Get Document Chunks

Get all chunks for a specific document.

**Endpoint**: `GET /v1/documents/{document_id}/chunks`

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)

**cURL**:
```bash
curl http://localhost:8000/v1/documents/550e8400-e29b-41d4-a716-446655440000/chunks
```

**Response**:
```json
{
  "total": 156,
  "page": 1,
  "limit": 50,
  "chunks": [
    {
      "id": "chunk-uuid-1",
      "content": "First chunk...",
      "page_number": 1,
      "chunk_index": 0,
      "token_count": 250
    },
    {
      "id": "chunk-uuid-2",
      "content": "Second chunk...",
      "page_number": 1,
      "chunk_index": 1,
      "token_count": 245
    }
  ]
}
```

---

### Delete Document

Delete a document and all its associated chunks.

**Endpoint**: `DELETE /v1/documents/{document_id}`

**Rate Limit**: 20 requests per minute

**cURL**:
```bash
curl -X DELETE http://localhost:8000/v1/documents/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "message": "Document deleted successfully",
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Upload Progress

### Get Upload Progress

Check the status of an upload batch.

**Endpoint**: `GET /v1/documents/uploads/{upload_id}`

**cURL**:
```bash
curl http://localhost:8000/v1/documents/uploads/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "upload_batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "total_documents": 2,
  "completed_documents": 2,
  "failed_documents": 0,
  "started_at": "2025-10-28T10:00:00Z",
  "completed_at": "2025-10-28T10:05:00Z"
}
```

---

## Query

### Query Documents

Ask a question about your uploaded documents.

**Endpoint**: `POST /v1/query`

**Rate Limit**: 20 requests per minute

**cURL**:
```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'
```

**With Pretty Output**:
```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}' \
  | python -m json.tool
```

**Response**:
```json
{
  "query": "What is machine learning?",
  "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn from data without explicit programming. It uses algorithms to identify patterns and make predictions based on training data. Key types include supervised learning, unsupervised learning, and reinforcement learning.",
  "chunks": [
    {
      "id": "chunk-uuid",
      "content": "Machine learning is...",
      "document_id": "doc-uuid",
      "document_filename": "AI_Basics.pdf",
      "page_number": 5,
      "score": 0.92
    }
  ],
  "processing_time": 1.23,
  "query_id": "query-uuid"
}
```

---

## Query History

### List All Queries

Get a paginated list of all past queries.

**Endpoint**: `GET /v1/queries`

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

**cURL**:
```bash
curl http://localhost:8000/v1/queries
```

**Response**:
```json
{
  "total": 45,
  "page": 1,
  "limit": 20,
  "queries": [
    {
      "id": "query-uuid",
      "query": "What is machine learning?",
      "created_at": "2025-10-28T10:00:00Z",
      "processing_time": 1.23
    }
  ]
}
```

---

### Get Query Details

Get detailed information about a specific query.

**Endpoint**: `GET /v1/queries/{query_id}`

**cURL**:
```bash
curl http://localhost:8000/v1/queries/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "query": "What is machine learning?",
  "answer": "Machine learning is...",
  "created_at": "2025-10-28T10:00:00Z",
  "processing_time": 1.23,
  "chunks_used": 5
}
```

---

## Error Responses

### Common Error Codes

**400 - Bad Request**:
```json
{
  "error": "Invalid request",
  "detail": "Field 'query' is required",
  "status": 400
}
```

**404 - Not Found**:
```json
{
  "error": "Document not found",
  "status": 404
}
```

**429 - Too Many Requests**:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "status": 429
}
```

**500 - Internal Server Error**:
```json
{
  "error": "Internal server error",
  "detail": "Error processing request",
  "status": 500
}
```

---

## Interactive Documentation

### Swagger UI

Access interactive API documentation:

```bash
open http://localhost:8000/docs
```

### ReDoc

Alternative API documentation:

```bash
open http://localhost:8000/redoc
```

---

## Testing the API

### Using PowerShell

**Upload Documents**:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/documents/upload" `
  -Method Post `
  -Form @{files = Get-Item "document.pdf"}
```

**Query Documents**:
```powershell
$body = @{query = "What is AI?"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/v1/query" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

### Using Python

**Install requests**:
```bash
pip install requests
```

**Upload and Query**:
```python
import requests

# Upload
files = [('files', open('document.pdf', 'rb'))]
response = requests.post('http://localhost:8000/v1/documents/upload', files=files)
print(response.json())

# Query
response = requests.post(
    'http://localhost:8000/v1/query',
    json={'query': 'What is AI?'}
)
print(response.json())
```

---

## Rate Limiting

Rate limits are per IP address:

- **Upload**: 10 requests per hour
- **Query**: 20 requests per minute
- **Read**: 100 requests per minute
- **Delete**: 20 requests per minute
- **Health**: 300 requests per minute

Rate limit information is returned in response headers:

```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1234567890
```

---

## File Upload Limits

- **Max files per request**: 20
- **Max file size**: 50 MB
- **Max pages per document**: 1,000
- **Supported formats**: PDF, DOCX, TXT, MD

---

For more information:
- [Architecture](architecture.md)
- [Operations Guide](operations.md)
- [Configuration Guide](configuration.md)

