# Deployment Guide

This guide covers various deployment strategies for ModelSwitch, from local development to cloud production deployments.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployments](#cloud-deployments)
  - [AWS Deployment](#aws-deployment)
  - [Google Cloud Platform](#google-cloud-platform)
  - [Microsoft Azure](#microsoft-azure)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Best Practices](#production-best-practices)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

## Local Development

### Prerequisites

- Python 3.11+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/caprolt/ModelSwitch.git
cd ModelSwitch

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env

# Train example models
python examples/train_example_models.py

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/healthz

## Docker Deployment

### Single Container

```bash
# Build the image
docker build -t modelswitch:latest .

# Run the container
docker run -d \
  --name modelswitch \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -e DEFAULT_VERSION=v1 \
  modelswitch:latest
```

### Docker Compose (Recommended)

Includes FastAPI app, Prometheus, and Grafana:

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Access Points

- API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### Custom Configuration

Create a `.env` file:

```bash
HOST=0.0.0.0
PORT=8000
DEBUG=false
MODELS_DIR=models
DEFAULT_VERSION=v1
METRICS_ENABLED=true
CORS_ORIGINS=["*"]
```

## Cloud Deployments

### AWS Deployment

#### Option 1: AWS ECS (Elastic Container Service)

**Prerequisites:**
- AWS CLI installed and configured
- ECR repository created

**Step 1: Build and Push Image**

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
docker build -t modelswitch:latest .
docker tag modelswitch:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/modelswitch:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/modelswitch:latest
```

**Step 2: Create ECS Task Definition**

```json
{
  "family": "modelswitch",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "modelswitch",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/modelswitch:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "HOST", "value": "0.0.0.0"},
        {"name": "PORT", "value": "8000"},
        {"name": "DEFAULT_VERSION", "value": "v1"},
        {"name": "METRICS_ENABLED", "value": "true"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/modelswitch",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/healthz || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

**Step 3: Create ECS Service**

```bash
aws ecs create-service \
  --cluster modelswitch-cluster \
  --service-name modelswitch-service \
  --task-definition modelswitch \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-xxx,subnet-yyy],
    securityGroups=[sg-xxx],
    assignPublicIp=ENABLED
  }" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=modelswitch,containerPort=8000"
```

**Step 4: Configure Application Load Balancer**

- Create target group (port 8000, health check: /healthz)
- Create ALB with listener on port 80/443
- Configure routing rules
- Set up SSL certificate (AWS Certificate Manager)

**Model Storage with S3:**

```bash
# Sync models to S3
aws s3 sync ./models s3://modelswitch-models/

# Mount S3 bucket in container (use s3fs or EFS)
```

#### Option 2: AWS EC2

**Launch EC2 Instance:**

```bash
# Launch instance
aws ec2 run-instances \
  --image-id ami-xxx \
  --instance-type t3.medium \
  --key-name your-key \
  --security-group-ids sg-xxx \
  --user-data file://install.sh
```

**install.sh:**

```bash
#!/bin/bash
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Pull and run container
docker run -d \
  --name modelswitch \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/models:/app/models \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/modelswitch:latest
```

#### Option 3: AWS Lambda (Serverless)

For sporadic inference workloads:

```python
# lambda_handler.py
import json
import joblib
import boto3

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Download model from S3
    s3.download_file('modelswitch-models', 'v1/model.pkl', '/tmp/model.pkl')
    model = joblib.load('/tmp/model.pkl')
    
    # Parse request
    body = json.loads(event['body'])
    features = body['features']
    
    # Predict
    prediction = model.predict([features])[0]
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'prediction': int(prediction),
            'version': 'v1'
        })
    }
```

**Deploy with SAM:**

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  ModelSwitchFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_handler.lambda_handler
      Runtime: python3.11
      MemorySize: 1024
      Timeout: 30
      Environment:
        Variables:
          MODEL_BUCKET: modelswitch-models
      Events:
        PredictApi:
          Type: Api
          Properties:
            Path: /predict
            Method: post
```

### Google Cloud Platform

#### Option 1: Cloud Run (Recommended)

**Deploy with gcloud:**

```bash
# Build and submit to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/modelswitch

# Deploy to Cloud Run
gcloud run deploy modelswitch \
  --image gcr.io/PROJECT_ID/modelswitch \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --port 8000 \
  --set-env-vars DEFAULT_VERSION=v1,METRICS_ENABLED=true
```

**With Cloud Storage for models:**

```bash
# Create bucket
gsutil mb gs://modelswitch-models

# Upload models
gsutil -m rsync -r ./models gs://modelswitch-models/models

# Mount in Cloud Run (using gcsfuse in Dockerfile)
```

#### Option 2: GKE (Google Kubernetes Engine)

```bash
# Create cluster
gcloud container clusters create modelswitch-cluster \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --region us-central1

# Get credentials
gcloud container clusters get-credentials modelswitch-cluster \
  --region us-central1

# Deploy with kubectl
kubectl apply -f k8s/
```

#### Option 3: Compute Engine

```bash
# Create instance
gcloud compute instances create modelswitch-vm \
  --image-family debian-11 \
  --machine-type n1-standard-2 \
  --zone us-central1-a \
  --metadata-from-file startup-script=startup.sh

# SSH and deploy
gcloud compute ssh modelswitch-vm --zone us-central1-a
```

### Microsoft Azure

#### Option 1: Azure Container Instances (ACI)

```bash
# Create resource group
az group create --name modelswitch-rg --location eastus

# Create container registry
az acr create --resource-group modelswitch-rg \
  --name modelswitchacr --sku Basic

# Build and push
az acr build --registry modelswitchacr \
  --image modelswitch:latest .

# Deploy container
az container create \
  --resource-group modelswitch-rg \
  --name modelswitch-aci \
  --image modelswitchacr.azurecr.io/modelswitch:latest \
  --cpu 1 \
  --memory 1 \
  --ports 8000 \
  --dns-name-label modelswitch-app \
  --environment-variables \
    DEFAULT_VERSION=v1 \
    METRICS_ENABLED=true
```

#### Option 2: Azure App Service

```bash
# Create App Service plan
az appservice plan create \
  --name modelswitch-plan \
  --resource-group modelswitch-rg \
  --is-linux \
  --sku B1

# Create web app
az webapp create \
  --resource-group modelswitch-rg \
  --plan modelswitch-plan \
  --name modelswitch-app \
  --deployment-container-image-name modelswitchacr.azurecr.io/modelswitch:latest

# Configure
az webapp config appsettings set \
  --resource-group modelswitch-rg \
  --name modelswitch-app \
  --settings DEFAULT_VERSION=v1 METRICS_ENABLED=true
```

#### Option 3: Azure Kubernetes Service (AKS)

```bash
# Create AKS cluster
az aks create \
  --resource-group modelswitch-rg \
  --name modelswitch-aks \
  --node-count 2 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials \
  --resource-group modelswitch-rg \
  --name modelswitch-aks

# Deploy
kubectl apply -f k8s/
```

## Kubernetes Deployment

### Kubernetes Manifests

**deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: modelswitch
  labels:
    app: modelswitch
spec:
  replicas: 3
  selector:
    matchLabels:
      app: modelswitch
  template:
    metadata:
      labels:
        app: modelswitch
    spec:
      containers:
      - name: modelswitch
        image: modelswitch:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEFAULT_VERSION
          value: "v1"
        - name: METRICS_ENABLED
          value: "true"
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8000"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: models
          mountPath: /app/models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
```

**service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: modelswitch-service
spec:
  selector:
    app: modelswitch
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**ingress.yaml:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: modelswitch-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.modelswitch.com
    secretName: modelswitch-tls
  rules:
  - host: api.modelswitch.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: modelswitch-service
            port:
              number: 80
```

**hpa.yaml (Horizontal Pod Autoscaler):**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: modelswitch-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: modelswitch
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace modelswitch

# Apply configurations
kubectl apply -f k8s/ -n modelswitch

# Check status
kubectl get pods -n modelswitch
kubectl get services -n modelswitch

# View logs
kubectl logs -f deployment/modelswitch -n modelswitch

# Scale manually
kubectl scale deployment modelswitch --replicas=5 -n modelswitch
```

## Production Best Practices

### 1. Security

```bash
# Use secrets for sensitive data
kubectl create secret generic modelswitch-secrets \
  --from-literal=api-key=your-secret-key \
  -n modelswitch

# Reference in deployment
env:
- name: API_KEY
  valueFrom:
    secretKeyRef:
      name: modelswitch-secrets
      key: api-key
```

### 2. Resource Limits

Always set resource requests and limits:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

### 3. Health Checks

Configure proper health checks:

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### 4. Logging

Configure structured logging:

```python
# app/logging_config.py
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        }
        return json.dumps(log_data)

# Configure in main.py
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger()
logger.addHandler(handler)
```

### 5. Monitoring

Set up comprehensive monitoring:

- **Application metrics**: Request rate, latency, errors
- **System metrics**: CPU, memory, disk, network
- **Business metrics**: Model accuracy, drift, usage
- **Alerts**: Error rates, high latency, resource exhaustion

### 6. Backup Strategy

```bash
# Backup models regularly
aws s3 sync ./models s3://modelswitch-backups/models/$(date +%Y%m%d)/

# Version control models
git lfs track "*.pkl"
git add models/
git commit -m "Add model v2"
git push
```

### 7. CI/CD Pipeline

See `.github/workflows/deploy.yml` for automated deployment pipeline.

## Monitoring Setup

### Prometheus Configuration

Already included in `docker-compose.yml`. For production:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'modelswitch'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

1. Import dashboard from `grafana/dashboard.json`
2. Configure datasource (Prometheus)
3. Set up alerts for critical metrics

### CloudWatch (AWS)

```bash
# Install CloudWatch agent
aws logs create-log-group --log-group-name /ecs/modelswitch

# Configure in task definition
"logConfiguration": {
  "logDriver": "awslogs",
  "options": {
    "awslogs-group": "/ecs/modelswitch",
    "awslogs-region": "us-east-1",
    "awslogs-stream-prefix": "ecs"
  }
}
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs modelswitch

# Common issues:
# 1. Models directory missing: Mount volume correctly
# 2. Permission issues: Check file ownership
# 3. Port conflict: Use different port
```

### High Memory Usage

```bash
# Check memory consumption
docker stats modelswitch

# Solutions:
# 1. Limit cached models
# 2. Increase container memory
# 3. Implement LRU cache eviction
```

### Slow Predictions

```bash
# Check metrics
curl http://localhost:8000/metrics | grep latency

# Solutions:
# 1. Warm up models on startup
# 2. Increase workers
# 3. Optimize model (quantization, pruning)
# 4. Use faster inference engine
```

### Connection Refused

```bash
# Check if service is running
kubectl get pods -n modelswitch

# Check service endpoints
kubectl get endpoints -n modelswitch

# Check ingress
kubectl describe ingress modelswitch-ingress -n modelswitch
```

### Model Version Not Found

```bash
# Check models directory
docker exec modelswitch ls -la /app/models

# Verify model files
docker exec modelswitch ls -la /app/models/v1/

# Check logs
docker logs modelswitch | grep "model"
```

## Support

For deployment issues:
- Check [Issues](https://github.com/caprolt/ModelSwitch/issues)
- Review [Architecture](ARCHITECTURE.md)
- See [Contributing](CONTRIBUTING.md) for development setup

For production support, consider:
- Professional support contract
- Managed deployment service
- Custom consulting
