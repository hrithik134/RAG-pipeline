# Test Runner Script for Phase 7
# Run comprehensive test suite with coverage

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 7: Comprehensive Testing Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Run different test categories
Write-Host ""
Write-Host "Running Unit Tests..." -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow
python -m pytest tests/test_chunking_comprehensive.py tests/test_extractors_comprehensive.py tests/test_validators_comprehensive.py -m unit -v --tb=short

Write-Host ""
Write-Host "Running Integration Tests..." -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow
python -m pytest tests/test_api_endpoints.py tests/test_rag_pipeline_complete.py -m integration -v --tb=short

Write-Host ""
Write-Host "Running All Tests with Coverage..." -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow
python -m pytest --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=85 -v

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Coverage report generated in: htmlcov/index.html" -ForegroundColor Green
Write-Host ""
Write-Host "To run specific test categories:" -ForegroundColor Cyan
Write-Host "  pytest -m unit           # Unit tests only" -ForegroundColor White
Write-Host "  pytest -m integration    # Integration tests only" -ForegroundColor White
Write-Host "  pytest -m slow           # Slow tests only" -ForegroundColor White
Write-Host "  pytest -m 'not slow'     # Skip slow tests" -ForegroundColor White
Write-Host ""
Write-Host "To run specific test files:" -ForegroundColor Cyan
Write-Host "  pytest tests/test_chunking_comprehensive.py" -ForegroundColor White
Write-Host "  pytest tests/test_api_endpoints.py" -ForegroundColor White
Write-Host ""

