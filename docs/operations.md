# Operations Runbook

This document provides operational procedures for running, monitoring, and troubleshooting the RAG Pipeline.

---

## Deployment

### Quick Start (Docker Compose - Recommended)

```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Verify installation
curl http://localhost:8000/health
```

---

## Service Management

### Start Services

```bash
docker-compose up -d
```

### Stop Services

```bash
docker-compose down
```

### Restart Services

```bash
docker-compose restart
```

### View Running Containers

```bash
docker-compose ps
```

### Access Container Shell

```bash
# API container
docker-compose exec api /bin/bash

# PostgreSQL
docker-compose exec postgres psql -U rag_user -d rag_db

# Redis
docker-compose exec redis redis-cli
```

---

## Monitoring

### Health Checks

**Application Health**:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "RAG Pipeline",
  "version": "1.0.0",
  "environment": "development"
}
```

### View Logs

**Application Logs**:
```bash
docker-compose logs -f api
```

**All Service Logs**:
```bash
docker-compose logs -f
```

**Specific Service**:
```bash
docker-compose logs -f postgres
docker-compose logs -f redis
```

**Last 100 Lines**:
```bash
docker-compose logs --tail=100 api
```

### Container Status

```bash
docker-compose ps
```

### Resource Usage

```bash
docker stats
```

---

## Database Operations

### Access PostgreSQL

```bash
docker-compose exec postgres psql -U rag_user -d rag_db
```

### Run Migrations

```bash
# Upgrade to latest
docker-compose exec api alembic upgrade head

# Show current version
docker-compose exec api alembic current

# Show migration history
docker-compose exec api alembic history
```

### Backup Database

```bash
# Create backup
docker-compose exec postgres pg_dump -U rag_user rag_db > backup.sql

# Compress backup
docker-compose exec postgres pg_dump -U rag_user rag_db | gzip > backup.sql.gz
```

### Restore Database

```bash
# Restore from backup
docker-compose exec -T postgres psql -U rag_user rag_db < backup.sql

# Restore compressed backup
gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U rag_user rag_db
```

### Database Size

```bash
docker-compose exec postgres psql -U rag_user -d rag_db -c "
SELECT 
    pg_size_pretty(pg_database_size('rag_db')) as database_size,
    pg_size_pretty(pg_database_size('rag_db') - pg_database_size('template0')) as data_size;
"
```

---

## Redis Operations

### Access Redis CLI

```bash
docker-compose exec redis redis-cli
```

### View Keys

```bash
docker-compose exec redis redis-cli KEYS "*"
```

### Clear Cache

```bash
# Clear all keys
docker-compose exec redis redis-cli FLUSHALL

# Clear specific pattern
docker-compose exec redis redis-cli --scan --pattern "rate_limit:*" | xargs docker-compose exec redis redis-cli DEL
```

### Monitor Redis

```bash
docker-compose exec redis redis-cli MONITOR
```

---

## Pinecone Operations

### Check Index Status

```python
import pinecone

pinecone.init(api_key="your-key", environment="us-east-1-aws")
index = pinecone.Index("rag-documents")

# Get index stats
stats = index.describe_index_stats()
print(stats)
```

### Delete All Vectors

```python
# Delete by filter
index.delete(delete_all=True)
```

---

## Common Tasks

### Upload Documents

```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@document.pdf"
```

### Query Documents

```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?"}'
```

### Check Upload Status

```bash
curl http://localhost:8000/v1/documents/uploads/{upload_id}
```

### List Documents

```bash
curl http://localhost:8000/v1/documents
```

---

## Troubleshooting

### Application Won't Start

**Symptoms**: Containers exit immediately or fail to start.

**Diagnosis**:
```bash
# Check logs
docker-compose logs api

# Check container status
docker-compose ps
```

**Common Causes**:
1. Port already in use
   ```bash
   # Check if ports are in use
   netstat -an | findstr :8000
   ```
2. Environment variables missing
   ```bash
   # Verify .env file exists and is configured
   cat .env
   ```
3. Database connection issue
   ```bash
   # Check database logs
   docker-compose logs postgres
   ```

**Solutions**:
```bash
# Rebuild containers
docker-compose build --no-cache

# Reset and restart
docker-compose down -v
docker-compose up -d
```

---

### Database Connection Issues

**Symptoms**: Application can't connect to PostgreSQL.

**Diagnosis**:
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U rag_user -d rag_db
```

**Solutions**:
```bash
# Restart database
docker-compose restart postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec api alembic upgrade head
```

---

### Pinecone Connection Issues

**Symptoms**: Embedding and query operations fail.

**Diagnosis**:
```bash
# Check API logs
docker-compose logs api | grep -i pinecone

# Verify API key
grep PINECONE_API_KEY .env
```

**Solutions**:
1. Verify API key in `.env`
2. Check Pinecone dashboard for index status
3. Ensure correct environment and region
4. Check rate limits

---

### Rate Limiting Issues

**Symptoms**: "Too many requests" errors.

**Diagnosis**:
```bash
# Check rate limit keys in Redis
docker-compose exec redis redis-cli KEYS "rate_limit:*"
```

**Solutions**:
1. Wait for rate limit reset
2. Clear rate limit cache:
   ```bash
   docker-compose exec redis redis-cli FLUSHALL
   ```
3. Adjust rate limits in `.env`:
   ```bash
   RATE_LIMIT_QUERY=30/minute
   ```

---

### Upload Failures

**Symptoms**: Documents fail to upload or process.

**Diagnosis**:
```bash
# Check upload logs
docker-compose logs api | grep -i upload

# Check file storage
ls -la uploads/
```

**Common Causes**:
1. File too large (max 50 MB)
2. Unsupported file format
3. Too many files (max 20 per batch)
4. Corrupt file

**Solutions**:
1. Check file size
2. Verify supported format (PDF, DOCX, TXT)
3. Reduce batch size
4. Try single file upload

---

### Query Failures

**Symptoms**: Queries return errors or empty results.

**Diagnosis**:
```bash
# Check query logs
docker-compose logs api | grep -i query

# Check Pinecone index
python check_pinecone.py
```

**Common Causes**:
1. No documents uploaded
2. Pinecone index empty
3. LLM provider issues
4. Rate limiting

**Solutions**:
1. Upload documents first
2. Check Pinecone index stats
3. Verify LLM API key
4. Check rate limits

---

## Performance Tuning

### Optimize PostgreSQL

**Increase shared_buffers**:
```bash
# Edit postgresql.conf
docker-compose exec postgres vi /var/lib/postgresql/data/postgresql.conf

# Add:
shared_buffers = 256MB
effective_cache_size = 1GB
```

### Optimize Redis

**Increase memory**:
```bash
# Edit docker-compose.yml redis command:
command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Increase Worker Count

Edit `gunicorn_conf.py`:
```python
workers = 8
```

---

## Backup and Recovery

### Full System Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U rag_user rag_db > db_backup.sql

# Backup uploads
tar -czf uploads_backup.tar.gz uploads/

# Backup configuration
cp .env env_backup
```

### Restore System

```bash
# Restore database
docker-compose exec -T postgres psql -U rag_user rag_db < db_backup.sql

# Restore uploads
tar -xzf uploads_backup.tar.gz

# Restore configuration
cp env_backup .env
```

---

## Scaling

### Horizontal Scaling

**Add more API workers**:
```bash
# Edit docker-compose.yml
# Increase workers
workers: 4

# Scale containers
docker-compose up -d --scale api=3
```

### Vertical Scaling

**Increase container resources** in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

---

## Security

### Update Environment Variables

```bash
# Edit .env
nano .env

# Restart services
docker-compose restart api
```

### Rotate API Keys

1. Update keys in `.env`
2. Restart services:
   ```bash
   docker-compose restart api
   ```

### Enable HTTPS (Production)

1. Add SSL certificates to `docker-compose.yml`
2. Update `CORS_ORIGINS`
3. Configure reverse proxy (Nginx)

---

## Maintenance

### Clear Old Data

```bash
# Remove old uploads (>30 days)
find uploads/ -mtime +30 -delete

# Clean Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Vacuum PostgreSQL
docker-compose exec postgres psql -U rag_user -d rag_db -c "VACUUM ANALYZE;"
```

### Update Dependencies

```bash
# Update requirements
pip install -r requirements.txt --upgrade

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

---

## Monitoring Commands

### Check System Health

```bash
# All services
docker-compose ps

# Application health
curl http://localhost:8000/health

# Database connections
docker-compose exec postgres psql -U rag_user -d rag_db -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory
docker-compose exec redis redis-cli INFO memory
```

### View Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

---

For more information:
- [Architecture](architecture.md)
- [API Examples](api-examples.md)
- [Configuration Guide](configuration.md)

