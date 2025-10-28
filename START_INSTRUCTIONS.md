# 🎯 RAG Pipeline - Docker Startup Instructions

## ✅ Prerequisites Check

Before starting, ensure:
- [ ] Docker Desktop is installed
- [ ] Docker Desktop is running (check system tray)
- [ ] Ports 8000, 5432, 6379 are available

---

## 🚀 Manual Commands to Start

### Method 1: Automated Script (Easiest)

```powershell
# Navigate to project directory
cd "D:\RAG pipeline"

# Run startup script
.\START_DOCKER.ps1
```

### Method 2: Manual Docker Commands

```powershell
# Navigate to project directory
cd "D:\RAG pipeline"

# Create uploads directory
New-Item -ItemType Directory -Path ".\uploads" -Force

# Build and start all services
docker-compose up --build -d

# Wait 30 seconds for services to start
Start-Sleep -Seconds 30

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

---

## 🌐 Access the Application

### On Your Computer (Localhost)

1. **API Documentation (Swagger UI)**
   ```
   http://localhost:8000/docs
   ```

2. **Alternative API Docs (ReDoc)**
   ```
   http://localhost:8000/redoc
   ```

3. **Health Check**
   ```
   http://localhost:8000/health
   ```

4. **Root Endpoint**
   ```
   http://localhost:8000/
   ```

### From Other Devices (Network Access)

1. **Find your IP address:**
   ```powershell
   ipconfig
   ```
   Look for "IPv4 Address" (e.g., 192.168.1.100)

2. **Share these URLs:**
   ```
   http://YOUR_IP:8000/docs
   http://YOUR_IP:8000/health
   ```

   Example:
   ```
   http://192.168.1.100:8000/docs
   http://192.168.1.100:8000/health
   ```

---

## 📊 Verify Everything is Running

### Check Container Status
```powershell
docker-compose ps
```

Expected output:
```
NAME          IMAGE              STATUS          PORTS
rag-app       rag-pipeline-app   Up             0.0.0.0:8000->8000/tcp
rag-postgres  postgres:15-alpine Up             0.0.0.0:5432->5432/tcp
rag-redis     redis:7-alpine     Up             0.0.0.0:6379->6379/tcp
```

### Test Health Endpoint
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

Expected response:
```json
{
  "status": "healthy",
  "service": "RAG Pipeline",
  "version": "0.1.0",
  "environment": "development"
}
```

---

## 📤 Upload Your First Document

### Using Swagger UI (Recommended)

1. Open http://localhost:8000/docs
2. Scroll to `POST /v1/documents/upload`
3. Click **"Try it out"**
4. Click **"Add file"** button
5. Select your PDF/DOCX/TXT files (max 20 files, 50MB each)
6. Click **"Execute"**
7. View the response with upload status

### Using PowerShell
```powershell
# Single file
$file = @{Name='files'; FileName='document.pdf'; FilePath='C:\path\to\document.pdf'}
Invoke-RestMethod -Uri "http://localhost:8000/v1/documents/upload" -Method Post -Form $file

# Multiple files
$files = @(
    @{Name='files'; FileName='doc1.pdf'; FilePath='C:\docs\doc1.pdf'},
    @{Name='files'; FileName='doc2.docx'; FilePath='C:\docs\doc2.docx'}
)
Invoke-RestMethod -Uri "http://localhost:8000/v1/documents/upload" -Method Post -Form $files
```

---

## 🛑 Stop the Application

### Method 1: Using Script
```powershell
.\STOP_DOCKER.ps1
```

### Method 2: Manual Command
```powershell
docker-compose down
```

---

## 🔄 Restart the Application

```powershell
# Restart all services
docker-compose restart

# Or restart just the app
docker-compose restart app
```

---

## 📝 View Logs

```powershell
# All services
docker-compose logs -f

# Just the application
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
```

---

## 🔥 Troubleshooting

### Problem: Docker Desktop not running
```powershell
# Start Docker Desktop from Start Menu
# Wait for it to fully start (whale icon in system tray)
```

### Problem: Port 8000 already in use
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with process ID)
taskkill /PID <PID> /F

# Or stop Docker and restart
docker-compose down
.\START_DOCKER.ps1
```

### Problem: Can't access from other devices
```powershell
# Allow through Windows Firewall (Run as Administrator)
New-NetFirewallRule -DisplayName "RAG Pipeline API" `
    -Direction Inbound `
    -LocalPort 8000 `
    -Protocol TCP `
    -Action Allow
```

### Problem: Services not starting
```powershell
# View detailed logs
docker-compose logs

# Clean restart
docker-compose down
docker-compose up --build -d
```

### Problem: Database connection errors
```powershell
# Wait for PostgreSQL to fully start
Start-Sleep -Seconds 30

# Check PostgreSQL logs
docker-compose logs postgres

# Restart services
docker-compose restart
```

---

## 🧹 Clean Up (Remove Everything)

### Remove containers and networks
```powershell
docker-compose down
```

### Remove containers, networks, and volumes (deletes all data)
```powershell
docker-compose down -v
```

### Remove everything including images
```powershell
docker-compose down -v --rmi all
docker system prune -af --volumes
```

---

## 📱 Sharing with Team Members

### Step 1: Start the application
```powershell
.\START_DOCKER.ps1
```

### Step 2: Find your IP address
```powershell
ipconfig
```
Look for IPv4 Address (e.g., 192.168.1.100)

### Step 3: Share the URL
Send this to your team:
```
API Docs: http://YOUR_IP:8000/docs
Health:   http://YOUR_IP:8000/health
```

### Step 4: Ensure firewall allows access
```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "RAG Pipeline API" `
    -Direction Inbound `
    -LocalPort 8000 `
    -Protocol TCP `
    -Action Allow
```

---

## ✅ Success Checklist

- [ ] Docker Desktop is running
- [ ] Ran `.\START_DOCKER.ps1` or `docker-compose up --build -d`
- [ ] All 3 containers show "Up" status (`docker-compose ps`)
- [ ] Can access http://localhost:8000/docs
- [ ] Health check returns `{"status": "healthy"}`
- [ ] Can upload a test document
- [ ] (Optional) Other devices can access via network IP

---

## 🎉 You're All Set!

The RAG Pipeline is now running and accessible at:
- **Local**: http://localhost:8000/docs
- **Network**: http://YOUR_IP:8000/docs

Start uploading documents and testing the Phase 2 features!

---

## 📚 Additional Resources

- **Full Docker Guide**: See `DOCKER_GUIDE.md`
- **Quick Start**: See `DOCKER_QUICK_START.md`
- **Phase 2 Details**: See `PHASE_2_COMPLETE.md`
- **API Documentation**: http://localhost:8000/docs (when running)

