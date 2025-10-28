# Phase 9 — Deployment and CI/CD Plan

## 📋 Overview

Phase 9 focuses on creating a complete CI/CD pipeline and deployment infrastructure for the RAG Pipeline. This includes GitHub Actions workflows, cloud deployment templates, and runtime guidance for production environments.

---

## 🎯 Goals for Phase 9

1. **GitHub Actions CI/CD**: Lint, type-check, test, build, and push Docker images
2. **Cloud Deployment Templates**: Terraform modules for AWS, GCP, and Azure
3. **Kubernetes Support**: Minimal Helm chart for Kubernetes deployments
4. **Runtime Guidance**: Secrets management, scaling, and worker configuration
5. **Production Ready**: Complete deployment documentation and best practices

---

## 🔄 Integration with Existing Code

### Files We'll Work With

**Existing Files (No Changes)**:
- `Dockerfile` - Already production-ready with multi-stage build
- `docker-compose.yml` - Local development setup
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project metadata and tool configs
- `pytest.ini` - Test configuration
- `gunicorn_conf.py` - Gunicorn configuration
- `app/main.py` - FastAPI application entry point
- `alembic/` - Database migrations

**New Files We'll Create**:
1. `.github/workflows/ci.yml` - CI pipeline
2. `.github/workflows/docker-build.yml` - Docker build and push
3. `terraform/aws/` - AWS ECS Fargate + RDS infrastructure
4. `terraform/gcp/` - GCP GKE + Cloud SQL infrastructure
5. `terraform/azure/` - Azure Web App + Azure DB infrastructure
6. `helm/rag-pipeline/` - Kubernetes Helm chart
7. `docs/deployment.md` - Deployment guide

---

## 📊 CI/CD Pipeline Design

### GitHub Actions Workflows

#### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Triggers**:
- Pull requests to `main` or `develop`
- Pushes to `main` or `develop`
- Manual workflow dispatch

**Python Versions**: 3.10, 3.11

**Steps**:
1. **Checkout Code**
   ```yaml
   - uses: actions/checkout@v4
   ```

2. **Setup Python**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: ${{ matrix.python }}
   ```

3. **Cache Dependencies**
   ```yaml
   - uses: actions/cache@v4
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
   ```

4. **Install Dependencies**
   ```yaml
   - run: pip install -r requirements.txt
   ```

5. **Lint with Ruff**
   ```yaml
   - run: ruff check app tests
   ```

6. **Type Check with mypy**
   ```yaml
   - run: mypy app
   ```

7. **Run Unit Tests**
   ```yaml
   - run: pytest -m unit --cov=app --cov-report=term-missing
   ```

8. **Run Integration Tests** (optional, allow failure)
   ```yaml
   - run: pytest -m integration
     continue-on-error: true
   ```

9. **Upload Coverage**
   ```yaml
   - uses: codecov/codecov-action@v4
   ```

---

#### 2. Docker Build Pipeline (`.github/workflows/docker-build.yml`)

**Triggers**:
- Push to `main` branch
- Tags matching `v*.*.*`

**Steps**:
1. **Checkout Code**
   ```yaml
   - uses: actions/checkout@v4
   ```

2. **Set up Docker Buildx**
   ```yaml
   - uses: docker/setup-buildx-action@v3
   ```

3. **Log in to Container Registry** (OIDC)
   ```yaml
   - name: Login to AWS ECR
     uses: aws-actions/amazon-ecr-login@v2
     with:
       oidc-role-arn: ${{ secrets.AWS_ECR_ROLE_ARN }}
   ```

4. **Build Docker Image**
   ```yaml
   - name: Build and push
     uses: docker/build-push-action@v5
     with:
       context: .
       push: true
       tags: |
         org/rag-pipeline:${{ github.sha }}
         org/rag-pipeline:latest
       cache-from: type=gha
       cache-to: type=gha,mode=max
   ```

5. **Scan Image** (optional)
   ```yaml
   - name: Run Trivy vulnerability scanner
     uses: aquasecurity/trivy-action@master
     with:
       image-ref: org/rag-pipeline:${{ github.sha }}
       format: 'sarif'
       output: 'trivy-results.sarif'
   ```

---

## ☁️ Cloud Deployment Templates

### AWS ECS Fargate + RDS

**Terraform Structure**:
```
terraform/aws/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── network/
│   │   ├── main.tf (VPC, subnets, IGW, NAT)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── rds/
│   │   ├── main.tf (PostgreSQL database)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecs/
│   │   ├── main.tf (Cluster, service, task definition)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── alb/
│   │   ├── main.tf (Application Load Balancer)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── secrets/
│       ├── main.tf (Secrets Manager)
│       ├── variables.tf
│       └── outputs.tf
```

**Key Features**:
- ECS Fargate with auto-scaling (min: 2, max: 10 tasks)
- RDS PostgreSQL db.t3.medium instance
- ALB with health checks on `/health`
- ECR for Docker images
- Secrets Manager for API keys
- CloudWatch for logging

**Task Definition**:
```hcl
resource "aws_ecs_task_definition" "app" {
  family                   = "rag-pipeline"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                      = "512"
  memory                  = "1024"
  
  container_definitions = jsonencode([{
    name  = "app"
    image = "org/rag-pipeline:latest"
    
    environment = [
      { name = "ENVIRONMENT", value = "production" }
    ]
    
    secrets = [
      { name = "PINECONE_API_KEY", valueFrom = "arn:aws:secretsmanager:..." }
    ]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group" = "/ecs/rag-pipeline"
        "awslogs-region" = "us-east-1"
      }
    }
    
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
    
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
  }])
}
```

---

### GCP GKE + Cloud SQL

**Terraform Structure**:
```
terraform/gcp/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── gke/
│   │   ├── main.tf (GKE cluster, node pool)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── cloud-sql/
│   │   ├── main.tf (Cloud SQL PostgreSQL)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── workload-identity/
│   │   ├── main.tf (Workload Identity binding)
│   │   └── variables.tf
│   └── artifact-registry/
│       ├── main.tf (Container registry)
│       ├── variables.tf
│       └── outputs.tf
```

**Key Features**:
- GKE cluster with auto-pilot
- Cloud SQL PostgreSQL with private IP
- Cloud SQL Proxy sidecar for secure connectivity
- Workload Identity for OIDC authentication
- Ingress with managed certificates
- HPA for autoscaling (CPU 60%, min 2, max 10)

**Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-pipeline
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rag-pipeline
  template:
    metadata:
      labels:
        app: rag-pipeline
    spec:
      containers:
      - name: app
        image: gcr.io/PROJECT_ID/rag-pipeline:latest
        ports:
        - containerPort: 8000
        
        env:
        - name: PINECONE_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: pinecone-api-key
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
      
      - name: cloud-sql-proxy
        image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest
        command:
        - "/cloud-sql-proxy"
        - "--address=0.0.0.0"
        - "--port=5432"
        - "PROJECT_ID:REGION:INSTANCE_NAME"
```

---

### Azure Web App + Azure DB

**Terraform Structure**:
```
terraform/azure/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── app-service/
│   │   ├── main.tf (Web App, App Service Plan)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── postgres/
│   │   ├── main.tf (Azure Database for PostgreSQL)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── container-registry/
│   │   ├── main.tf (ACR)
│   │   └── variables.tf
│   └── key-vault/
│       ├── main.tf (Key Vault for secrets)
│       ├── variables.tf
│       └── outputs.tf
```

**Key Features**:
- Web App with container support
- Azure Database for PostgreSQL Flexible Server
- Azure Container Registry
- Managed Identity + Key Vault for secrets
- Auto-scale based on CPU usage

**App Service**:
```hcl
resource "azurerm_linux_web_app" "app" {
  name                = "rag-pipeline-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  service_plan_id     = azurerm_service_plan.main.id
  
  site_config {
    always_on = true
    
    application_stack {
      docker_image_name   = "org/rag-pipeline:latest"
      docker_registry_url = "https://${azurerm_container_registry.main.login_server}"
    }
    
    health_check_path = "/health"
  }
  
  app_settings = {
    "PINECONE_API_KEY"     = "@Microsoft.KeyVault(SecretUri=https://...vaults/...)"
    "DATABASE_URL"         = "@Microsoft.KeyVault(SecretUri=https://...)"
  }
}
```

---

## ☸️ Kubernetes Helm Chart

**Chart Structure**:
```
helm/rag-pipeline/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── hpa.yaml
    ├── configmap.yaml
    ├── secret.yaml
    └── migration-job.yaml (pre-upgrade hook)
```

**Key Templates**:

**1. Deployment (`templates/deployment.yaml`)**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "rag-pipeline.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  
  template:
    metadata:
      labels:
        app: {{ include "rag-pipeline.name" . }}
    spec:
      containers:
      - name: app
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        ports:
        - name: http
          containerPort: 8000
          
        envFrom:
        - secretRef:
            name: {{ include "rag-pipeline.fullname" . }}-secrets
        - configMapRef:
            name: {{ include "rag-pipeline.fullname" . }}-config
        
        resources:
          requests:
            memory: "{{ .Values.resources.requests.memory }}"
            cpu: "{{ .Values.resources.requests.cpu }}"
          limits:
            memory: "{{ .Values.resources.limits.memory }}"
            cpu: "{{ .Values.resources.limits.cpu }}"
        
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 60
          periodSeconds: 30
        
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
```

**2. Migration Job (`templates/migration-job.yaml`)**:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "rag-pipeline.fullname" . }}-migration
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        command: ["alembic", "upgrade", "head"]
        envFrom:
        - secretRef:
            name: {{ include "rag-pipeline.fullname" . }}-secrets
      restartPolicy: Never
```

**3. HPA (`templates/hpa.yaml`)**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "rag-pipeline.fullname" . }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "rag-pipeline.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
```

**Values** (`values.yaml`):
```yaml
replicaCount: 2

image:
  repository: org/rag-pipeline
  tag: latest
  pullPolicy: IfNotPresent

resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"

autoscaling:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 60

env:
  LLM_PROVIDER: "google"
  PINECONE_DIMENSION: 768
  MAX_DOCUMENTS_PER_UPLOAD: 20
  MAX_PAGES_PER_DOCUMENT: 1000

secrets:
  PINECONE_API_KEY: ""
  GOOGLE_API_KEY: ""
```

---

## 🔐 Secrets Management with GitHub OIDC

### AWS Setup

**1. Configure OIDC Provider**:
```hcl
resource "aws_iam_oidc_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  
  client_id_list = ["sts.amazonaws.com"]
  
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}
```

**2. Create IAM Role**:
```hcl
resource "aws_iam_role" "github_actions" {
  name = "github-actions-rag-pipeline"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_oidc_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:org/rag-pipeline:*"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_actions_ecr" {
  role = aws_iam_role.github_actions.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ]
      Resource = "*"
    }]
  })
}
```

**3. GitHub Actions Workflow**:
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ACCOUNT_ID:role/github-actions-rag-pipeline
    aws-region: us-east-1
```

---

### GCP Setup

**1. Create Workload Identity Pool**:
```bash
gcloud iam workload-identity-pools create "github-pool" \
  --location="global" \
  --project=PROJECT_ID

gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --allowed-audiences="sts.googleapis.com"
```

**2. Grant Permissions**:
```bash
gcloud iam service-accounts add-iam-policy-binding \
  SERVICE_ACCOUNT_EMAIL \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/org/rag-pipeline"
```

**3. GitHub Actions Workflow**:
```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
    service_account: 'SERVICE_ACCOUNT_EMAIL'
```

---

### Azure Setup

**1. Create App Registration**:
```bash
az ad app create --display-name "rag-pipeline-github"

az ad app federated-credential create \
  --id "github-actions" \
  --app-id APP_ID \
  --parameters github-federated-credential.json
```

**2. Grant Permissions**:
```bash
az role assignment create \
  --assignee PRINCIPAL_ID \
  --role "AcrPush"
```

**3. GitHub Actions Workflow**:
```yaml
- name: Azure Login
  uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

- name: Log in to Azure Container Registry
  run: az acr login --name REGISTRY_NAME
```

---

## 📈 Scaling and Concurrency Configuration

### Horizontal Scaling

**ECS Fargate**:
```hcl
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_policy" {
  name               = "cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 60.0
  }
}
```

**Kubernetes HPA**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rag-pipeline
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rag-pipeline
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
```

---

### Gunicorn Worker Configuration

**Current Setup** (`gunicorn_conf.py`):
- Workers: 4 (configurable via environment)
- Worker class: uvicorn.workers.UvicornWorker
- Timeout: 120 seconds
- Keep-alive: 5 seconds

**Production Recommendations**:
```python
# For CPU-bound: (2 × CPU cores) + 1
workers = int(os.getenv('API_WORKERS', '4'))

# For I/O-bound (LLM/DB calls): 4 × CPU cores
workers = int(os.getenv('API_WORKERS', '8'))
```

**Environment Variable** (`.env`):
```bash
API_WORKERS=4  # Default for development
```

**Container Resource Limits**:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

---

### Database Connection Pooling

**Current Configuration**:
```bash
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

**Formula for Cloud Deployments**:
```
Pool Size per Instance = (Expected Requests/sec × Avg Request Time) / Workers per Instance
```

**Example**:
- 100 req/sec, 0.5s avg request time, 8 workers
- Pool size = (100 × 0.5) / 8 = 6.25 → 7 connections
- With overflow: 7 + 20 = 27 max connections per instance
- For 5 instances: 135 total connections

**AWS RDS Recommendation**:
```bash
# Instance db.t3.medium supports 87 connections max
# With 5 instances: 5 × 27 = 135 connections
# Error: Exceeds instance limit

# Solution: Reduce pool size or upgrade RDS instance
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

---

## 🏥 Health Checks and Monitoring

### Health Check Endpoint

Already implemented in `app/main.py`:
```python
@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "RAG Pipeline",
        "version": "1.0.0",
        "environment": settings.app_env
    }
```

### Liveness and Readiness Probes

**Kubernetes**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

**ECS**:
```hcl
healthCheck = {
  command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval    = 30
  timeout     = 5
  retries     = 3
  startPeriod = 60
}
```

---

## 🔄 Database Migration Strategy

### ECS Fargate

**Option 1: One-off Task**:
```bash
aws ecs run-task \
  --cluster rag-pipeline-cluster \
  --task-definition rag-pipeline-migration \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=DISABLED}"
```

**Option 2: Task Definition for Migration**:
```hcl
resource "aws_ecs_task_definition" "migration" {
  family                   = "rag-pipeline-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = "256"
  memory                  = "512"
  
  container_definitions = jsonencode([{
    name  = "migrate"
    image = "org/rag-pipeline:latest"
    command = ["alembic", "upgrade", "head"]
    # ... rest of config
  }])
}
```

### Kubernetes

**Migration Job** (Helm pre-upgrade hook):
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: rag-pipeline-migration
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        command: ["alembic", "upgrade", "head"]
      restartPolicy: Never
  backoffLimit: 1
  ttlSecondsAfterFinished: 3600
```

---

## 📝 Deployment Documentation

### Deployment Guide Structure

**File**: `docs/deployment.md`

**Sections**:
1. **Prerequisites** - Required tools and access
2. **CI/CD Setup** - GitHub Actions configuration
3. **AWS Deployment** - Step-by-step Terraform deployment
4. **GCP Deployment** - Step-by-step Terraform deployment
5. **Azure Deployment** - Step-by-step Terraform deployment
6. **Kubernetes Deployment** - Helm chart deployment
7. **Secrets Configuration** - OIDC and secret stores
8. **Scaling Configuration** - Autoscaling setup
9. **Monitoring** - Logging and metrics
10. **Troubleshooting** - Common issues and solutions

---

## ✅ Acceptance Criteria

### CI/CD
- ✅ Lint passes on all PRs
- ✅ Type check passes
- ✅ Unit tests pass (136/139 passing)
- ✅ Coverage report generated
- ✅ Docker image builds successfully
- ✅ Image pushed to registry
- ✅ Image scanning runs (optional)

### Infrastructure
- ✅ Terraform validates successfully
- ✅ Terraform plan shows expected resources
- ✅ Secrets stored in cloud secret stores
- ✅ Health checks configured
- ✅ Autoscaling configured
- ✅ Logging configured

### Runtime
- ✅ Application starts successfully
- ✅ Health endpoint returns 200
- ✅ Migrations run before deployment
- ✅ Database connectivity works
- ✅ Pinecone connectivity works
- ✅ LLM API calls succeed

---

## 🚀 Implementation Order

### Step 1: Setup GitHub Actions (Priority 1)
1. Create `.github/workflows/ci.yml`
2. Create `.github/workflows/docker-build.yml`
3. Test on a feature branch
4. Merge to main

### Step 2: Create Deployment Documentation (Priority 2)
1. Create `docs/deployment.md`
2. Document OIDC setup
3. Document secrets management
4. Document scaling configuration

### Step 3: Create Cloud Templates (Priority 3)
1. Start with AWS (Terraform)
2. Add GCP (Terraform)
3. Add Azure (Terraform)
4. Test in dev environment

### Step 4: Create Helm Chart (Priority 4)
1. Create `helm/rag-pipeline/`
2. Test on minikube/local Kubernetes
3. Document deployment process

### Step 5: Production Deployment (Priority 5)
1. Deploy to dev environment
2. Smoke testing
3. Deploy to staging
4. Deploy to production

---

## 🔍 Integration with Existing Files

### No Code Changes Required

**File**: `Dockerfile`
- Already uses multi-stage build
- Already has Gunicorn configuration
- Already has health check configuration

**File**: `docker-compose.yml`
- Current service names: `app`, `postgres`, `redis`, `migrate`
- Keep compatibility with local development

**File**: `pytest.ini`
- Current markers: `unit`, `integration`, `api`, etc.
- CI will use these markers

**File**: `requirements.txt`
- Already has all dependencies
- CI will install from this file

**File**: `gunicorn_conf.py`
- Current workers: 4
- Environment variable: `API_WORKERS`

**File**: `app/main.py`
- Health check at `/health` already implemented
- No changes needed

---

## 📊 Success Metrics

### CI/CD Metrics
- Build time < 10 minutes
- Test execution < 5 minutes
- Docker build < 3 minutes
- Image size < 500 MB

### Deployment Metrics
- Deployment time < 15 minutes
- Zero-downtime deployments
- Rollback time < 5 minutes
- Health check passes within 60 seconds

### Runtime Metrics
- P99 latency < 500ms
- Error rate < 0.1%
- Uptime > 99.9%
- Autoscaling responds within 5 minutes

---

**Document Version**: 1.0  
**Last Updated**: October 28, 2025  
**Status**: Ready for Implementation  
**Next Steps**: Implement GitHub Actions workflows

