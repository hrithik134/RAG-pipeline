# Start RAG Pipeline with Docker (Complete Setup)
# This script starts the entire RAG pipeline stack with all Phase 5 features enabled

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RAG Pipeline - Docker Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This will start:" -ForegroundColor Yellow
Write-Host "  ✓ PostgreSQL database" -ForegroundColor Gray
Write-Host "  ✓ Redis (for rate limiting)" -ForegroundColor Gray
Write-Host "  ✓ FastAPI application" -ForegroundColor Gray
Write-Host "  ✓ Database migrations" -ForegroundColor Gray
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Docker is running" -ForegroundColor Green
Write-Host ""

# Check for .env file with API keys
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  No .env file found" -ForegroundColor Yellow
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Gray
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "IMPORTANT: Configure your API keys!" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Please edit .env and add your:" -ForegroundColor Yellow
        Write-Host "  - GOOGLE_API_KEY" -ForegroundColor Gray
        Write-Host "  - PINECONE_API_KEY" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Press any key after you've added your keys..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

# Stop any existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null

# Build and start containers
Write-Host "Building and starting containers..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Gray
Write-Host ""

docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ RAG Pipeline Started Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Access Your API" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "API Root:        http://localhost:8000" -ForegroundColor Green
    Write-Host "Swagger UI:      http://localhost:8000/docs" -ForegroundColor Green
    Write-Host "ReDoc:           http://localhost:8000/redoc" -ForegroundColor Green
    Write-Host "Health Check:    http://localhost:8000/health" -ForegroundColor Green
    Write-Host "Metrics:         http://localhost:8000/metrics" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Phase 5 Features Enabled" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "✓ Rate Limiting (Redis-backed)" -ForegroundColor Gray
    Write-Host "✓ Enhanced Error Handling" -ForegroundColor Gray
    Write-Host "✓ Pagination Support" -ForegroundColor Gray
    Write-Host "✓ Input Validation" -ForegroundColor Gray
    Write-Host "✓ Security Headers" -ForegroundColor Gray
    Write-Host "✓ API Documentation" -ForegroundColor Gray
    Write-Host "✓ Health & Metrics Endpoints" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Useful Commands" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "View logs:       docker-compose logs -f app" -ForegroundColor Gray
    Write-Host "Stop services:   docker-compose down" -ForegroundColor Gray
    Write-Host "Restart:         docker-compose restart" -ForegroundColor Gray
    Write-Host "Check status:    docker-compose ps" -ForegroundColor Gray
    Write-Host ""
    
    # Test the API
    Write-Host "Testing API..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get -ErrorAction Stop
        Write-Host "✅ API is responding!" -ForegroundColor Green
        Write-Host ""
        Write-Host "API Status:" -ForegroundColor Cyan
        $response | ConvertTo-Json -Depth 3
    } catch {
        Write-Host "⚠️  API not responding yet. Wait a few seconds and try:" -ForegroundColor Yellow
        Write-Host "   curl http://localhost:8000/" -ForegroundColor Gray
    }
    
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ Failed to Start Services" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the logs with:" -ForegroundColor Yellow
    Write-Host "  docker-compose logs" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Open http://localhost:8000/docs in your browser" -ForegroundColor Gray
Write-Host "2. Try the /health endpoint to verify all services" -ForegroundColor Gray
Write-Host "3. Upload documents using /v1/documents/upload" -ForegroundColor Gray
Write-Host "4. Query your documents using /v1/query" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 See PHASE_5_QUICKSTART.md for detailed examples" -ForegroundColor Yellow
Write-Host ""
