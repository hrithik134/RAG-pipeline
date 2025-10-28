# Quick Endpoint Testing Script (requires app to be running)
# Run this AFTER starting the application

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   Testing FastAPI Endpoints" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Root endpoint
Write-Host "Test 1: Root Endpoint (GET /)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method Get
    Write-Host "✅ Success" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "---------------------------------------------------" -ForegroundColor Gray
Write-Host ""

# Test 2: Health check
Write-Host "Test 2: Health Check (GET /health)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "✅ Success" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "---------------------------------------------------" -ForegroundColor Gray
Write-Host ""

# Test 3: OpenAPI schema
Write-Host "Test 3: OpenAPI Schema (GET /openapi.json)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/openapi.json" -Method Get
    Write-Host "✅ Success" -ForegroundColor Green
    Write-Host "Schema contains $($response.paths.Count) endpoint(s)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   Summary" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If all tests passed, your FastAPI app is working!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Open in browser:" -ForegroundColor Yellow
Write-Host "   Swagger UI: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   ReDoc:      http://localhost:8000/redoc" -ForegroundColor White
Write-Host ""

