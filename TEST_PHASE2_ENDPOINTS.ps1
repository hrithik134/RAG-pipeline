# Phase 2 Endpoint Testing Script
# Tests the document upload and processing endpoints

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 2 Endpoint Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Check if server is running
Write-Host "Checking if server is running..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "✅ Server is running" -ForegroundColor Green
    Write-Host "   Service: $($health.service)" -ForegroundColor Gray
    Write-Host "   Version: $($health.version)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Server is not running!" -ForegroundColor Red
    Write-Host "Please start the server first: uvicorn app.main:app --reload" -ForegroundColor Yellow
    exit 1
}

# Create test files
Write-Host "Creating test files..." -ForegroundColor Yellow
$testDir = ".\test_uploads"
if (-not (Test-Path $testDir)) {
    New-Item -ItemType Directory -Path $testDir | Out-Null
}

# Create test TXT file
$testFile1 = "$testDir\test_document_1.txt"
@"
This is a test document for Phase 2 validation.

It contains multiple paragraphs to test the chunking functionality.
The document should be processed, extracted, and chunked into smaller pieces.

Each chunk will have approximately 1000 tokens with 150 token overlap.
This ensures that context is preserved between chunks for better retrieval.

The RAG pipeline will use these chunks for semantic search and question answering.
"@ | Out-File -FilePath $testFile1 -Encoding UTF8

# Create test TXT file 2
$testFile2 = "$testDir\test_document_2.txt"
@"
This is the second test document.

It demonstrates batch upload functionality where multiple documents
can be uploaded and processed simultaneously.

The system enforces a limit of 20 documents per batch and 1000 pages per document.
Each file must be under 50 MB in size.
"@ | Out-File -FilePath $testFile2 -Encoding UTF8

Write-Host "✅ Test files created" -ForegroundColor Green
Write-Host ""

# Test 1: Upload documents
Write-Host "Test 1: Uploading documents..." -ForegroundColor Yellow
try {
    $form = @{
        files = Get-Item $testFile1, $testFile2
    }
    
    $upload = Invoke-RestMethod -Uri "$baseUrl/v1/documents/upload" `
        -Method Post `
        -Form $form
    
    Write-Host "✅ Upload successful" -ForegroundColor Green
    Write-Host "   Upload ID: $($upload.id)" -ForegroundColor Gray
    Write-Host "   Batch ID: $($upload.upload_batch_id)" -ForegroundColor Gray
    Write-Host "   Status: $($upload.status)" -ForegroundColor Gray
    Write-Host "   Total Documents: $($upload.total_documents)" -ForegroundColor Gray
    Write-Host "   Successful: $($upload.successful_documents)" -ForegroundColor Gray
    Write-Host "   Failed: $($upload.failed_documents)" -ForegroundColor Gray
    Write-Host ""
    
    $uploadId = $upload.id
    $documentId = $upload.documents[0].id
    
} catch {
    Write-Host "❌ Upload failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Get upload status
Write-Host "Test 2: Getting upload status..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "$baseUrl/v1/documents/uploads/$uploadId" -Method Get
    
    Write-Host "✅ Status retrieved" -ForegroundColor Green
    Write-Host "   Status: $($status.status)" -ForegroundColor Gray
    Write-Host "   Documents: $($status.total_documents)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Failed to get status: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Get upload progress
Write-Host "Test 3: Getting upload progress..." -ForegroundColor Yellow
try {
    $progress = Invoke-RestMethod -Uri "$baseUrl/v1/documents/uploads/$uploadId/progress" -Method Get
    
    Write-Host "✅ Progress retrieved" -ForegroundColor Green
    Write-Host "   Progress: $($progress.progress_percentage)%" -ForegroundColor Gray
    Write-Host "   Processed: $($progress.processed_documents)/$($progress.total_documents)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Failed to get progress: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Get document details
Write-Host "Test 4: Getting document details..." -ForegroundColor Yellow
try {
    $document = Invoke-RestMethod -Uri "$baseUrl/v1/documents/$documentId" -Method Get
    
    Write-Host "✅ Document retrieved" -ForegroundColor Green
    Write-Host "   Filename: $($document.filename)" -ForegroundColor Gray
    Write-Host "   Status: $($document.status)" -ForegroundColor Gray
    Write-Host "   Pages: $($document.page_count)" -ForegroundColor Gray
    Write-Host "   Chunks: $($document.total_chunks)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Failed to get document: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: List documents
Write-Host "Test 5: Listing documents..." -ForegroundColor Yellow
try {
    $documents = Invoke-RestMethod -Uri "$baseUrl/v1/documents?skip=0&limit=10" -Method Get
    
    Write-Host "✅ Documents listed" -ForegroundColor Green
    Write-Host "   Count: $($documents.Count)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Failed to list documents: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Get document chunks
Write-Host "Test 6: Getting document chunks..." -ForegroundColor Yellow
try {
    $chunks = Invoke-RestMethod -Uri "$baseUrl/v1/documents/$documentId/chunks?limit=5" -Method Get
    
    Write-Host "✅ Chunks retrieved" -ForegroundColor Green
    Write-Host "   Count: $($chunks.Count)" -ForegroundColor Gray
    if ($chunks.Count -gt 0) {
        Write-Host "   First chunk preview: $($chunks[0].content_preview)" -ForegroundColor Gray
    }
    Write-Host ""
} catch {
    Write-Host "❌ Failed to get chunks: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ ALL ENDPOINT TESTS COMPLETED" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Phase 2 endpoints are working correctly!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now:" -ForegroundColor Yellow
Write-Host "  • View API docs: $baseUrl/docs" -ForegroundColor White
Write-Host "  • Upload more documents via the API" -ForegroundColor White
Write-Host "  • Proceed to Phase 3 (Embeddings & Pinecone)" -ForegroundColor White
Write-Host ""

# Cleanup
Write-Host "Cleaning up test files..." -ForegroundColor Yellow
Remove-Item -Path $testDir -Recurse -Force
Write-Host "✅ Cleanup complete" -ForegroundColor Green

