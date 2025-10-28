# ==========================================
# Docker Stop Script
# ==========================================
# Stops all Docker containers for the RAG Pipeline
# Usage: .\docker-stop.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  RAG Pipeline - Docker Stop Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
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
Write-Host "Checking for running containers..." -ForegroundColor Yellow
$containers = docker-compose ps -q
if (-not $containers) {
    Write-Host "ℹ️  No containers are currently running" -ForegroundColor Cyan
    exit 0
}

# Display current status
Write-Host ""
Write-Host "Current containers:" -ForegroundColor Cyan
docker-compose ps
Write-Host ""

# Confirm stop
$confirm = Read-Host "Stop all containers? (Y/n)"
if ($confirm -ne "" -and $confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Stopping containers..." -ForegroundColor Yellow
docker-compose stop

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All containers stopped successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some containers may not have stopped properly" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Container status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "To start containers:  .\docker-start.ps1" -ForegroundColor White
Write-Host "To remove containers: docker-compose down" -ForegroundColor White
Write-Host "To reset everything:  .\docker-reset.ps1" -ForegroundColor White
Write-Host ""

