# ==========================================
# Docker Start Script
# ==========================================
# Starts all Docker containers for the RAG Pipeline
# Usage: .\docker-start.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  RAG Pipeline - Docker Start Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "[1/6] Checking Docker status..." -ForegroundColor Yellow
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker is not running!" -ForegroundColor Red
        Write-Host "Please start Docker Desktop and try again." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not accessible!" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
Write-Host ""
Write-Host "[2/6] Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    
    if (Test-Path "env.example") {
        Write-Host "Creating .env from env.example..." -ForegroundColor Yellow
        Copy-Item "env.example" ".env"
        Write-Host "✅ .env file created" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  IMPORTANT: Please edit .env and add your API keys!" -ForegroundColor Yellow
        Write-Host "   - PINECONE_API_KEY" -ForegroundColor Yellow
        Write-Host "   - GOOGLE_API_KEY or OPENAI_API_KEY" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press any key to open .env file in notepad..." -ForegroundColor Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        notepad .env
        Write-Host ""
        Write-Host "After adding API keys, press any key to continue..." -ForegroundColor Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    } else {
        Write-Host "❌ env.example not found! Cannot create .env" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ .env file found" -ForegroundColor Green
}

# Stop any existing containers
Write-Host ""
Write-Host "[3/6] Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null
Write-Host "✅ Existing containers stopped" -ForegroundColor Green

# Build images
Write-Host ""
Write-Host "[4/6] Building Docker images..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Gray
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Images built successfully" -ForegroundColor Green

# Start containers
Write-Host ""
Write-Host "[5/6] Starting containers..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start containers!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Containers started" -ForegroundColor Green

# Wait for services to be healthy
Write-Host ""
Write-Host "[6/6] Waiting for services to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$allHealthy = $false

while ($attempt -lt $maxAttempts -and -not $allHealthy) {
    Start-Sleep -Seconds 2
    $attempt++
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 2>&1
        if ($response.StatusCode -eq 200) {
            $allHealthy = $true
        }
    } catch {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

Write-Host ""
if ($allHealthy) {
    Write-Host "✅ All services are ready!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Services are starting... (may take a bit longer)" -ForegroundColor Yellow
}

# Display container status
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Container Status" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
docker-compose ps

# Display access information
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Access Information" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🌐 API:            http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API Docs:       http://localhost:8000/docs" -ForegroundColor Green
Write-Host "📖 ReDoc:          http://localhost:8000/redoc" -ForegroundColor Green
Write-Host "🏥 Health Check:   http://localhost:8000/health" -ForegroundColor Green
Write-Host "📊 Metrics:        http://localhost:8000/metrics" -ForegroundColor Green
Write-Host ""
Write-Host "💾 Database:       localhost:5432" -ForegroundColor Cyan
Write-Host "   User:           rag_user" -ForegroundColor Gray
Write-Host "   Password:       rag_password" -ForegroundColor Gray
Write-Host "   Database:       rag_db" -ForegroundColor Gray
Write-Host ""
Write-Host "🔄 Redis:          localhost:6379" -ForegroundColor Cyan
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Optional Services" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "To start pgAdmin (database UI), run:" -ForegroundColor Yellow
Write-Host "  docker-compose --profile tools up -d" -ForegroundColor White
Write-Host "  Access at: http://localhost:5050" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Useful Commands" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "View logs:         .\docker-logs.ps1" -ForegroundColor White
Write-Host "Stop containers:   .\docker-stop.ps1" -ForegroundColor White
Write-Host "Reset everything:  .\docker-reset.ps1" -ForegroundColor White
Write-Host "Enter container:   .\docker-shell.ps1 <service>" -ForegroundColor White
Write-Host ""
Write-Host "🎉 RAG Pipeline is ready to use!" -ForegroundColor Green
Write-Host ""

# Ask if user wants to open API docs
$openDocs = Read-Host "Open API documentation in browser? (Y/n)"
if ($openDocs -eq "" -or $openDocs -eq "Y" -or $openDocs -eq "y") {
    Start-Process "http://localhost:8000/docs"
}

