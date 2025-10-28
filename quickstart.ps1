# RAG Pipeline - Quick Start Script for Windows
# Run this after installing Python 3.10-3.12 or with Docker

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('docker', 'local')]
    [string]$Mode = 'docker'
)

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   RAG Pipeline - Quick Start" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env file" -ForegroundColor Green
        Write-Host "📝 Please edit .env and add your API keys:" -ForegroundColor Yellow
        Write-Host "   - PINECONE_API_KEY" -ForegroundColor Yellow
        Write-Host "   - OPENAI_API_KEY or GOOGLE_API_KEY" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press Enter after updating .env to continue..." -ForegroundColor Yellow
        Read-Host
    } else {
        Write-Host "❌ .env.example not found!" -ForegroundColor Red
        exit 1
    }
}

if ($Mode -eq 'docker') {
    Write-Host "🐳 Starting with Docker..." -ForegroundColor Cyan
    Write-Host ""
    
    # Check if Docker is running
    try {
        docker ps > $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Docker is not installed or not running." -ForegroundColor Red
        Write-Host "   Download from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✅ Docker is running" -ForegroundColor Green
    Write-Host ""
    
    # Check if docker-compose.yml exists (will be created in Phase 6)
    if (Test-Path "docker-compose.yml") {
        Write-Host "📦 Building and starting services..." -ForegroundColor Cyan
        docker-compose up -d --build
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Services started successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "🔗 Available endpoints:" -ForegroundColor Cyan
            Write-Host "   - Health check: http://localhost:8000/health" -ForegroundColor White
            Write-Host "   - API docs: http://localhost:8000/docs" -ForegroundColor White
            Write-Host ""
            Write-Host "📊 View logs:" -ForegroundColor Cyan
            Write-Host "   docker-compose logs -f" -ForegroundColor White
            Write-Host ""
            Write-Host "🛑 Stop services:" -ForegroundColor Cyan
            Write-Host "   docker-compose down" -ForegroundColor White
        } else {
            Write-Host "❌ Failed to start services" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "⚠️  docker-compose.yml not found (will be created in Phase 6)" -ForegroundColor Yellow
        Write-Host "   For now, building standalone Docker image..." -ForegroundColor Yellow
        Write-Host ""
        
        docker build -t rag-pipeline:latest .
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Docker image built successfully!" -ForegroundColor Green
            Write-Host "   Image name: rag-pipeline:latest" -ForegroundColor White
        } else {
            Write-Host "❌ Failed to build Docker image" -ForegroundColor Red
            exit 1
        }
    }
    
} elseif ($Mode -eq 'local') {
    Write-Host "🐍 Starting with local Python..." -ForegroundColor Cyan
    Write-Host ""
    
    # Check Python version
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "Found: $pythonVersion" -ForegroundColor Green
        
        # Extract version number
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            
            if ($major -eq 3 -and $minor -ge 10 -and $minor -le 12) {
                Write-Host "✅ Python version is compatible" -ForegroundColor Green
            } elseif ($major -eq 3 -and $minor -eq 13) {
                Write-Host "⚠️  Python 3.13 detected - some dependencies may not be compatible" -ForegroundColor Yellow
                Write-Host "   Recommend Python 3.10-3.12 or use Docker mode" -ForegroundColor Yellow
            } else {
                Write-Host "⚠️  Python version may not be compatible (recommend 3.10-3.12)" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "❌ Python not found or not in PATH" -ForegroundColor Red
        Write-Host "   Download Python 3.12: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    
    # Check if venv exists
    if (-Not (Test-Path "venv")) {
        Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
        python -m venv venv
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Virtual environment created" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✅ Virtual environment exists" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "📥 Activating virtual environment and installing dependencies..." -ForegroundColor Cyan
    
    # Activate venv and install dependencies
    & ".\venv\Scripts\Activate.ps1"
    
    Write-Host "Upgrading pip..." -ForegroundColor Cyan
    python -m pip install --upgrade pip --quiet
    
    Write-Host "Installing requirements..." -ForegroundColor Cyan
    pip install -r requirements.txt --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        Write-Host "   Try: pip install -r requirements.txt" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    Write-Host "🚀 Starting application..." -ForegroundColor Cyan
    Write-Host ""
    
    # Start the application
    python -m app.main
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan

