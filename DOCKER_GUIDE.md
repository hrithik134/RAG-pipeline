# 🐳 Docker Deployment Guide

## Quick Start

### Option 1: Automated Script (Recommended)
```powershell
.\START_DOCKER.ps1
```

### Option 2: Manual Commands
```powershell
# Build and start all services
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

---

## 📋 Prerequisites

1. **Docker Desktop** installed and running
   - Download: https://www.docker.com/products/docker-desktop

2. **Ports Available**
   - `8000` - FastAPI application
   - `5432` - PostgreSQL database
   - `6379` - Redis cache

---

## 🚀 Starting the Application

### Step 1: Start Docker Desktop
Make sure Docker Desktop is running on your computer.

### Step 2: Run the Startup Script
```powershell
.\START_DOCKER.ps1
```

This script will:
- ✅ Check if Docker is running
- ✅ Create necessary directories
- ✅ Stop any existing containers
- ✅ Build the application image
- ✅ Start all services (PostgreSQL, Redis, FastAPI)
- ✅ Show access URLs
- ✅ Check application health

### Step 3: Wait for Services
First startup takes 2-5 minutes to:
- Download base images
- Install dependencies
- Initialize database

---

## 🌐 Accessing the Application

### Local Access (Your Computer)
- **API Docs (Swagger UI)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root Endpoint**: http://localhost:8000/

### Network Access (Other Devices)
Replace `<YOUR_IP>` with your computer's IP address (shown by the script):
- **API Docs**: http://<YOUR_IP>:8000/docs
- **Health Check**: http://<YOUR_IP>:8000/health

**Example**: If your IP is `192.168.1.100`:
- http://192.168.1.100:8000/docs

### Finding Your IP Address
```powershell
# PowerShell
ipconfig

# Look for "IPv4 Address" under your network adapter
# Usually starts with 192.168.x.x or 10.0.x.x
```

---

## 📊 Managing Services

### View Container Status
```powershell
docker-compose ps
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 app
```

### Restart Services
```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart app
```

### Stop Services
```powershell
# Using script
.\STOP_DOCKER.ps1

# Manual
docker-compose down
```

### Stop and Remove Everything (Including Data)
```powershell
docker-compose down -v
```
⚠️ **Warning**: This deletes all uploaded documents and database data!

---

## 🔧 Troubleshooting

### Problem: "Docker is not running"
**Solution**: Start Docker Desktop and wait for it to fully initialize.

### Problem: "Port 8000 is already in use"
**Solution**: Stop any other service using port 8000
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with the number from above)
taskkill /PID <PID> /F
```

### Problem: "Cannot connect to database"
**Solution**: Wait for PostgreSQL to fully start
```powershell
# Check PostgreSQL logs
docker-compose logs postgres

# Restart if needed
docker-compose restart postgres app
```

### Problem: Application not responding
**Solution**: Check application logs
```powershell
docker-compose logs -f app
```

### Problem: Build fails
**Solution**: Clean Docker cache and rebuild
```powershell
docker-compose down
docker system prune -f
docker-compose up --build -d
```

---

## 📁 File Structure in Docker

```
/app/                          # Application root in container
├── app/                       # Python application code
│   ├── main.py               # FastAPI app
│   ├── models/               # Database models
│   ├── routers/              # API endpoints
│   ├── services/             # Business logic
│   └── utils/                # Utilities
├── uploads/                  # Uploaded documents (mounted volume)
├── requirements.txt          # Python dependencies
└── alembic/                  # Database migrations
```

---

## 🔄 Database Migrations

### Run Migrations
```powershell
# Access app container
docker-compose exec app bash

# Inside container
alembic upgrade head

# Exit container
exit
```

### Create New Migration
```powershell
docker-compose exec app bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
exit
```

---

## 📤 Uploading Documents

### Using Swagger UI (Recommended)
1. Open http://localhost:8000/docs
2. Find `POST /v1/documents/upload`
3. Click "Try it out"
4. Click "Add file" and select your documents
5. Click "Execute"

### Using PowerShell
```powershell
$files = @(
    @{Name='files'; FileName='doc1.pdf'; FilePath='C:\path\to\doc1.pdf'},
    @{Name='files'; FileName='doc2.docx'; FilePath='C:\path\to\doc2.docx'}
)

Invoke-RestMethod -Uri "http://localhost:8000/v1/documents/upload" `
    -Method Post `
    -Form $files
```

### Using curl
```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@document1.pdf" \
  -F "files=@document2.docx"
```

---

## 🔐 Network Security

### Allow Access Through Windows Firewall

If other devices can't connect:

1. Open **Windows Defender Firewall**
2. Click **Advanced settings**
3. Click **Inbound Rules** → **New Rule**
4. Select **Port** → Next
5. Select **TCP** and enter `8000` → Next
6. Select **Allow the connection** → Next
7. Check all profiles → Next
8. Name: "RAG Pipeline API" → Finish

### Or use PowerShell (Run as Administrator):
```powershell
New-NetFirewallRule -DisplayName "RAG Pipeline API" `
    -Direction Inbound `
    -LocalPort 8000 `
    -Protocol TCP `
    -Action Allow
```

---

## 📊 Container Resource Usage

### View Resource Usage
```powershell
docker stats
```

### Recommended Resources
- **CPU**: 2+ cores
- **Memory**: 4GB minimum, 8GB recommended
- **Disk**: 10GB free space

### Configure Docker Resources
1. Open Docker Desktop
2. Settings → Resources
3. Adjust CPU, Memory, Disk limits
4. Click "Apply & Restart"

---

## 🧹 Cleanup

### Remove Stopped Containers
```powershell
docker-compose down
```

### Remove Images
```powershell
docker-compose down --rmi all
```

### Remove Everything (Fresh Start)
```powershell
docker-compose down -v --rmi all
docker system prune -af --volumes
```

---

## 📝 Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - APP_ENV=development          # development/production
  - DEBUG=true                   # true/false
  - MAX_DOCUMENTS_PER_UPLOAD=20  # Max files per batch
  - MAX_PAGES_PER_DOCUMENT=1000  # Max pages per document
  - MAX_FILE_SIZE_MB=50          # Max file size
  - CHUNK_SIZE=1000              # Tokens per chunk
  - CHUNK_OVERLAP=150            # Token overlap
```

After changes:
```powershell
docker-compose down
docker-compose up -d
```

---

## 🎯 Production Deployment

For production use:

1. **Change passwords** in `docker-compose.yml`
2. **Set `DEBUG=false`**
3. **Set `APP_ENV=production`**
4. **Use HTTPS** (add nginx reverse proxy)
5. **Set up backups** for PostgreSQL data
6. **Monitor logs** regularly

---

## 📞 Quick Reference

| Command | Description |
|---------|-------------|
| `.\START_DOCKER.ps1` | Start everything |
| `.\STOP_DOCKER.ps1` | Stop everything |
| `docker-compose ps` | Check status |
| `docker-compose logs -f app` | View logs |
| `docker-compose restart app` | Restart app |
| `docker-compose down` | Stop services |
| `docker-compose up -d` | Start services |

---

## ✅ Success Checklist

- [ ] Docker Desktop is running
- [ ] Ran `.\START_DOCKER.ps1`
- [ ] All containers show "Up" status
- [ ] Can access http://localhost:8000/docs
- [ ] Health check returns "healthy"
- [ ] Can upload a test document
- [ ] Other devices can access via network IP

---

**Your RAG Pipeline is now running in Docker! 🎉**

Access the API documentation at: **http://localhost:8000/docs**

