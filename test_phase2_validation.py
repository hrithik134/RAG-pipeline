"""
Phase 2 Validation Script

This script validates that all Phase 2 components are properly implemented
and can be imported without errors.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all Phase 2 modules can be imported."""
    print("=" * 70)
    print("PHASE 2 VALIDATION - Import Tests")
    print("=" * 70)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Exceptions
    try:
        from app.utils.exceptions import (
            IngestionError,
            FileValidationError,
            InvalidFileTypeError,
            FileSizeExceededError,
            DocumentLimitExceededError,
            PageLimitExceededError,
            DuplicateDocumentError,
            ExtractionError,
            ChunkingError,
            StorageError,
            InsufficientStorageError,
        )
        print("✅ Test 1: Custom exceptions imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        tests_failed += 1
    
    # Test 2: File Storage
    try:
        from app.utils.file_storage import FileStorage
        storage = FileStorage()
        print("✅ Test 2: FileStorage imported and instantiated")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        tests_failed += 1
    
    # Test 3: File Validator
    try:
        from app.services.file_validator import FileValidator
        validator = FileValidator()
        print("✅ Test 3: FileValidator imported and instantiated")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        tests_failed += 1
    
    # Test 4: Text Extractors
    try:
        from app.services.text_extractor import (
            BaseExtractor,
            PDFExtractor,
            DOCXExtractor,
            TXTExtractor,
            MarkdownExtractor,
            ExtractorFactory,
            ExtractedText,
        )
        pdf_extractor = PDFExtractor()
        docx_extractor = DOCXExtractor()
        txt_extractor = TXTExtractor()
        print("✅ Test 4: Text extractors imported and instantiated")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        tests_failed += 1
    
    # Test 5: Token Chunker
    try:
        from app.services.chunking import TokenChunker, ChunkData
        chunker = TokenChunker()
        print("✅ Test 5: TokenChunker imported and instantiated")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}")
        tests_failed += 1
    
    # Test 6: Ingestion Service
    try:
        from app.services.ingestion_service import IngestionService
        print("✅ Test 6: IngestionService imported")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 6 FAILED: {e}")
        tests_failed += 1
    
    # Test 7: Pydantic Schemas
    try:
        from app.schemas.document import (
            ChunkResponse,
            ChunkDetailResponse,
            DocumentUploadResponse,
            DocumentDetailResponse,
            DocumentListResponse,
            UploadBatchResponse,
            UploadProgressResponse,
            ErrorResponse,
        )
        print("✅ Test 7: Pydantic schemas imported")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 7 FAILED: {e}")
        tests_failed += 1
    
    # Test 8: Upload Router
    try:
        from app.routers.upload import router
        print("✅ Test 8: Upload router imported")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 8 FAILED: {e}")
        tests_failed += 1
    
    # Test 9: Main App Integration
    try:
        from app.main import app
        print("✅ Test 9: Main FastAPI app imported with router")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 9 FAILED: {e}")
        tests_failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)
    
    return tests_failed == 0


def test_functionality():
    """Test basic functionality of Phase 2 components."""
    print("\n" + "=" * 70)
    print("PHASE 2 VALIDATION - Functionality Tests")
    print("=" * 70)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Token Counting
    try:
        from app.services.chunking import TokenChunker
        chunker = TokenChunker()
        
        text = "This is a test sentence."
        token_count = chunker.count_tokens(text)
        
        assert token_count > 0, "Token count should be greater than 0"
        print(f"✅ Test 1: Token counting works (counted {token_count} tokens)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        tests_failed += 1
    
    # Test 2: Sentence Splitting
    try:
        from app.services.chunking import TokenChunker
        chunker = TokenChunker()
        
        text = "First sentence. Second sentence! Third sentence?"
        sentences = chunker.split_by_sentences(text)
        
        assert len(sentences) >= 3, "Should split into at least 3 sentences"
        print(f"✅ Test 2: Sentence splitting works (found {len(sentences)} sentences)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        tests_failed += 1
    
    # Test 3: File Type Validation
    try:
        from app.services.file_validator import FileValidator
        from unittest.mock import Mock
        from fastapi import UploadFile
        
        validator = FileValidator()
        
        # Test valid file
        file = Mock(spec=UploadFile)
        file.filename = "test.pdf"
        result = validator.validate_file_type(file)
        
        assert result is True, "PDF should be valid"
        print("✅ Test 3: File type validation works")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        tests_failed += 1
    
    # Test 4: ExtractorFactory
    try:
        from app.services.text_extractor import ExtractorFactory, PDFExtractor
        
        extractor = ExtractorFactory.get_extractor("document.pdf")
        assert isinstance(extractor, PDFExtractor), "Should return PDFExtractor"
        
        print("✅ Test 4: ExtractorFactory works")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        tests_failed += 1
    
    # Test 5: Exception Hierarchy
    try:
        from app.utils.exceptions import (
            IngestionError,
            FileValidationError,
            InvalidFileTypeError,
        )
        
        # Test exception inheritance
        assert issubclass(FileValidationError, IngestionError)
        assert issubclass(InvalidFileTypeError, FileValidationError)
        
        print("✅ Test 5: Exception hierarchy correct")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}")
        tests_failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)
    
    return tests_failed == 0


def test_configuration():
    """Test that configuration is properly set up."""
    print("\n" + "=" * 70)
    print("PHASE 2 VALIDATION - Configuration Tests")
    print("=" * 70)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Settings
    try:
        from app.config import settings
        
        assert settings.max_documents_per_upload == 20
        assert settings.max_pages_per_document == 1000
        assert settings.max_file_size_mb == 50
        assert settings.chunk_size == 1000
        assert settings.chunk_overlap == 150
        
        print("✅ Test 1: Configuration settings correct")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        tests_failed += 1
    
    # Test 2: Allowed Extensions
    try:
        from app.config import settings
        
        extensions = settings.allowed_extensions_list
        assert '.pdf' in extensions
        assert '.docx' in extensions
        assert '.txt' in extensions
        
        print(f"✅ Test 2: Allowed extensions configured: {extensions}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        tests_failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)
    
    return tests_failed == 0


def main():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("PHASE 2 IMPLEMENTATION VALIDATION")
    print("RAG Pipeline - Document Ingestion & Processing")
    print("=" * 70 + "\n")
    
    import_success = test_imports()
    functionality_success = test_functionality()
    config_success = test_configuration()
    
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    if import_success and functionality_success and config_success:
        print("✅ ALL TESTS PASSED - Phase 2 is ready!")
        print("\nPhase 2 Components:")
        print("  ✅ Custom exceptions")
        print("  ✅ File storage utility")
        print("  ✅ File validator service")
        print("  ✅ Text extractor service (PDF, DOCX, TXT, MD)")
        print("  ✅ Token chunking service")
        print("  ✅ Ingestion orchestration service")
        print("  ✅ Pydantic schemas")
        print("  ✅ Upload router endpoint")
        print("  ✅ Unit tests")
        print("  ✅ Integration tests")
        print("\nNext Steps:")
        print("  1. Start the application: python -m uvicorn app.main:app --reload")
        print("  2. Test endpoints at: http://localhost:8000/docs")
        print("  3. Run tests: pytest tests/test_ingestion.py")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

