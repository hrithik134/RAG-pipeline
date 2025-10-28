# Phase 6 UI Access Guide

## 🎯 Quick Access - Development Mode

### **Main UI Pages**

#### 1. **Swagger UI** (Interactive API Documentation)
```powershell
# Method 1: PowerShell command
Start-Process http://localhost:8000/docs

# Method 2: Copy to browser
# URL: http://localhost:8000/docs
```
**Features:** Interactive API testing, request/response examples

---

#### 2. **ReDoc** (Alternative API Documentation)
```powershell
Start-Process http://localhost:8000/redoc
```
**URL:** http://localhost:8000/redoc  
**Features:** Clean, readable API documentation

---

#### 3. **Health Check** (Service Status)
```powershell
Start-Process http://localhost:8000/health
```
**URL:** http://localhost:8000/health  
**Features:** Shows service status, database, Redis, Pinecone health

---

#### 4. **Metrics** (System Statistics)
```powershell
Start-Process http://localhost:8000/metrics
```
**URL:** http://localhost:8000/metrics  
**Features:** System metrics, document counts, query stats

---

#### 5. **Root Endpoint** (API Information)
```powershell
Start-Process http://localhost:8000/
```
**URL:** http://localhost:8000/  
**Features:** API overview, version info, available endpoints

---

## 🚀 One-Command: Open All Pages

```powershell
Start-Process http://localhost:8000/docs
Start-Process http://localhost:8000/redoc
Start-Process http://localhost:8000/health
Start-Process http://localhost:8000/metrics
Start-Process http://localhost:8000/
```

---

## 📋 Other Useful Endpoints

### **OpenAPI JSON Schema**
```powershell
Start-Process http://localhost:8000/openapi.json
```

### **Query Documents**
```powershell
# Via browser: POST to http://localhost:8000/v1/query
# Or test via Swagger UI
Start-Process http://localhost:8000/docs
```

### **Upload Documents**
```powershell
# Via browser: POST to http://localhost:8000/v1/documents/upload
# Or use Swagger UI
Start-Process http://localhost:8000/docs
```

---

## 🧪 Testing via Browser

### 1. Open Swagger UI
```powershell
Start-Process http://localhost:8000/docs
```

### 2. Try These Endpoints

#### Test Health Check
1. Click on **`GET /health`**
2. Click **"Try it out"**
3. Click **"Execute"**
4. See response: `{"status": "healthy", ...}`

#### Test Metrics
1. Click on **`GET /metrics`**
2. Click **"Try it out"**
3. Click **"Execute"**
4. See system statistics

#### Test Query
1. Click on **`POST /v1/query`**
2. Click **"Try it out"**
3. Enter query: `{"query": "What is AI?"}`
4. Click **"Execute"**
5. Get response with citations

#### Test Upload
1. Click on **`POST /v1/documents/upload`**
2. Click **"Try it out"**
3. Click **"Choose File"** and select a PDF
4. Click **"Execute"**
5. See upload progress

---

## 🔧 Alternative Access Methods

### Using curl (Command Line)
```powershell
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# Get all documents
curl http://localhost:8000/v1/documents
```

### Using Invoke-WebRequest (PowerShell)
```powershell
# Health check
Invoke-WebRequest http://localhost:8000/health

# Metrics
Invoke-WebRequest http://localhost:8000/metrics

# Format as JSON
(Invoke-WebRequest http://localhost:8000/health).Content | ConvertFrom-Json
```

---

## 📊 Production Mode Access

If running production mode (port 8001):

### All URLs shift to port 8001:
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **Health:** http://localhost:8001/health
- **Metrics:** http://localhost:8001/metrics
- **Root:** http://localhost:8001/

### Commands:
```powershell
Start-Process http://localhost:8001/docs
Start-Process http://localhost:8001/redoc
Start-Process http://localhost:8001/health
Start-Process http://localhost:8001/metrics
```

---

## 🎯 Recommended: Start Here

### Best Page to Start Testing:
**http://localhost:8000/docs** - Swagger UI

**Why?**
- ✅ Interactive API testing
- ✅ See all endpoints
- ✅ Try requests directly
- ✅ View schemas
- ✅ Test with real data

### Quick Test:
```powershell
# Open Swagger UI
Start-Process http://localhost:8000/docs

# Try health check first
Start-Process http://localhost:8000/health

# View all available endpoints
Start-Process http://localhost:8000/
```

---

## 📝 Summary of All URLs

### Development Mode (Port 8000)
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics
- **Root:** http://localhost:8000/
- **OpenAPI:** http://localhost:8000/openapi.json

### Production Mode (Port 8001)
- **API Docs:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **Health:** http://localhost:8001/health
- **Metrics:** http://localhost:8001/metrics
- **Root:** http://localhost:8001/

---

## 🎉 Ready to Test!

**Copy and paste these in PowerShell:**

```powershell
# Open main API docs
Start-Process http://localhost:8000/docs

# Or open all at once
Start-Process http://localhost:8000/docs
Start-Process http://localhost:8000/health
Start-Process http://localhost:8000/metrics
```

**All Phase 6 UI pages are accessible and ready for testing!** 🚀

