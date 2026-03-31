# Deployment Guide

This guide covers various deployment options for the Document Query System.

## Table of Contents

- [Local Deployment](#local-deployment)
- [Docker Deployment](#docker-deployment)
- [AWS Lambda Deployment](#aws-lambda-deployment)
- [AWS ECS Deployment](#aws-ecs-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)

---

## Local Deployment

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd Docllm

# Install dependencies
pip install -r requirements.txt

# Start server
python main.py

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Prerequisites

- Docker installed
- Docker Compose installed

### Setup

#### 1. Build Docker Image

```bash
docker build -t docllm-backend:latest .
```

#### 2. Run with Docker Compose

```bash
docker-compose up -d
```

#### 3. Verify

```bash
curl http://localhost:8000/health
```

### Docker Compose with Ollama

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - USE_OPENAI=false
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3:8b
      - EMBEDDING_MODEL=nomic-embed-text
      - VECTOR_DB=faiss
      - DEBUG=true
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  ollama_data:
```

### Push to Container Registry

```bash
# Tag image
docker tag docllm-backend:latest your-registry/docllm-backend:v1.0

# Push to registry
docker push your-registry/docllm-backend:v1.0
```

---

## AWS Lambda Deployment

### Prerequisites

- AWS CLI configured
- AWS SAM CLI installed
- Docker installed (for local testing)

### Deployment Steps

#### 1. Configure AWS Credentials

```bash
aws configure
```

#### 2. Update SAM Template

Edit `template.yaml` with your settings:

```yaml
Parameters:
  OllamaBaseUrl:
    Type: String
    Default: "http://your-ollama-endpoint.amazonaws.com"
  Environment:
    Type: String
    Default: "prod"
```

#### 3. Build Application

```bash
sam build
```

#### 4. Deploy

```bash
# First time deployment
sam deploy --guided

# Subsequent deployments
sam deploy
```

#### 5. Configure Environment Variables

```bash
aws ssm put-parameter \
  --name /docllm/OPENAI_API_KEY \
  --value "your-api-key" \
  --type SecureString

aws ssm put-parameter \
  --name /docllm/USE_OPENAI \
  --value "true" \
  --type String
```

#### 6. Update Lambda Environment

```yaml
# In template.yaml
Globals:
  Function:
    Environment:
      Variables:
        USE_OPENAI: !Ref UseOpenAI
        OPENAI_API_KEY: !Ref OpenAIApiKey
```

#### 7. API Gateway CORS

The SAM template includes CORS configuration. For custom domains:

```yaml
Domain:
  DomainName: api.yourdomain.com
  CertificateArn: arn:aws:acm:us-east-1:123456789:certificate/abc
  EndpointConfiguration: REGIONAL
  Route53:
    HostedZoneId: Z1234567890
```

### Lambda Layer for Dependencies

Create a Lambda layer for Python dependencies:

```bash
# Create layer directory
mkdir -p python/lib/python3.9/site-packages

# Install dependencies
pip install -r requirements.txt -t python/lib/python3.9/site-packages

# Create zip
cd python
zip -r ../layer.zip .
cd ..

# Upload to Lambda
aws lambda publish-layer-version \
  --layer-name docllm-dependencies \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.9 python3.10 python3.11
```

### API Gateway Custom Domain

```bash
# Create API
aws apigateway create-rest-api --name docllm-api

# Get API ID
API_ID=$(aws apigateway get-rest-apis --query 'items[0].id' --output text)

# Create resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $(aws apigateway get-resources --rest-api-id $API_ID --query 'items[0].id' --output text) \
  --path-part documents

# Deploy
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

---

## AWS ECS Deployment

### Prerequisites

- ECS cluster created
- Application Load Balancer configured
- ECR repository created

### Build and Push Image

```bash
# Login to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY

# Create repository
aws ecr create-repository --repository-name docllm-backend

# Build and tag
docker build -t docllm-backend:latest .
docker tag docllm-backend:latest $ECR_REGISTRY/docllm-backend:latest

# Push
docker push $ECR_REGISTRY/docllm-backend:latest
```

### Create Task Definition

```json
{
  "family": "docllm-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "docllm-backend",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/docllm-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "USE_OPENAI",
          "value": "true"
        },
        {
          "name": "VECTOR_DB",
          "value": "pinecone"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:docllm:OPENAI_API_KEY"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/docllm",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Register Task Definition

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Create Service

```bash
aws ecs create-service \
  --cluster docllm-cluster \
  --service-name docllm-backend \
  --task-definition docllm-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-123,subnet-456],securityGroups=[sg-789]}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/docllm/abc,containerName=docllm-backend,containerPort=8000"
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl configured
- Helm (optional)

### Create Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docllm-backend
  labels:
    app: docllm-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docllm-backend
  template:
    metadata:
      labels:
        app: docllm-backend
    spec:
      containers:
      - name: docllm-backend
        image: your-registry/docllm-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: USE_OPENAI
          value: "true"
        - name: VECTOR_DB
          value: "pinecone"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: docllm-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Create Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: docllm-backend
spec:
  selector:
    app: docllm-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Create Secrets

```bash
kubectl create secret generic docllm-secrets \
  --from-literal=openai-api-key="your-api-key"
```

### Deploy

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Check status
kubectl get pods
kubectl get services
kubectl logs -l app=docllm-backend
```

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: docllm-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: docllm-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

```bash
kubectl apply -f hpa.yaml
kubectl get hpa
```

### Helm Chart (Optional)

```bash
# Create Helm chart
helm create docllm-backend

# Edit values.yaml
# Install
helm install docllm-backend ./docllm-backend

# Upgrade
helm upgrade docllm-backend ./docllm-backend
```

---

## Production Checklist

### Security

- [ ] Enable HTTPS/TLS
- [ ] Configure authentication
- [ ] Set up rate limiting
- [ ] Use secrets management
- [ ] Enable WAF
- [ ] Configure VPC
- [ ] Enable CloudTrail logging

### Monitoring

- [ ] Set up CloudWatch
- [ ] Configure alarms
- [ ] Enable access logging
- [ ] Set up distributed tracing
- [ ] Configure dashboards

### Performance

- [ ] Enable caching
- [ ] Configure auto-scaling
- [ ] Optimize database queries
- [ ] Set up CDN
- [ ] Configure connection pooling

### Backup & Recovery

- [ ] Enable vector store backups
- [ ] Configure S3 versioning
- [ ] Set up disaster recovery
- [ ] Test restoration

---

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `USE_OPENAI` | Use OpenAI API | Yes | `false` |
| `OPENAI_API_KEY` | OpenAI API key | If USE_OPENAI=true | - |
| `OLLAMA_BASE_URL` | Ollama server URL | If USE_OPENAI=false | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | If USE_OPENAI=false | `llama3:8b` |
| `EMBEDDING_MODEL` | Embedding model | Yes | `nomic-embed-text` |
| `VECTOR_DB` | Vector database | Yes | `faiss` |
| `PINECONE_API_KEY` | Pinecone API key | If VECTOR_DB=pinecone | - |
| `AWS_ACCESS_KEY_ID` | AWS access key | For S3 | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | For S3 | - |
| `S3_BUCKET` | S3 bucket name | For S3 | - |

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs <container-id>

# Check environment
docker exec <container-id> env

# Shell into container
docker exec -it <container-id> /bin/bash
```

### Lambda Cold Start

- Increase memory allocation
- Use provisioned concurrency
- Pre-warm Lambda

### ECS Task Not Starting

```bash
# Check service events
aws ecs describe-services --cluster <cluster> --services <service>

# Check task definition
aws ecs describe-task-definition --task-definition docllm-backend

# Check CloudWatch logs
aws logs tail /ecs/docllm --follow
```

### Kubernetes Pod Issues

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check events
kubectl get events --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> --previous
```
