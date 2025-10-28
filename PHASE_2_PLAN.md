# Phase 2 - Document Ingestion & Processing
## Detailed Implementation Plan

---

## ✅ Phase 1 Recap - What We Built

**Completed**: Database architecture with 4 models
- ✅ `Upload` model (enforces 20 doc limit)
- ✅ `Document` model (enforces 1000 page limit)
- ✅ `Chunk` model (maps to Pinecone)
- ✅ `Query` model (logs queries)
- ✅ Alembic migration ready
- ✅ Model unit tests

---

## 🎯 Phase 2 Overview

Phase 2 implements the **document ingestion pipeline** that:
1. Accepts file uploads (PDF, DOCX, TXT)
2. Validates files (type, size, page count)
3. Extracts text content
4. Splits text into token-aware chunks
5. Stores chunks in database (ready for Phase 3 embedding)

---

## 📋 Objectives

1. **File Upload Handling**
   - Accept multipart file uploads
   - Validate file types (PDF, DOCX, TXT)
   - Enforce size limits (50 MB per file)
   - Calculate SHA-256 hash for deduplication

2. **Text Extraction**
   - PDF: PyMuPDF (primary) + pdfminer.six (fallback)
   - DOCX: python-docx
   - TXT: direct read
   - Handle encoding issues gracefully

3. **Page Count Validation**
   - Extract page count during parsing
   - Enforce 1000-page limit per document
   - Reject files exceeding limit

4. **Token-Aware Chunking**
   - Use tiktoken for accurate token counting
   - Default: 1000 tokens per chunk
   - Overlap: 150 tokens (15%)
   - Preserve sentence boundaries where possible

5. **Batch Processing**
   - Support up to 20 documents per upload batch
   - Process files asynchronously
   - Track progress per document
   - Handle partial failures gracefully

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Upload Request                        │
│              (multipart/form-data)                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   File Validator       │
        │  - Type check          │
        │  - Size check          │
        │  - Count check (≤20)   │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │   File Storage         │
        │  - Save to disk/S3     │
        │  - Calculate hash      │
        │  - Check duplicates    │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │   Text Extractor       │
        │  - PDF parser          │
        │  - DOCX parser         │
        │  - TXT reader          │
        │  - Page count check    │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │   Token Chunker        │
        │  - tiktoken counter    │
        │  - Overlap handling    │
        │  - Sentence boundary   │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │   Database Storage     │
        │  - Save Document       │
        │  - Save Chunks         │
        │  - Update Upload       │
        └────────────────────────┘
```

---

## 📦 Files to Create

### 1. **`app/services/file_validator.py`** (~150 lines)

**Purpose**: Validate uploaded files before processing

**Key Functions**:
```python
class FileValidator:
    def validate_file_type(file: UploadFile) -> bool
    def validate_file_size(file: UploadFile) -> bool
    def validate_batch_size(files: List[UploadFile]) -> bool
    def calculate_file_hash(file_path: str) -> str
    def check_duplicate(hash: str, db: Session) -> Optional[Document]
```

**Validations**:
- ✅ File extension in ['.pdf', '.docx', '.txt']
- ✅ File size ≤ 50 MB
- ✅ Batch size ≤ 20 files
- ✅ SHA-256 hash calculation
- ✅ Duplicate detection via hash

---

### 2. **`app/services/text_extractor.py`** (~250 lines)

**Purpose**: Extract text from different document formats

**Key Classes**:
```python
class BaseExtractor(ABC):
    @abstractmethod
    def extract_text(file_path: str) -> ExtractedText
    @abstractmethod
    def get_page_count(file_path: str) -> int

class PDFExtractor(BaseExtractor):
    # Uses PyMuPDF (fitz) primary
    # Falls back to pdfminer.six if needed
    def extract_text(file_path: str) -> ExtractedText
    def get_page_count(file_path: str) -> int

class DOCXExtractor(BaseExtractor):
    # Uses python-docx
    def extract_text(file_path: str) -> ExtractedText
    def get_page_count(file_path: str) -> int  # Estimated

class TXTExtractor(BaseExtractor):
    # Direct file read with encoding detection
    def extract_text(file_path: str) -> ExtractedText
    def get_page_count(file_path: str) -> int  # Always 1

class ExtractorFactory:
    def get_extractor(file_type: str) -> BaseExtractor
```

**Features**:
- ✅ Multi-format support (PDF, DOCX, TXT)
- ✅ Fallback mechanisms for PDFs
- ✅ Encoding detection (chardet)
- ✅ Page count extraction
- ✅ Error handling with detailed messages

**Page Count Handling**:
- **PDF**: Direct from PDF metadata
- **DOCX**: Estimated (chars / 1800)
- **TXT**: Always 1 page

---

### 3. **`app/services/chunking.py`** (~200 lines)

**Purpose**: Split text into token-aware chunks with overlap

**Key Classes**:
```python
class TokenChunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        encoding_name: str = "cl100k_base"
    )
    
    def chunk_text(
        self,
        text: str,
        document_id: UUID,
        metadata: Dict[str, Any]
    ) -> List[ChunkData]
    
    def count_tokens(self, text: str) -> int
    
    def split_by_sentences(self, text: str) -> List[str]
    
    def create_chunks_with_overlap(
        self,
        sentences: List[str]
    ) -> List[str]
```

**Chunking Strategy**:
1. **Split by sentences** (using NLTK or regex)
2. **Group sentences** until reaching ~1000 tokens
3. **Add overlap** by including last 150 tokens from previous chunk
4. **Track positions** (start_char, end_char)
5. **Preserve metadata** (page_number, document_id)

**Example**:
```
Document: 5000 tokens

Chunk 0: tokens 0-1000 (chars 0-4500)
Chunk 1: tokens 850-1850 (chars 3800-8300)  ← 150 token overlap
Chunk 2: tokens 1700-2700 (chars 7600-12100)
Chunk 3: tokens 2550-3550 (chars 11400-15900)
Chunk 4: tokens 3400-4400 (chars 15200-19700)
Chunk 5: tokens 4250-5000 (chars 19000-22500)
```

---

### 4. **`app/services/ingestion_service.py`** (~300 lines)

**Purpose**: Orchestrate the entire ingestion pipeline

**Key Class**:
```python
class IngestionService:
    def __init__(self, db: Session)
    
    async def process_upload_batch(
        self,
        files: List[UploadFile],
        upload_batch_id: str
    ) -> Upload
    
    async def process_single_document(
        self,
        file: UploadFile,
        upload: Upload
    ) -> Document
    
    def save_file(
        self,
        file: UploadFile,
        upload_id: UUID
    ) -> str  # Returns file_path
    
    def extract_and_chunk(
        self,
        file_path: str,
        document: Document
    ) -> List[Chunk]
```

**Workflow**:
1. **Create Upload** record (status=PENDING)
2. **Validate batch** (≤20 files)
3. **For each file**:
   - Validate type & size
   - Save to disk
   - Calculate hash & check duplicates
   - Create Document record
   - Extract text & page count
   - **Validate page count** (≤1000)
   - Chunk text
   - Save Chunks to database
   - Update Document status
4. **Update Upload** status (COMPLETED/FAILED)

---

### 5. **`app/schemas/document.py`** (~100 lines)

**Purpose**: Pydantic schemas for API requests/responses

**Key Schemas**:
```python
class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    file_size: int
    file_type: str
    page_count: int
    status: DocumentStatus
    created_at: datetime

class UploadBatchResponse(BaseModel):
    id: UUID
    upload_batch_id: str
    status: UploadStatus
    total_documents: int
    documents: List[DocumentUploadResponse]
    created_at: datetime

class ChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    token_count: int
    page_number: Optional[int]
    content_preview: str  # First 100 chars

class DocumentDetailResponse(BaseModel):
    id: UUID
    filename: str
    page_count: int
    total_chunks: int
    status: DocumentStatus
    chunks: List[ChunkResponse]
```

---

### 6. **`app/utils/file_storage.py`** (~100 lines)

**Purpose**: Handle file storage (local or cloud)

**Key Functions**:
```python
class FileStorage:
    def save_file(
        self,
        file: UploadFile,
        upload_id: UUID
    ) -> str  # Returns path
    
    def delete_file(self, file_path: str) -> None
    
    def get_file_path(
        self,
        upload_id: UUID,
        filename: str
    ) -> str
```

**Storage Structure**:
```
uploads/
├── {upload_id}/
│   ├── document1.pdf
│   ├── document2.docx
│   └── document3.txt
```

---

### 7. **`app/utils/exceptions.py`** (~80 lines)

**Purpose**: Custom exceptions for ingestion errors

**Key Exceptions**:
```python
class IngestionError(Exception):
    """Base ingestion error"""

class FileValidationError(IngestionError):
    """File validation failed"""

class PageLimitExceededError(IngestionError):
    """Document exceeds 1000 pages"""

class DocumentLimitExceededError(IngestionError):
    """Upload batch exceeds 20 documents"""

class ExtractionError(IngestionError):
    """Text extraction failed"""

class ChunkingError(IngestionError):
    """Chunking failed"""
```

---

## 🔧 Implementation Steps

### Step 1: File Validation (30 min)
- ✅ Create `file_validator.py`
- ✅ Implement type, size, batch validation
- ✅ Add hash calculation
- ✅ Add duplicate detection

### Step 2: Text Extraction (45 min)
- ✅ Create `text_extractor.py`
- ✅ Implement PDFExtractor (PyMuPDF + fallback)
- ✅ Implement DOCXExtractor
- ✅ Implement TXTExtractor
- ✅ Create ExtractorFactory
- ✅ Add page count extraction

### Step 3: Token Chunking (40 min)
- ✅ Create `chunking.py`
- ✅ Implement TokenChunker with tiktoken
- ✅ Add sentence boundary detection
- ✅ Implement overlap logic
- ✅ Track char positions

### Step 4: Ingestion Service (45 min)
- ✅ Create `ingestion_service.py`
- ✅ Implement batch processing
- ✅ Add file storage
- ✅ Integrate extractor & chunker
- ✅ Add error handling

### Step 5: Schemas & Utils (20 min)
- ✅ Create Pydantic schemas
- ✅ Create file storage utility
- ✅ Create custom exceptions

### Step 6: Testing (30 min)
- ✅ Unit tests for validator
- ✅ Unit tests for extractors
- ✅ Unit tests for chunker
- ✅ Integration test for full pipeline

---

## 📊 Key Constraints Enforced

| Constraint | Location | Enforcement |
|------------|----------|-------------|
| **≤20 documents/batch** | `file_validator.py` | Pre-upload validation |
| **≤1000 pages/doc** | `text_extractor.py` | Post-extraction validation |
| **≤50 MB/file** | `file_validator.py` | Pre-upload validation |
| **Valid file types** | `file_validator.py` | Extension check |
| **No duplicates** | `file_validator.py` | Hash comparison |

---

## 🧪 Testing Strategy

### Unit Tests (`tests/test_ingestion.py`)

1. **File Validator Tests**:
   ```python
   test_validate_file_type_valid()
   test_validate_file_type_invalid()
   test_validate_file_size_within_limit()
   test_validate_file_size_exceeds_limit()
   test_validate_batch_size_20_files()
   test_validate_batch_size_21_files()  # Should fail
   test_calculate_file_hash()
   test_check_duplicate_exists()
   ```

2. **Text Extractor Tests**:
   ```python
   test_pdf_extraction()
   test_pdf_page_count()
   test_pdf_fallback_to_pdfminer()
   test_docx_extraction()
   test_txt_extraction_utf8()
   test_txt_extraction_latin1()
   test_page_limit_exceeded()  # 1001 pages
   ```

3. **Chunker Tests**:
   ```python
   test_chunk_text_basic()
   test_chunk_with_overlap()
   test_token_counting()
   test_sentence_boundary_preservation()
   test_chunk_metadata()
   ```

### Integration Tests (`tests/test_ingestion_integration.py`)

```python
test_full_ingestion_pipeline()
test_batch_upload_20_documents()
test_reject_21st_document()
test_reject_1001_page_document()
test_duplicate_detection()
test_partial_batch_failure()
```

---

## 📈 Performance Considerations

### Optimization Strategies:

1. **Async Processing**:
   - Use `asyncio` for concurrent file processing
   - Process multiple documents in parallel (up to 5 at a time)

2. **Streaming**:
   - Stream file uploads to disk (don't load in memory)
   - Use `aiofiles` for async file I/O

3. **Chunking Efficiency**:
   - Cache tiktoken encoding
   - Batch token counting operations

4. **Memory Management**:
   - Process one document at a time
   - Clear text content after chunking
   - Use generators where possible

---

## 🔍 Error Handling

### Error Scenarios:

| Error | Handling |
|-------|----------|
| Invalid file type | Return 400 with clear message |
| File too large | Return 413 (Payload Too Large) |
| Too many files | Return 400 with limit message |
| Page limit exceeded | Mark document as FAILED, continue batch |
| Extraction failure | Mark document as FAILED, log error |
| Duplicate file | Skip, return existing document ID |
| Disk space full | Return 507 (Insufficient Storage) |

---

## 📝 Example Usage

### Upload Documents:
```python
# Client code
files = [
    ("files", open("doc1.pdf", "rb")),
    ("files", open("doc2.docx", "rb")),
]

response = requests.post(
    "http://localhost:8000/v1/documents:upload",
    files=files
)

# Response
{
    "upload_id": "uuid-123",
    "upload_batch_id": "batch-2025-10-25-001",
    "status": "processing",
    "total_documents": 2,
    "documents": [
        {
            "id": "doc-uuid-1",
            "filename": "doc1.pdf",
            "page_count": 45,
            "status": "processing"
        },
        {
            "id": "doc-uuid-2",
            "filename": "doc2.docx",
            "page_count": 12,
            "status": "processing"
        }
    ]
}
```

---

## 🎯 Success Criteria

After Phase 2, you will have:

1. **File Upload System**:
   - ✅ Accepts PDF, DOCX, TXT files
   - ✅ Validates all constraints (20 docs, 1000 pages, 50 MB)
   - ✅ Detects duplicates via hash

2. **Text Extraction**:
   - ✅ Extracts text from all formats
   - ✅ Accurate page counting
   - ✅ Robust error handling

3. **Token Chunking**:
   - ✅ 1000 tokens per chunk with 150 overlap
   - ✅ Preserves sentence boundaries
   - ✅ Tracks positions accurately

4. **Database Storage**:
   - ✅ Documents stored with metadata
   - ✅ Chunks stored with positions
   - ✅ Upload batches tracked

5. **Testing**:
   - ✅ Unit tests for all components
   - ✅ Integration tests for pipeline
   - ✅ Edge case coverage

---

## 🔗 Integration with Other Phases

### Phase 1 (Database) → Phase 2:
- Uses `Upload`, `Document`, `Chunk` models
- Enforces CHECK constraints at DB level

### Phase 2 → Phase 3 (Embeddings):
- Provides chunks ready for embedding
- Chunks have `embedding_id` field (NULL initially)
- Phase 3 will populate `embedding_id` after Pinecone upsert

### Phase 2 → Phase 5 (API):
- Provides `IngestionService` for upload endpoint
- Schemas ready for API responses

---

## 📊 Deliverables Summary

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `app/services/file_validator.py` | File validation | ~150 | Pending |
| `app/services/text_extractor.py` | Text extraction | ~250 | Pending |
| `app/services/chunking.py` | Token chunking | ~200 | Pending |
| `app/services/ingestion_service.py` | Orchestration | ~300 | Pending |
| `app/schemas/document.py` | API schemas | ~100 | Pending |
| `app/utils/file_storage.py` | File storage | ~100 | Pending |
| `app/utils/exceptions.py` | Custom errors | ~80 | Pending |
| `tests/test_ingestion.py` | Unit tests | ~400 | Pending |
| `tests/test_ingestion_integration.py` | Integration tests | ~200 | Pending |
| **Total** | **9 files** | **~1780 lines** | **Ready to build** |

---

## ⏱️ Estimated Time: 3.5 hours

- **Step 1** (Validation): 30 min
- **Step 2** (Extraction): 45 min
- **Step 3** (Chunking): 40 min
- **Step 4** (Service): 45 min
- **Step 5** (Schemas/Utils): 20 min
- **Step 6** (Testing): 30 min
- **Buffer**: 30 min

---

## 🚀 Ready to Proceed?

Phase 2 will create a complete document ingestion pipeline that:
- ✅ Accepts and validates file uploads
- ✅ Extracts text from PDF/DOCX/TXT
- ✅ Enforces all business rules (20 docs, 1000 pages)
- ✅ Creates token-aware chunks with overlap
- ✅ Stores everything in the database
- ✅ Provides comprehensive error handling
- ✅ Includes full test coverage

**All chunks will be ready for Phase 3 (embedding & Pinecone upsert).**

---

**Phase 1**: ✅ Complete  
**Phase 2**: 📋 Plan Ready  
**Next**: Implement Phase 2 ingestion pipeline

Type **"proceed with phase 2"** to start implementation!

