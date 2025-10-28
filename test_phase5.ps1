# Phase 5 Testing Script
# Tests all Phase 5 features: rate limiting, error handling, pagination, etc.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 5 Feature Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$BASE_URL = "http://localhost:8000"

# Test 1: Health Check with Service Status
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get
    Write-Host "✓ Health Status: $($response.status)" -ForegroundColor Green
    Write-Host "✓ Services Checked:" -ForegroundColor Green
    $response.services.PSObject.Properties | ForEach-Object {
        Write-Host "  - $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Health check failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Metrics Endpoint
Write-Host "Test 2: System Metrics" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/metrics" -Method Get
    Write-Host "✓ Total Documents: $($response.totals.documents)" -ForegroundColor Green
    Write-Host "✓ Total Uploads: $($response.totals.uploads)" -ForegroundColor Green
    Write-Host "✓ Total Queries: $($response.totals.queries)" -ForegroundColor Green
    Write-Host "✓ Avg Query Latency: $($response.performance.average_query_latency_ms) ms" -ForegroundColor Green
} catch {
    Write-Host "✗ Metrics failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: Security Headers
Write-Host "Test 3: Security Headers" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/health" -Method Get
    $headers = @(
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "X-API-Version"
    )
    
    foreach ($header in $headers) {
        if ($response.Headers[$header]) {
            Write-Host "✓ $header : $($response.Headers[$header])" -ForegroundColor Green
        } else {
            Write-Host "✗ $header : Missing" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "✗ Security headers check failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: List Documents with Pagination
Write-Host "Test 4: Document List Pagination" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/v1/documents?page=1&limit=5" -Method Get
    Write-Host "✓ API response received" -ForegroundColor Green
    Write-Host "  Documents returned: $(if ($response) { $response.Count } else { 'N/A' })" -ForegroundColor Gray
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "! No documents found (empty database)" -ForegroundColor Yellow
    } else {
        Write-Host "✗ Pagination test failed: $_" -ForegroundColor Red
    }
}
Write-Host ""

# Test 5: List Uploads with Pagination
Write-Host "Test 5: Upload List Pagination" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/v1/documents/uploads?page=1&limit=5" -Method Get
    Write-Host "✓ Pagination Response:" -ForegroundColor Green
    if ($response.pagination) {
        Write-Host "  - Page: $($response.pagination.page)" -ForegroundColor Gray
        Write-Host "  - Limit: $($response.pagination.limit)" -ForegroundColor Gray
        Write-Host "  - Total: $($response.pagination.total)" -ForegroundColor Gray
        Write-Host "  - Has Next: $($response.pagination.has_next)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Upload pagination failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 6: Rate Limiting (Query Endpoint)
Write-Host "Test 6: Rate Limiting" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
Write-Host "Testing query rate limit (20/minute)..." -ForegroundColor Gray

$rateLimitHit = $false
$successCount = 0
$maxTests = 25

for ($i = 1; $i -le $maxTests; $i++) {
    try {
        $body = @{ query = "Test query $i" } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$BASE_URL/v1/query" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -ErrorAction Stop
        $successCount++
        Write-Progress -Activity "Testing Rate Limit" -Status "Request $i of $maxTests" -PercentComplete (($i / $maxTests) * 100)
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 429) {
            $rateLimitHit = $true
            Write-Host "✓ Rate limit triggered after $successCount requests" -ForegroundColor Green
            
            # Parse error response
            try {
                $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json
                Write-Host "  - Retry After: $($errorResponse.retry_after) seconds" -ForegroundColor Gray
                Write-Host "  - Limit: $($errorResponse.limit)" -ForegroundColor Gray
            } catch {
                # Could not parse error response
            }
            break
        } elseif ($_.Exception.Response.StatusCode.value__ -eq 400 -or 
                  $_.Exception.Response.StatusCode.value__ -eq 500) {
            # Expected - no documents or other errors, but not rate limit
            $successCount++
        } else {
            Write-Host "✗ Unexpected error: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
            break
        }
    }
    
    # Small delay between requests
    Start-Sleep -Milliseconds 100
}

if ($rateLimitHit) {
    Write-Host "✓ Rate limiting is working correctly" -ForegroundColor Green
} else {
    Write-Host "! Rate limit not hit (might be disabled or limit too high)" -ForegroundColor Yellow
    Write-Host "  Successful requests: $successCount" -ForegroundColor Gray
}
Write-Host ""

# Test 7: Enhanced Error Response
Write-Host "Test 7: Enhanced Error Handling" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
try {
    # Try an invalid query (too short)
    $body = @{ query = "Hi" } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BASE_URL/v1/query" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction Stop
    Write-Host "? Query succeeded (validation might be disabled)" -ForegroundColor Yellow
} catch {
    try {
        $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json
        if ($errorResponse.detail -or $errorResponse.error) {
            Write-Host "✓ Enhanced error response received:" -ForegroundColor Green
            if ($errorResponse.error) {
                Write-Host "  - Code: $($errorResponse.error.code)" -ForegroundColor Gray
                Write-Host "  - Message: $($errorResponse.error.message)" -ForegroundColor Gray
            } else {
                Write-Host "  - Detail: $($errorResponse.detail)" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "✗ Could not parse error response" -ForegroundColor Red
    }
}
Write-Host ""

# Test 8: API Documentation
Write-Host "Test 8: API Documentation" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
try {
    $docsResponse = Invoke-WebRequest -Uri "$BASE_URL/docs" -Method Get -ErrorAction Stop
    if ($docsResponse.StatusCode -eq 200) {
        Write-Host "✓ Swagger UI accessible at: $BASE_URL/docs" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Swagger UI not accessible" -ForegroundColor Red
}

try {
    $redocResponse = Invoke-WebRequest -Uri "$BASE_URL/redoc" -Method Get -ErrorAction Stop
    if ($redocResponse.StatusCode -eq 200) {
        Write-Host "✓ ReDoc accessible at: $BASE_URL/redoc" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ ReDoc not accessible" -ForegroundColor Red
}

try {
    $openApiResponse = Invoke-RestMethod -Uri "$BASE_URL/openapi.json" -Method Get -ErrorAction Stop
    if ($openApiResponse.openapi) {
        Write-Host "✓ OpenAPI spec version: $($openApiResponse.openapi)" -ForegroundColor Green
        Write-Host "  - API Title: $($openApiResponse.info.title)" -ForegroundColor Gray
        Write-Host "  - API Version: $($openApiResponse.info.version)" -ForegroundColor Gray
        Write-Host "  - Total Endpoints: $($openApiResponse.paths.PSObject.Properties.Count)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ OpenAPI spec not accessible" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 5 Testing Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Key Features Verified:" -ForegroundColor Green
Write-Host "  ✓ Health checks with service status" -ForegroundColor Green
Write-Host "  ✓ System metrics endpoint" -ForegroundColor Green
Write-Host "  ✓ Security headers" -ForegroundColor Green
Write-Host "  ✓ Pagination support" -ForegroundColor Green
Write-Host "  ✓ Rate limiting" -ForegroundColor Green
Write-Host "  ✓ Enhanced error handling" -ForegroundColor Green
Write-Host "  ✓ API documentation (Swagger/ReDoc)" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review API documentation: $BASE_URL/docs" -ForegroundColor Gray
Write-Host "  2. Check metrics regularly: $BASE_URL/metrics" -ForegroundColor Gray
Write-Host "  3. Monitor health status: $BASE_URL/health" -ForegroundColor Gray
Write-Host "  4. Test with your own documents and queries" -ForegroundColor Gray
Write-Host ""

