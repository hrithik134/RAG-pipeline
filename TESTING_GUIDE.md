# Phase 6 Testing Guide

## ✅ Setup Complete - Ready for Testing!

---

## 🎯 Current Status

### Development Environment (Running)
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Mode:** Uvicorn with hot reload
- **Status:** ✅ Running and healthy

### Production Environment (Available)
- **URL:** http://localhost:8001
- **Mode:** Gunicorn with multiple workers
- **Ports:** 8001 (API), 5433 (Postgres), 6380 (Redis)
- **Start:** `docker-compose -f docker-compose.prod.yml up -d`

---

## 🧪 What to Test

### 1. Development Mode (Currently Running)

#### Test API Endpoints
```powershell
# Health check
curl http://localhost:8000/health

# API docs (in browser)
Start-Process http://localhost:8000/docs

# Root endpoint
curl http://localhost:8000/
```

#### Test Hot Reload
1. Edit a file in `app/` folder
2. Check logs: `.\docker-logs.ps1 app -Follow`
3. You should see: "Detected file change, reloading..."

#### Test Container Features
```powershell
# Check non-root user
docker exec RAG-API id
# Should show: uid=1000(appuser)

# Check Gunicorn is installed
docker exec RAG-API gunicorn --version
# Should show: gunicorn (version 21.2.0)

# View gunicorn config
docker exec RAG-API cat /app/gunicorn_conf.py
```

### 2. Production Mode (Switch When Ready)

#### Start Production Mode
```powershell
# Stop development
docker-compose down

# Start production
docker-compose -f docker-compose.prod.yml up -d

# Wait for startup
Start-Sleep -Seconds 10
```

#### Test Production Endpoints
```powershell
# Health check (note port 8001)
curl http://localhost:8001/health

# API docs
Start-Process http://localhost:8001/docs
```

#### Test Gunicorn Workers
```powershell
# Check for multiple workers
docker exec RAG-API-Prod ps aux | Select-String "gunicorn"

# Should show:
# - 1 master process
# - 4+ worker processes
```

---

## 📊 Quick Tests

### Test 1: API Health
```powershell
Invoke-WebRequest http://localhost:8000/health
# Expected: StatusCode 200
```

### Test 2: Resource Limits
```powershell
docker inspect RAG-API --format '{{.HostConfig.Memory}}'
# Expected: 2147483648 (2GB)

docker inspect RAG-API --format '{{.HostConfig.NanoCpus}}'
# Expected: 2000000000 (2 cores)
```

### Test 3: Container Logs
```powershell
.\docker-logs.ps1 app
# Should show clean startup with no errors
```

### Test 4: Database Connection
```powershell
docker exec RAG-PostgreSQL psql -U rag_user -d rag_db -c "SELECT version();"
# Should show PostgreSQL version
```

### Test 5: Redis Connection
```powershell
docker exec RAG-Redis redis-cli ping
# Expected: PONG
```

---

## 🔍 What Phase 6 Features Were Implemented

### ✅ Production Features
- [x] Gunicorn 21.2.0 installed
- [x] Multi-worker configuration
- [x] Non-root user (appuser)
- [x] Resource limits (CPU & memory)
- [x] Health checks
- [x] Log rotation

### ✅ Docker Optimizations
- [x] Multi-stage builds
- [x] Smaller images (~300MB vs ~900MB)
- [x] Layer caching
- [x] Optimized .dockerignore

### ✅ Developer Tools
- [x] docker-start.ps1 (one-command start)
- [x] docker-stop.ps1 (graceful stop)
- [x] docker-reset.ps1 (complete reset)
- [x] docker-logs.ps1 (log viewer)
- [x] docker-shell.ps1 (container access)

### ✅ Environment Management
- [x] env.example (template)
- [x] env.development (dev settings)
- [x] env.production (prod settings)

### ✅ Services
- [x] PostgreSQL with health checks
- [x] Redis with memory limits
- [x] FastAPI with Gunicorn
- [x] Automatic migrations
- [x] pgAdmin (optional)

---

## 🛠️ Useful Commands

### Container Management
```powershell
# View all containers
docker-compose ps

# View logs (all services)
docker-compose logs

# View logs (specific service)
.\docker-logs.ps1 app

# Follow logs
.\docker-logs.ps1 app -Follow

# Restart a service
docker-compose restart app

# Stop all
docker-compose down

# Complete reset
.\docker-reset.ps1
```

### Debugging
```powershell
# Enter container
.\docker-shell.ps1 app

# Check running processes
docker exec RAG-API ps aux

# Check environment variables
docker exec RAG-API env

# Check disk usage
docker system df
```

### Testing Different Modes
```powershell
# Development (hot reload)
docker-compose up -d

# Production (Gunicorn)
docker-compose -f docker-compose.prod.yml up -d

# With pgAdmin
docker-compose --profile tools up -d
```

---

## 📈 Performance Testing

### Test Load (Development)
```powershell
# Using curl in a loop
for ($i=1; $i -le 100; $i++) {
    curl http://localhost:8000/health
    Write-Host "Request $i"
}
```

### Test Load (Production)
```powershell
# Same test but on production port
for ($i=1; $i -le 100; $i++) {
    curl http://localhost:8001/health
    Write-Host "Request $i"
}
```

### Compare Response Times
```powershell
# Development mode
Measure-Command { Invoke-WebRequest http://localhost:8000/health }

# Production mode (if started)
Measure-Command { Invoke-WebRequest http://localhost:8001/health }
```

---

## ✅ Validation Checklist

### Basic Functionality
- [ ] API responds to health check
- [ ] API docs page loads
- [ ] Containers start successfully
- [ ] No errors in logs
- [ ] Hot reload works (dev mode)

### Security
- [ ] Running as non-root user
- [ ] No secrets in container
- [ ] Resource limits enforced
- [ ] Proper file permissions

### Performance
- [ ] Build completes in < 5 minutes
- [ ] Startup completes in < 60 seconds
- [ ] API responds in < 200ms
- [ ] Memory usage stable

### Production Features
- [ ] Gunicorn installed
- [ ] Multi-worker config present
- [ ] Health checks passing
- [ ] Logs rotating properly

---

## 🎯 Expected Results

### Development Mode
- **Workers:** 1
- **Reload:** Enabled
- **Startup:** ~2-5 seconds
- **Memory:** ~500MB
- **Best For:** Development, testing

### Production Mode
- **Workers:** 4+
- **Reload:** Disabled
- **Startup:** ~5-10 seconds
- **Memory:** ~1.5GB
- **Best For:** Production, high load

---

## 🚨 Troubleshooting

### Issue: API not responding
```powershell
# Check if container is running
docker-compose ps

# Check logs
.\docker-logs.ps1 app

# Restart
docker-compose restart app
```

### Issue: Port already in use
```powershell
# Stop all containers
docker-compose down

# Check what's using the port
netstat -ano | findstr :8000

# Start again
docker-compose up -d
```

### Issue: Database connection failed
```powershell
# Check database health
docker exec RAG-PostgreSQL pg_isready -U rag_user

# Check connection string
docker exec RAG-API env | Select-String DATABASE_URL
```

---

## 🎉 Success Criteria

Phase 6 is working correctly if:

✅ All containers start without errors  
✅ API responds to health checks  
✅ Gunicorn is installed (v21.2.0)  
✅ Running as non-root user  
✅ Resource limits enforced  
✅ Hot reload works in dev mode  
✅ Production mode available  
✅ No linter errors  
✅ Logs are clean  
✅ All endpoints accessible  

---

## 📞 Need Help?

Check these files:
- **PHASE_6_VALIDATION_COMPLETE.md** - Full validation report
- **PHASE_6_PLAN.md** - Detailed implementation plan
- **docker-compose.yml** - Development configuration
- **docker-compose.prod.yml** - Production configuration

View logs:
```powershell
.\docker-logs.ps1 app
```

---

**Ready to test! 🚀**

Everything is configured and running. Start testing the API at:
- **Development:** http://localhost:8000
- **Production:** http://localhost:8001 (after starting with prod compose file)

