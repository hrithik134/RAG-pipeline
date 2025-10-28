# Google AI Setup Guide

## 🔄 Switch from OpenAI to Google AI

This guide shows you how to use Google AI (Vertex AI) embeddings instead of OpenAI.

---

## ⚠️ **IMPORTANT: Dimension Change**

**Google embeddings are 768 dimensions**, not 3072 like OpenAI's `text-embedding-3-large`.

You **MUST** change `PINECONE_DIMENSION` from `3072` to `768` or you'll get dimension mismatch errors!

---

## 📝 **Step 1: Get Google AI API Key**

1. Go to: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

---

## 📝 **Step 2: Create `.env` File**

Create a file named `.env` in your project root (`D:\RAG pipeline\.env`) with this content:

```bash
# ============================================================================
# REQUIRED: Google AI API Key
# ============================================================================

GOOGLE_API_KEY=AIza...your-google-api-key...

# ============================================================================
# REQUIRED: Pinecone API Key
# ============================================================================

PINECONE_API_KEY=pcsk_...your-pinecone-key...

# ============================================================================
# Pinecone Configuration (CRITICAL: Google = 768D!)
# ============================================================================

PINECONE_INDEX_NAME=ragingestion-google
PINECONE_DIMENSION=768
PINECONE_METRIC=cosine
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# ============================================================================
# Google AI Configuration
# ============================================================================

GOOGLE_EMBEDDING_MODEL=models/text-embedding-004
GOOGLE_MODEL=gemini-1.5-pro

# ============================================================================
# Provider Selection
# ============================================================================

EMBEDDING_PROVIDER=google
LLM_PROVIDER=google

# ============================================================================
# Optional: Performance Tuning
# ============================================================================

EMBED_BATCH_SIZE=64
UPSERT_BATCH_SIZE=100
INDEX_CONCURRENCY=2
EMBED_RETRY_MAX=5
EMBED_RETRY_DELAY=1.0
```

---

## 📝 **Step 3: Files Already Updated**

I've already updated `docker-compose.yml` for you! The changes include:

1. ✅ Changed default `PINECONE_DIMENSION` from `3072` to `768`
2. ✅ Changed default `PINECONE_INDEX_NAME` to `ragingestion-google`
3. ✅ Added `GOOGLE_API_KEY` environment variable
4. ✅ Added `GOOGLE_MODEL` and `GOOGLE_EMBEDDING_MODEL`
5. ✅ Changed default providers to `google`
6. ✅ Removed hardcoded API keys (now uses `.env` file)

**No code changes needed!** Just create the `.env` file above.

---

## 🚀 **Step 4: Deploy**

```powershell
# Stop existing services
docker-compose down

# Remove old Pinecone index (if it exists with wrong dimension)
# You can do this in Pinecone dashboard or it will auto-create new one

# Rebuild and start
docker-compose build app
docker-compose up -d

# Check logs
docker-compose logs app --tail 50
```

---

## ✅ **Step 5: Verify**

Look for these lines in the logs:

```
Initialized Vertex embedding provider
Initialized Pinecone store: index=ragingestion-google, dimension=768
```

If you see:
- ❌ `"Dimension mismatch"` → Delete old Pinecone index or change `PINECONE_INDEX_NAME`
- ❌ `"Google API key is required"` → Check your `.env` file
- ✅ `"Initialized Vertex"` → Success!

---

## 🧪 **Step 6: Test**

```powershell
# Upload a test document
curl -X POST "http://localhost:8000/v1/documents/upload" `
  -F "files=@test.pdf"

# Check indexing status
curl "http://localhost:8000/v1/documents/{doc-id}/indexing-status"
```

---

## ⚠️ **Known Limitation**

**Google AI embedding provider is currently a STUB!**

The implementation in `app/services/embeddings/vertex_provider.py` raises `NotImplementedError`.

### **To Make It Work, You Need to Implement:**

1. Install Google AI SDK:
   ```bash
   pip install google-generativeai
   ```

2. Update `app/services/embeddings/vertex_provider.py`:

```python
import google.generativeai as genai
from typing import List, Optional

class VertexEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str = "models/text-embedding-004"):
        genai.configure(api_key=api_key)
        self.model = model
    
    async def embed_texts(self, texts: List[str], batch_size: Optional[int] = None):
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        
        return EmbeddingResult(
            embeddings=embeddings,
            model=self.model,
            total_tokens=len(texts) * 100,  # Estimate
            dimension=768
        )
    
    def dimension(self) -> int:
        return 768
    
    def model_name(self) -> str:
        return self.model
    
    def max_input_length(self) -> int:
        return 2048
```

---

## 🔄 **Alternative: Use OpenAI Instead**

If you want to use OpenAI (which is fully implemented), just change your `.env`:

```bash
# Use OpenAI
OPENAI_API_KEY=sk-...your-key...
EMBEDDING_PROVIDER=openai
PINECONE_DIMENSION=3072
PINECONE_INDEX_NAME=ragingestion
```

---

## 📊 **Comparison: Google vs OpenAI**

| Feature | Google AI | OpenAI |
|---------|-----------|--------|
| Embedding Model | text-embedding-004 | text-embedding-3-large |
| Dimension | 768 | 3072 |
| Max Input | 2048 tokens | 8191 tokens |
| Cost | Free (with limits) | $0.13 per 1M tokens |
| Implementation | ⚠️ Stub (needs work) | ✅ Fully implemented |
| Quality | Good | Excellent |

---

## 🛠️ **Troubleshooting**

### **Error: "Dimension mismatch"**

**Cause**: Existing Pinecone index has 3072D (OpenAI), but Google is 768D.

**Solution**:
1. Delete old index in Pinecone dashboard
2. Or change `PINECONE_INDEX_NAME` to create new index
3. Restart: `docker-compose down && docker-compose up -d`

### **Error: "NotImplementedError"**

**Cause**: Vertex provider is a stub.

**Solution**: Either:
1. Implement the provider (see code above)
2. Or switch back to OpenAI

### **Error: "Google API key is required"**

**Cause**: `.env` file not found or key not set.

**Solution**:
1. Verify `.env` exists: `Test-Path .env`
2. Check contents: `Get-Content .env`
3. Restart: `docker-compose restart FastAPI`

---

## 📚 **Summary of Changes**

### **Files Modified:**
1. ✅ `docker-compose.yml` - Updated environment variables

### **Files to Create:**
1. `.env` - Add your Google API key here

### **No Changes Needed:**
- ❌ No Python code changes
- ❌ No database changes
- ❌ No configuration file edits

---

## 🎯 **Quick Setup Commands**

```powershell
# 1. Create .env file
@"
GOOGLE_API_KEY=AIza...your-key...
PINECONE_API_KEY=pcsk_...your-key...
PINECONE_DIMENSION=768
PINECONE_INDEX_NAME=ragingestion-google
EMBEDDING_PROVIDER=google
LLM_PROVIDER=google
"@ | Out-File -FilePath .env -Encoding utf8

# 2. Restart services
docker-compose down
docker-compose up -d

# 3. Check logs
docker-compose logs FastAPI --tail 50
```

---

## ⚠️ **CRITICAL REMINDER**

**Google embeddings = 768 dimensions**  
**OpenAI embeddings = 3072 dimensions**

**You CANNOT mix them!** If you have documents indexed with OpenAI (3072D), you must:
1. Delete them from Pinecone
2. Reindex with Google (768D)
3. Or use a different index name

---

**Need Help?** Check `PHASE_3_COMPLETE.md` for more details!

