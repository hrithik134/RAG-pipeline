# Phase 2 Setup Script
# Installs dependencies and validates the Phase 2 implementation

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 2 Setup - Document Ingestion" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".\.venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Virtual environment found" -ForegroundColor Green

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "`nInstalling Phase 2 dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green

# Create upload directory
Write-Host "`nCreating upload directory..." -ForegroundColor Yellow
if (-not (Test-Path ".\uploads")) {
    New-Item -ItemType Directory -Path ".\uploads" | Out-Null
    Write-Host "✅ Upload directory created" -ForegroundColor Green
} else {
    Write-Host "✅ Upload directory already exists" -ForegroundColor Green
}

# Run validation
Write-Host "`nRunning Phase 2 validation..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
python test_phase2_validation.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "✅ PHASE 2 SETUP COMPLETE!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Start the server: uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host "  2. Open API docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  3. Run tests: pytest tests/test_ingestion.py -v" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "⚠️  VALIDATION FAILED" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Some tests failed. Please review the output above." -ForegroundColor Yellow
    Write-Host "The application should still work, but some features may have issues." -ForegroundColor Yellow
    Write-Host ""
}

