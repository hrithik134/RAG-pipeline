# 🚀 Docker Quick Start - 3 Steps

## Step 1: Start Docker Desktop
Make sure Docker Desktop is running.

## Step 2: Run Startup Script
```powershell
.\START_DOCKER.ps1
```

## Step 3: Access the Application
- **Your Computer**: http://localhost:8000/docs
- **Other Devices**: http://YOUR_IP:8000/docs

Replace `YOUR_IP` with the IP address shown by the script.

---

## 📱 Access URLs

### API Documentation (Swagger UI)
```
Local:   http://localhost:8000/docs
Network: http://YOUR_IP:8000/docs
```

### Health Check
```
Local:   http://localhost:8000/health
Network: http://YOUR_IP:8000/health
```

---

## 🛑 Stop Services
```powershell
.\STOP_DOCKER.ps1
```

Or:
```powershell
docker-compose down
```

---

## 📊 View Logs
```powershell
docker-compose logs -f app
```

---

## 🔄 Restart Services
```powershell
docker-compose restart
```

---

## ✅ Verify Everything Works

1. Open http://localhost:8000/docs
2. Try the `GET /health` endpoint
3. Should return:
```json
{
  "status": "healthy",
  "service": "RAG Pipeline",
  "version": "0.1.0",
  "environment": "development"
}
```

---

## 🌐 Share with Others

1. Find your IP address:
```powershell
ipconfig
```

2. Share this URL with others on your network:
```
http://YOUR_IP:8000/docs
```

3. They can now access the API from their devices!

---

## 📤 Upload Documents

1. Go to http://localhost:8000/docs
2. Find `POST /v1/documents/upload`
3. Click "Try it out"
4. Click "Add file" and select documents
5. Click "Execute"

---

## 🆘 Problems?

### Can't access from other devices?
```powershell
# Allow through firewall (Run as Administrator)
New-NetFirewallRule -DisplayName "RAG Pipeline API" `
    -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### Application not starting?
```powershell
# View logs
docker-compose logs -f app

# Restart
docker-compose restart
```

### Port already in use?
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Stop Docker and try again
docker-compose down
.\START_DOCKER.ps1
```

---

**That's it! Your RAG Pipeline is running! 🎉**

