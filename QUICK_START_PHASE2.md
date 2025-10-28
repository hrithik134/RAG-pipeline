# Phase 2 Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies (2 min)
```powershell
.\SETUP_PHASE2.ps1
```

### Step 2: Start Server (1 min)
```powershell
uvicorn app.main:app --reload
```

### Step 3: Test Endpoints (2 min)
```powershell
# In a new terminal
.\TEST_PHASE2_ENDPOINTS.ps1
```

### Step 4: View API Docs
Open: http://localhost:8000/docs

---

## 📤 Upload Documents

### Using Swagger UI
1. Go to http://localhost:8000/docs
2. Click on `POST /v1/documents/upload`
3. Click "Try it out"
4. Click "Add file" and select your documents
5. Click "Execute"

### Using PowerShell
```powershell
$files = @(
    @{Name='files'; FileName='doc1.pdf'; FilePath='C:\path\to\doc1.pdf'},
    @{Name='files'; FileName='doc2.docx'; FilePath='C:\path\to\doc2.docx'}
)

Invoke-RestMethod -Uri "http://localhost:8000/v1/documents/upload" `
    -Method Post `
    -Form $files
```

### Using Python
```python
import requests

files = [
    ('files', open('doc1.pdf', 'rb')),
    ('files', open('doc2.docx', 'rb')),
]

response = requests.post(
    'http://localhost:8000/v1/documents/upload',
    files=files
)

print(response.json())
```

### Using curl
```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.docx"
```

---

## 🔍 Check Status

### Get Upload Status
```powershell
$uploadId = "your-upload-id-here"
Invoke-RestMethod -Uri "http://localhost:8000/v1/documents/uploads/$uploadId"
```

### Get Progress
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/documents/uploads/$uploadId/progress"
```

---

## 📋 List & View

### List All Documents
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/documents?limit=10"
```

### Get Document Details
```powershell
$docId = "your-document-id-here"
Invoke-RestMethod -Uri "http://localhost:8000/v1/documents/$docId"
```

### Get Document Chunks
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/documents/$docId/chunks?limit=5"
```

---

## 🧪 Run Tests

### All Tests
```powershell
pytest tests/ -v
```

### Unit Tests Only
```powershell
pytest tests/test_ingestion.py -v
```

### Integration Tests Only
```powershell
pytest tests/test_ingestion_integration.py -v
```

### With Coverage
```powershell
pytest tests/ --cov=app --cov-report=html
```

---

## 📊 Key Limits

| Limit | Value |
|-------|-------|
| Max files per batch | 20 |
| Max file size | 50 MB |
| Max pages per document | 1000 |
| Tokens per chunk | 1000 |
| Token overlap | 150 |
| Supported formats | PDF, DOCX, TXT, MD |

---

## 🐛 Troubleshooting

### Server won't start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
uvicorn app.main:app --reload --port 8001
```

### Import errors
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Upload fails
- Check file size (must be ≤50 MB)
- Check file type (must be PDF, DOCX, TXT, or MD)
- Check batch size (must be ≤20 files)

### Database errors
```powershell
# Run migrations
alembic upgrade head
```

---

## 📚 Documentation

- **Full Details**: `PHASE_2_COMPLETE.md`
- **Summary**: `PHASE_2_SUMMARY.md`
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ✅ Verify Installation

```powershell
python test_phase2_validation.py
```

All tests should pass ✅

---

## 🎯 What's Working

✅ File upload (PDF, DOCX, TXT, MD)  
✅ File validation (type, size, count)  
✅ Duplicate detection  
✅ Text extraction  
✅ Page count validation  
✅ Token-aware chunking  
✅ Sentence boundary preservation  
✅ Database storage  
✅ Status tracking  
✅ Progress monitoring  
✅ Error handling  

---

## 🔜 Next: Phase 3

Phase 3 will add:
- Embedding generation (OpenAI/Google)
- Pinecone vector storage
- Semantic search capabilities

---

**Phase 2 is ready to use! 🎉**

Upload your documents and watch them get processed, extracted, and chunked automatically!

