# Manual FastAPI Testing Script
# This script helps you test the FastAPI application

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   FastAPI Application Manual Test" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is available
Write-Host "Checking Docker availability..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker is available" -ForegroundColor Green
        $useDocker = $true
    } else {
        Write-Host "❌ Docker is not available" -ForegroundColor Red
        $useDocker = $false
    }
} catch {
    Write-Host "❌ Docker is not installed" -ForegroundColor Red
    $useDocker = $false
}

Write-Host ""

if ($useDocker) {
    Write-Host "🐳 Testing with Docker..." -ForegroundColor Cyan
    Write-Host ""
    
    # Build the image
    Write-Host "Step 1: Building Docker image..." -ForegroundColor Yellow
    docker build -t rag-pipeline:test .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker image built successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to build Docker image" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    
    # Run the container
    Write-Host "Step 2: Starting container..." -ForegroundColor Yellow
    docker run -d -p 8000:8000 --name rag-api-test --env-file .env rag-pipeline:test
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container started successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to start container" -ForegroundColor Red
        Write-Host "   Trying to remove existing container..." -ForegroundColor Yellow
        docker rm -f rag-api-test 2>$null
        docker run -d -p 8000:8000 --name rag-api-test --env-file .env rag-pipeline:test
    }
    
    Write-Host ""
    Write-Host "Step 3: Waiting for application to start (10 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host ""
    Write-Host "Step 4: Checking container logs..." -ForegroundColor Yellow
    docker logs rag-api-test --tail 20
    
    Write-Host ""
    Write-Host "Step 5: Testing health endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
        Write-Host "✅ Health check successful!" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Cyan
        $response | ConvertTo-Json -Depth 3
    } catch {
        Write-Host "❌ Health check failed" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host "   🌐 Access the Application" -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Open these URLs in your browser:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Swagger UI (Interactive Docs):" -ForegroundColor White
    Write-Host "   http://localhost:8000/docs" -ForegroundColor Green
    Write-Host ""
    Write-Host "2. ReDoc (Clean Docs):" -ForegroundColor White
    Write-Host "   http://localhost:8000/redoc" -ForegroundColor Green
    Write-Host ""
    Write-Host "3. Health Check:" -ForegroundColor White
    Write-Host "   http://localhost:8000/health" -ForegroundColor Green
    Write-Host ""
    Write-Host "4. Root Endpoint:" -ForegroundColor White
    Write-Host "   http://localhost:8000/" -ForegroundColor Green
    Write-Host ""
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Enter to stop the container and clean up..." -ForegroundColor Yellow
    Read-Host
    
    Write-Host ""
    Write-Host "Stopping and removing container..." -ForegroundColor Yellow
    docker stop rag-api-test
    docker rm rag-api-test
    
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
    
} else {
    Write-Host "⚠️  Docker is not available" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To test the FastAPI application, you need to:" -ForegroundColor Yellow
    Write-Host "1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "   OR" -ForegroundColor Yellow
    Write-Host "2. Fix your Python installation (3.10-3.12 recommended)" -ForegroundColor White
    Write-Host ""
    Write-Host "After installing Docker, run this script again." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan

