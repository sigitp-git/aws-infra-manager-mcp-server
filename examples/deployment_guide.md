# AWS Infrastructure Manager MCP Server - Deployment Guide

This guide provides step-by-step instructions for deploying and configuring the AWS Infrastructure Manager MCP Server in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Production Deployment](#production-deployment)
- [Container Deployment](#container-deployment)
- [AWS Lambda Deployment](#aws-lambda-deployment)
- [Configuration Management](#configuration-management)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Memory**: Minimum 512MB RAM
- **Storage**: 100MB free space
- **Network**: Internet access for AWS API calls

### Required Tools

```bash
# Install uv (recommended Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or install with pip
pip install uv

# Install AWS CLI (optional but recommended)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### AWS Account Setup

1. **Create AWS Account** (if not already available)
2. **Configure IAM User/Role** with appropriate permissions
3. **Set up AWS credentials** using one of the methods below

## Local Development Setup

### 1. Clone and Install

```bash
# Clone the repository
git clone <repository-url>
cd aws-infra-manager-mcp-server

# Install dependencies
uv sync --extra dev

# Verify installation
uv run python -c "import aws_infra_manager_mcp_server; print('Installation successful')"
```

### 2. Configure AWS Credentials

Choose one of the following methods:

#### Method A: AWS CLI Configuration

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and default region
```

#### Method B: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=your_access_key_here
export AWS_SECRET_ACCESS_KEY=your_secret_key_here
export AWS_DEFAULT_REGION=us-east-1
```

#### Method C: AWS Profile

```bash
# Configure named profile
aws configure --profile mcp-server

# Use profile
export AWS_PROFILE=mcp-server
```

### 3. Test the Server

```bash
# Run tests
uv run pytest tests/ -v

# Test AWS connectivity
uv run python -c "
from aws_infra_manager_mcp_server.server import get_caller_identity
result = get_caller_identity()
print('AWS Connection:', 'Success' if result.get('success') else 'Failed')
print('Account:', result.get('identity', {}).get('Account', 'Unknown'))
"
```

### 4. Configure MCP Client

Add to your MCP client configuration (e.g., `.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "aws-infra-manager": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/aws-infra-manager-mcp-server",
        "python",
        "-m",
        "aws_infra_manager_mcp_server.server"
      ],
      "env": {
        "AWS_REGION": "us-east-1"
      },
      "disabled": false,
      "autoApprove": [
        "get_caller_identity",
        "list_ec2_instances",
        "list_vpcs",
        "list_s3_buckets",
        "list_rds_instances",
        "list_lambda_functions",
        "get_aws_regions"
        "list_ec2_instances",
        "list_vpcs",
        "list_s3_buckets"
      ]
    }
  }
}
```

## Production Deployment

### 1. Server Setup

#### Ubuntu/Debian

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Create application user
sudo useradd -m -s /bin/bash mcp-server
sudo su - mcp-server

# Clone and install
git clone <repository-url> aws-infra-manager-mcp-server
cd aws-infra-manager-mcp-server
uv sync --extra dev
```

#### Amazon Linux 2/RHEL/CentOS

```bash
# Update system
sudo yum update -y

# Install Python 3.10+
sudo yum install python3 python3-pip -y

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Create application user
sudo useradd -m mcp-server
sudo su - mcp-server

# Clone and install
git clone <repository-url> aws-infra-manager-mcp-server
cd aws-infra-manager-mcp-server
uv sync --extra dev
```

### 2. IAM Role Configuration (Recommended)

Create an IAM role for the server:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Attach the necessary policies:

```bash
# Create role
aws iam create-role \
    --role-name MCPServerRole \
    --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
    --role-name MCPServerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

aws iam attach-role-policy \
    --role-name MCPServerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Create instance profile
aws iam create-instance-profile \
    --instance-profile-name MCPServerProfile

aws iam add-role-to-instance-profile \
    --instance-profile-name MCPServerProfile \
    --role-name MCPServerRole
```

### 3. Systemd Service Configuration

Create a systemd service file:

```bash
sudo tee /etc/systemd/system/mcp-server.service << EOF
[Unit]
Description=AWS Infrastructure Manager MCP Server
After=network.target

[Service]
Type=simple
User=mcp-server
Group=mcp-server
WorkingDirectory=/home/mcp-server/aws-infra-manager-mcp-server
Environment=AWS_REGION=us-east-1
Environment=PYTHONPATH=/home/mcp-server/aws-infra-manager-mcp-server/src
ExecStart=/home/mcp-server/.local/bin/uv run python -m aws_infra_manager_mcp_server.server
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mcp-server
sudo systemctl start mcp-server

# Check status
sudo systemctl status mcp-server
```

### 4. Nginx Reverse Proxy (Optional)

If exposing the server via HTTP:

```bash
# Install Nginx
sudo apt install nginx -y

# Configure Nginx
sudo tee /etc/nginx/sites-available/mcp-server << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/mcp-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Container Deployment

### 1. Docker Setup

Create a Dockerfile:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create app directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN uv sync --extra dev

# Create non-root user
RUN useradd -m -u 1000 mcp-server
USER mcp-server

# Expose port (if needed)
EXPOSE 8000

# Run the server
CMD ["uv", "run", "python", "-m", "aws_infra_manager_mcp_server.server"]
```

Build and run:

```bash
# Build image
docker build -t aws-infra-manager-mcp-server .

# Run container
docker run -d \
    --name mcp-server \
    -e AWS_REGION=us-east-1 \
    -e AWS_ACCESS_KEY_ID=your_key \
    -e AWS_SECRET_ACCESS_KEY=your_secret \
    -p 8000:8000 \
    aws-infra-manager-mcp-server

# Or with IAM role (on EC2)
docker run -d \
    --name mcp-server \
    -e AWS_REGION=us-east-1 \
    -p 8000:8000 \
    aws-infra-manager-mcp-server
```

### 2. Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    container_name: aws-infra-manager-mcp-server
    restart: unless-stopped
    environment:
      - AWS_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: mcp-server-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - mcp-server
```

Deploy:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f mcp-server

# Scale if needed
docker-compose up -d --scale mcp-server=3
```

### 3. Kubernetes Deployment

Create Kubernetes manifests:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  labels:
    app: mcp-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      serviceAccountName: mcp-server-sa
      containers:
      - name: mcp-server
        image: aws-infra-manager-mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: AWS_REGION
          value: "us-east-1"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mcp-server-service
spec:
  selector:
    app: mcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
# serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-server-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/MCPServerRole
```

Deploy to Kubernetes:

```bash
# Apply manifests
kubectl apply -f deployment.yaml

# Check deployment
kubectl get pods -l app=mcp-server
kubectl get services

# View logs
kubectl logs -l app=mcp-server -f
```

## AWS Lambda Deployment

### 1. Lambda Function Setup

Create `lambda_handler.py`:

```python
import json
import logging
from aws_infra_manager_mcp_server.server import mcp

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """AWS Lambda handler for MCP server."""
    try:
        # Extract MCP request from event
        method = event.get('httpMethod', 'POST')
        body = json.loads(event.get('body', '{}'))
        
        # Process MCP request
        if method == 'POST' and 'method' in body:
            # Handle MCP tool call
            tool_name = body['method']
            params = body.get('params', {})
            
            # Execute tool
            result = mcp.call_tool(tool_name, params)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request'})
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### 2. Package for Lambda

```bash
# Create deployment package
mkdir lambda-package
cd lambda-package

# Install dependencies
uv pip install --target . aws-infra-manager-mcp-server

# Copy handler
cp ../lambda_handler.py .

# Create ZIP
zip -r ../mcp-server-lambda.zip .
```

### 3. Deploy Lambda Function

```bash
# Create Lambda function
aws lambda create-function \
    --function-name mcp-server \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT:role/MCPServerLambdaRole \
    --handler lambda_handler.lambda_handler \
    --zip-file fileb://mcp-server-lambda.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables='{AWS_REGION=us-east-1}'

# Create API Gateway
aws apigateway create-rest-api \
    --name mcp-server-api \
    --description "MCP Server API"
```

## Configuration Management

### 1. Environment-Specific Configurations

Create configuration files for different environments:

```bash
# config/development.env
AWS_REGION=us-east-1
LOG_LEVEL=DEBUG
MAX_RETRIES=3

# config/staging.env
AWS_REGION=us-east-1
LOG_LEVEL=INFO
MAX_RETRIES=5

# config/production.env
AWS_REGION=us-east-1
LOG_LEVEL=WARNING
MAX_RETRIES=10
```

### 2. AWS Systems Manager Parameter Store

Store sensitive configuration:

```bash
# Store database password
aws ssm put-parameter \
    --name "/mcp-server/prod/database/password" \
    --value "SecurePassword123!" \
    --type "SecureString"

# Store API keys
aws ssm put-parameter \
    --name "/mcp-server/prod/api/key" \
    --value "api-key-value" \
    --type "SecureString"
```

### 3. Configuration Loading

Update server to load configuration:

```python
import os
import boto3
from typing import Dict, Any

class ConfigManager:
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.ssm = boto3.client('ssm')
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from various sources."""
        # Load from environment variables
        self._config.update({
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'max_retries': int(os.getenv('MAX_RETRIES', '5'))
        })
        
        # Load from Parameter Store
        try:
            parameters = self.ssm.get_parameters_by_path(
                Path=f'/mcp-server/{self.environment}/',
                Recursive=True,
                WithDecryption=True
            )
            
            for param in parameters['Parameters']:
                key = param['Name'].split('/')[-1]
                self._config[key] = param['Value']
                
        except Exception as e:
            print(f"Warning: Could not load parameters from SSM: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

# Usage
config = ConfigManager(os.getenv('ENVIRONMENT', 'production'))
```

## Monitoring Setup

### 1. CloudWatch Logs

Configure logging:

```python
import logging
import boto3
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured logging for CloudWatch."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create CloudWatch handler
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

logger = setup_logging()
```

### 2. CloudWatch Metrics

Add custom metrics:

```python
import boto3
from datetime import datetime

class MetricsCollector:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
    
    def put_metric(self, metric_name: str, value: float, unit: str = 'Count'):
        """Send custom metric to CloudWatch."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='MCP/Server',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to send metric {metric_name}: {e}")

# Usage
metrics = MetricsCollector()
metrics.put_metric('ToolCalls', 1)
metrics.put_metric('ErrorRate', 0.05, 'Percent')
```

### 3. Health Checks

Implement health check endpoints:

```python
@mcp.tool()
def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        # Test AWS connectivity
        sts = aws_clients.get_client('sts')
        identity = sts.get_caller_identity()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "aws_account": identity.get('Account'),
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Troubleshooting

### Common Issues

#### 1. AWS Credentials Not Found

```bash
# Check credentials
aws sts get-caller-identity

# If using IAM role, check instance metadata
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Verify environment variables
env | grep AWS
```

#### 2. Permission Denied Errors

```bash
# Check IAM policies
aws iam list-attached-role-policies --role-name MCPServerRole
aws iam get-role-policy --role-name MCPServerRole --policy-name MCPServerPolicy

# Test specific permissions
aws ec2 describe-instances --dry-run
```

#### 3. Network Connectivity Issues

```bash
# Test AWS API connectivity
curl -I https://ec2.us-east-1.amazonaws.com

# Check security groups
aws ec2 describe-security-groups --group-ids sg-12345678

# Verify VPC configuration
aws ec2 describe-vpcs
```

#### 4. High Memory Usage

```bash
# Monitor memory usage
top -p $(pgrep -f mcp-server)

# Check for memory leaks
python -m memory_profiler server.py

# Adjust container limits
docker update --memory=1g mcp-server
```

### Debugging Tools

#### 1. Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
uv run python -m aws_infra_manager_mcp_server.server
```

#### 2. AWS CLI Debug Mode

```bash
aws --debug ec2 describe-instances
```

#### 3. Network Debugging

```bash
# Test DNS resolution
nslookup ec2.us-east-1.amazonaws.com

# Check network routes
traceroute ec2.us-east-1.amazonaws.com

# Monitor network traffic
sudo tcpdump -i any host ec2.us-east-1.amazonaws.com
```

### Performance Optimization

#### 1. Connection Pooling

```python
import boto3
from botocore.config import Config

# Configure connection pooling
config = Config(
    max_pool_connections=50,
    retries={'max_attempts': 3}
)

session = boto3.Session()
client = session.client('ec2', config=config)
```

#### 2. Caching

```python
from functools import lru_cache
import time

@lru_cache(maxsize=128)
def get_cached_regions():
    """Cache AWS regions for 1 hour."""
    return get_aws_regions()

# Clear cache periodically
def clear_cache():
    get_cached_regions.cache_clear()
```

#### 3. Async Operations

```python
import asyncio
import aioboto3

async def async_list_instances():
    """Async version of list_ec2_instances."""
    session = aioboto3.Session()
    async with session.client('ec2') as ec2:
        response = await ec2.describe_instances()
        return response
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Update Dependencies**
   ```bash
   uv sync --upgrade
   ```

2. **Rotate Credentials**
   ```bash
   aws iam create-access-key --user-name mcp-server-user
   # Update configuration
   aws iam delete-access-key --access-key-id OLD_KEY --user-name mcp-server-user
   ```

3. **Review Logs**
   ```bash
   sudo journalctl -u mcp-server -f
   ```

4. **Monitor Metrics**
   ```bash
   aws cloudwatch get-metric-statistics \
       --namespace MCP/Server \
       --metric-name ToolCalls \
       --start-time 2024-01-01T00:00:00Z \
       --end-time 2024-01-02T00:00:00Z \
       --period 3600 \
       --statistics Sum
   ```

### Getting Help

- **Documentation**: Check the API reference and security guide
- **Logs**: Review application and system logs
- **AWS Support**: Create support cases for AWS-related issues
- **Community**: Check GitHub issues and discussions

Remember to always test deployments in a staging environment before production!