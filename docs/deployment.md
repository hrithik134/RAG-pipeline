# Deployment Guide

Complete guide for deploying the RAG Pipeline to production.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [CI/CD Setup](#cicd-setup)
3. [AWS Deployment](#aws-deployment)
4. [GCP Deployment](#gcp-deployment)
5. [Azure Deployment](#azure-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Secrets Configuration](#secrets-configuration)
8. [Scaling Configuration](#scaling-configuration)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Docker**: For building container images
- **kubectl**: For Kubernetes deployments (if using K8s)
- **Terraform**: For infrastructure as code (>= 1.0)
- **AWS CLI / gcloud / Azure CLI**: For cloud-specific deployments

### Required Access

- GitHub repository with Actions enabled
- Cloud provider account (AWS/GCP/Azure)
- Container registry access (ECR/GCR/ACR)
- Database service account
- Secrets management access

---

## CI/CD Setup

### GitHub Actions Configuration

The CI/CD pipeline is configured in:
- `.github/workflows/ci.yml` - Continuous Integration
- `.github/workflows/docker-build.yml` - Docker build and push

### Enabling GitHub Actions

1. **Enable Actions** in your GitHub repository settings
2. **Configure Secrets** (for push workflows):
   - `AWS_ECR_ROLE_ARN` - For AWS deployments
   - `GOOGLE_APPLICATION_CREDENTIALS` - For GCP deployments
   - `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` - For Azure deployments

### Manual Docker Push

Since push is configured to skip in workflows, manually push images:

```bash
# Build locally
docker build -t rag-pipeline:latest .

# Tag for registry
docker tag rag-pipeline:latest <registry>/rag-pipeline:<version>

# Push to registry
docker push <registry>/rag-pipeline:<version>
```

---

## AWS Deployment

### Using ECS Fargate

#### 1. Create ECR Repository

```bash
aws ecr create-repository --repository-name rag-pipeline
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
```

#### 2. Push Docker Image

```bash
# Build image
docker build -t rag-pipeline:latest .

# Tag and push
docker tag rag-pipeline:latest <account>.dkr.ecr.us-east-1.amazonaws.com/rag-pipeline:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/rag-pipeline:latest
```

#### 3. Create Secrets in Secrets Manager

```bash
# Store Pinecone API key
aws secretsmanager create-secret \
  --name rag-pipeline/pinecone-api-key \
  --secret-string "your-pinecone-api-key"

# Store LLM provider keys
aws secretsmanager create-secret \
  --name rag-pipeline/google-api-key \
  --secret-string "your-google-api-key"
```

#### 4. Configure Environment Variables

Create `.env.production`:
```bash
APP_ENV=production
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/rag_db
REDIS_URL=redis://elasticache-endpoint:6379/0
PINECONE_API_KEY=your-key
GOOGLE_API_KEY=your-key
LLM_PROVIDER=google
```

#### 5. Deploy with Terraform

```bash
cd terraform/aws
terraform init
terraform plan
terraform apply
```

---

## GCP Deployment

### Using GKE

#### 1. Create Artifact Registry

```bash
gcloud artifacts repositories create rag-pipeline \
  --repository-format=docker \
  --location=us-east1
```

#### 2. Push Docker Image

```bash
# Configure auth
gcloud auth configure-docker us-east1-docker.pkg.dev

# Build and push
docker build -t us-east1-docker.pkg.dev/PROJECT/rag-pipeline/rag-pipeline:latest .
docker push us-east1-docker.pkg.dev/PROJECT/rag-pipeline/rag-pipeline:latest
```

#### 3. Create Secrets in Secret Manager

```bash
echo -n "your-pinecone-api-key" | gcloud secrets create pinecone-api-key --data-file=-
echo -n "your-google-api-key" | gcloud secrets create google-api-key --data-file=-
```

#### 4. Deploy with Terraform

```bash
cd terraform/gcp
terraform init
terraform plan
terraform apply
```

---

## Azure Deployment

### Using Container Instances

#### 1. Create Azure Container Registry

```bash
az acr create --resource-group <group> --name <registry> --sku Basic
az acr login --name <registry>
```

#### 2. Push Docker Image

```bash
# Tag and push
docker tag rag-pipeline:latest <registry>.azurecr.io/rag-pipeline:latest
docker push <registry>.azurecr.io/rag-pipeline:latest
```

#### 3. Create Key Vault Secrets

```bash
az keyvault secret set --vault-name <vault> --name pinecone-api-key --value "your-key"
az keyvault secret set --vault-name <vault> --name google-api-key --value "your-key"
```

#### 4. Deploy with Terraform

```bash
cd terraform/azure
terraform init
terraform plan
terraform apply
```

---

## Kubernetes Deployment

### Using Helm Chart

#### 1. Update Values

Edit `helm/rag-pipeline/values.yaml`:
```yaml
image:
  repository: <registry>/rag-pipeline
  tag: latest

secrets:
  PINECONE_API_KEY: <your-key>
  GOOGLE_API_KEY: <your-key>

env:
  LLM_PROVIDER: "google"
```

#### 2. Install with Helm

```bash
cd helm/rag-pipeline
helm install rag-pipeline . \
  --set secrets.PINECONE_API_KEY="<key>" \
  --set secrets.GOOGLE_API_KEY="<key>"
```

#### 3. Upgrade Release

```bash
helm upgrade rag-pipeline . \
  --set image.tag="<new-version>"
```

---

## Secrets Configuration

### AWS Secrets Manager

Create secrets:
```bash
aws secretsmanager create-secret \
  --name rag-pipeline/pinecone-api-key \
  --secret-string "value"
```

Access in ECS task:
```hcl
secrets = [
  {
    name = "PINECONE_API_KEY"
    valueFrom = "arn:aws:secretsmanager:...:secret:rag-pipeline/pinecone-api-key"
  }
]
```

### GCP Secret Manager

Create secrets:
```bash
echo -n "value" | gcloud secrets create pinecone-api-key --data-file=-
```

Access in deployment:
```yaml
env:
  - name: PINECONE_API_KEY
    valueFrom:
      secretKeyRef:
        name: pinecone-api-key
        key: latest
```

### Azure Key Vault

Create secrets:
```bash
az keyvault secret set --vault <vault> --name pinecone-api-key --value "value"
```

Access in App Service:
```bash
az webapp config appsettings set \
  --name <app> \
  --settings "PINECONE_API_KEY=@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/pinecone-api-key/)"
```

---

## Scaling Configuration

### ECS Autoscaling

Enable in Terraform:
```hcl
resource "aws_appautoscaling_policy" "ecs_policy" {
  target_value = 60.0
  predefined_metric_specification {
    predefined_metric_type = "ECSServiceAverageCPUUtilization"
  }
}
```

### Kubernetes HPA

Enable in Helm:
```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 60
```

---

## Monitoring

### Health Checks

Endpoint: `https://your-domain/health`

Expected response:
```json
{
  "status": "healthy",
  "service": "RAG Pipeline",
  "version": "1.0.0",
  "environment": "production"
}
```

### Logging

View logs:
```bash
# AWS CloudWatch
aws logs tail /ecs/rag-pipeline --follow

# GCP Cloud Logging
gcloud logging tail "resource.type=k8s_container"

# Azure Monitor
az webapp log tail --name <app>
```

---

## Troubleshooting

### Deployment Issues

**Issue**: Container fails to start
**Solution**: Check logs, verify secrets, verify database connectivity

**Issue**: Health check fails
**Solution**: Ensure `/health` endpoint returns 200, check application logs

**Issue**: Migrations fail
**Solution**: Run manual migration:
```bash
docker run --rm <image> alembic upgrade head
```

### Connection Issues

**Issue**: Database connection timeout
**Solution**: Verify security groups, check database endpoint

**Issue**: Pinecone connection fails
**Solution**: Verify API key, check network connectivity

---

For more information:
- [Architecture](architecture.md)
- [API Examples](api-examples.md)
- [Operations](operations.md)
- [Configuration](configuration.md)

