# ==========================================
# Docker Reset Script
# ==========================================
# Completely resets the Docker environment
# WARNING: This will delete all data!
# Usage: .\docker-reset.ps1

Write-Host "================================================" -ForegroundColor Red
Write-Host "  RAG Pipeline - Docker Reset Script" -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red
Write-Host ""
Write-Host "⚠️  WARNING: This will DELETE ALL data!" -ForegroundColor Red
Write-Host "   - All containers will be removed" -ForegroundColor Yellow
Write-Host "   - All volumes will be deleted" -ForegroundColor Yellow
Write-Host "   - All networks will be removed" -ForegroundColor Yellow
Write-Host "   - Database data will be lost" -ForegroundColor Yellow
Write-Host "   - Uploaded files will remain (in ./uploads)" -ForegroundColor Yellow
Write-Host ""

# Confirm reset
$confirm = Read-Host "Are you sure you want to continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Cancelled" -ForegroundColor Green
    exit 0
}

Write-Host ""
$finalConfirm = Read-Host "Type 'DELETE' to confirm"
if ($finalConfirm -ne "DELETE") {
    Write-Host "Cancelled" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Starting Reset Process" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Stop all containers
Write-Host ""
Write-Host "[1/4] Stopping containers..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null
Write-Host "✅ Containers stopped" -ForegroundColor Green

# Remove containers and networks
Write-Host ""
Write-Host "[2/4] Removing containers and networks..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>&1 | Out-Null
Write-Host "✅ Containers and networks removed" -ForegroundColor Green

# Remove volumes
Write-Host ""
Write-Host "[3/4] Removing volumes..." -ForegroundColor Yellow
docker-compose down -v 2>&1 | Out-Null
docker volume rm rag_postgres_data 2>&1 | Out-Null
docker volume rm rag_redis_data 2>&1 | Out-Null
docker volume rm rag_pgadmin_data 2>&1 | Out-Null
Write-Host "✅ Volumes removed" -ForegroundColor Green

# Remove unused images (optional)
Write-Host ""
Write-Host "[4/4] Cleaning up Docker..." -ForegroundColor Yellow
docker system prune -f 2>&1 | Out-Null
Write-Host "✅ Cleanup complete" -ForegroundColor Green

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Reset Complete" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ All Docker resources have been removed" -ForegroundColor Green
Write-Host ""
Write-Host "To start fresh:" -ForegroundColor Cyan
Write-Host "  .\docker-start.ps1" -ForegroundColor White
Write-Host ""

