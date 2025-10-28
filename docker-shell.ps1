# ==========================================
# Docker Shell Script
# ==========================================
# Open a shell inside a running container
# Usage: .\docker-shell.ps1 <service>
# Examples:
#   .\docker-shell.ps1 app       # Shell into API container
#   .\docker-shell.ps1 postgres  # Shell into database

param(
    [Parameter(Mandatory=$false)]
    [string]$Service = ""
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  RAG Pipeline - Docker Shell" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker is not running!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Docker is not installed or not accessible!" -ForegroundColor Red
    exit 1
}

# Check if containers are running
$containers = docker-compose ps -q
if (-not $containers) {
    Write-Host "ℹ️  No containers are currently running" -ForegroundColor Cyan
    Write-Host "Start containers with: .\docker-start.ps1" -ForegroundColor Yellow
    exit 0
}

# If no service specified, show available services
if (-not $Service) {
    Write-Host "Available services:" -ForegroundColor Cyan
    Write-Host ""
    docker-compose ps --services
    Write-Host ""
    $Service = Read-Host "Enter service name"
}

# Validate service exists
$validServices = docker-compose ps --services
if (-not ($validServices -contains $Service)) {
    Write-Host "❌ Service '$Service' not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available services:" -ForegroundColor Yellow
    docker-compose ps --services
    exit 1
}

# Check if service is running
$runningService = docker-compose ps $Service -q
if (-not $runningService) {
    Write-Host "❌ Service '$Service' is not running!" -ForegroundColor Red
    exit 1
}

Write-Host "Opening shell in '$Service' container..." -ForegroundColor Green
Write-Host "Type 'exit' to return to your terminal" -ForegroundColor Gray
Write-Host ""

# Determine shell command based on service
switch ($Service) {
    "postgres" {
        Write-Host "Connecting to PostgreSQL..." -ForegroundColor Yellow
        docker-compose exec $Service psql -U rag_user -d rag_db
    }
    "redis" {
        Write-Host "Connecting to Redis CLI..." -ForegroundColor Yellow
        docker-compose exec $Service redis-cli
    }
    default {
        Write-Host "Opening bash shell..." -ForegroundColor Yellow
        docker-compose exec $Service bash
    }
}

Write-Host ""
Write-Host "Exited from $Service" -ForegroundColor Green

