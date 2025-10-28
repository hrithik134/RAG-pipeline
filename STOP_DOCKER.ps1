# Docker Stop Script for RAG Pipeline

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RAG Pipeline - Stopping Docker Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Stopping containers..." -ForegroundColor Yellow
docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ All services stopped successfully" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Error stopping services" -ForegroundColor Red
    Write-Host ""
}

