# ==========================================
# Docker Logs Script
# ==========================================
# View logs from Docker containers
# Usage: .\docker-logs.ps1 [service] [options]
# Examples:
#   .\docker-logs.ps1           # Show all logs
#   .\docker-logs.ps1 app       # Show API logs
#   .\docker-logs.ps1 postgres  # Show database logs
#   .\docker-logs.ps1 app -f    # Follow API logs (live)

param(
    [string]$Service = "",
    [switch]$Follow = $false,
    [int]$Tail = 100
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  RAG Pipeline - Docker Logs" -ForegroundColor Cyan
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

# Build docker-compose logs command
$logCommand = "docker-compose logs --tail=$Tail"

if ($Follow) {
    $logCommand += " -f"
}

if ($Service) {
    $logCommand += " $Service"
    Write-Host "Viewing logs for: $Service" -ForegroundColor Green
} else {
    Write-Host "Viewing logs for: All services" -ForegroundColor Green
}

if ($Follow) {
    Write-Host "Following logs (Ctrl+C to stop)..." -ForegroundColor Yellow
} else {
    Write-Host "Showing last $Tail lines..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Execute logs command
Invoke-Expression $logCommand

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Available Services" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "app        - FastAPI application" -ForegroundColor White
Write-Host "postgres   - PostgreSQL database" -ForegroundColor White
Write-Host "redis      - Redis cache" -ForegroundColor White
Write-Host "migrate    - Database migrations" -ForegroundColor White
Write-Host "pgadmin    - pgAdmin (if running)" -ForegroundColor White
Write-Host ""
Write-Host "Examples:" -ForegroundColor Cyan
Write-Host "  .\docker-logs.ps1 app -Follow" -ForegroundColor Gray
Write-Host "  .\docker-logs.ps1 postgres" -ForegroundColor Gray
Write-Host "  .\docker-logs.ps1 -Tail 50" -ForegroundColor Gray
Write-Host ""

