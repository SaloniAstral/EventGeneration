# Financial Data Streaming System - Production Deployment Guide

Complete guide for deploying the Financial Data Streaming System to AWS ECS with automated CI/CD pipelines.

## 🏗️ Architecture Overview

The production deployment uses AWS ECS (Elastic Container Service) with the following components:

- **ECS Cluster**: Container orchestration platform
- **Application Load Balancer (ALB)**: Traffic distribution and health checks
- **ECR Repositories**: Container image storage
- **Auto Scaling**: Automatic scaling based on CPU utilization
- **CloudWatch**: Monitoring and logging
- **VPC & Security Groups**: Network isolation and security

## 🚀 Quick Start Deployment

### Prerequisites

1. **AWS CLI** installed and configured
2. **Docker** installed and running
3. **AWS Account** with appropriate permissions
4. **VPC** with public and private subnets

### One-Command Deployment

```bash
# Deploy to production
./deployment/deploy.sh production

# Deploy to staging
./deployment/deploy.sh staging

# Deploy to development
./deployment/deploy.sh development
```

## 📋 Manual Deployment Steps

### 1. Prepare AWS Environment

```bash
# Configure AWS CLI
aws configure

# Verify credentials
aws sts get-caller-identity

# Set region
export AWS_REGION=us-east-2
```

### 2. Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com

# Build images
docker build -t financial-streaming-api-server:latest ec2_api_server/
docker build -t financial-streaming-stream-receiver:latest ec2_stream_receiver/
docker build -t financial-streaming-driver:latest ec2_driver/
docker build -t financial-streaming-monitoring:latest monitoring/

# Tag and push images
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$AWS_REGION

docker tag financial-streaming-api-server:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-api-server-production:latest
docker tag financial-streaming-stream-receiver:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-stream-receiver-production:latest
docker tag financial-streaming-driver:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-driver-production:latest
docker tag financial-streaming-monitoring:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-monitoring-production:latest

docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-api-server-production:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-stream-receiver-production:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-driver-production:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-monitoring-production:latest
```

### 3. Deploy ECS Cluster

```bash
# Deploy cluster stack
aws cloudformation deploy \
    --template-file deployment/ecs-cluster.yaml \
    --stack-name financial-streaming-production-cluster \
    --parameter-overrides \
        Environment=production \
        VpcId=vpc-xxxxxxxxx \
        PublicSubnet1=subnet-xxxxxxxxx \
        PublicSubnet2=subnet-xxxxxxxxx \
        PrivateSubnet1=subnet-xxxxxxxxx \
        PrivateSubnet2=subnet-xxxxxxxxx \
        InstanceType=t3.medium \
        MinSize=2 \
        MaxSize=10 \
        DesiredCapacity=2 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-2
```

### 4. Deploy ECS Services

```bash
# Get stack outputs
CLUSTER_NAME=$(aws cloudformation describe-stacks --stack-name financial-streaming-production-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' --output text)
ALB_ARN=$(aws cloudformation describe-stacks --stack-name financial-streaming-production-cluster --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerArn`].OutputValue' --output text)
TASK_EXECUTION_ROLE_ARN=$(aws cloudformation describe-stacks --stack-name financial-streaming-production-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECSTaskExecutionRoleArn`].OutputValue' --output text)
TASK_ROLE_ARN=$(aws cloudformation describe-stacks --stack-name financial-streaming-production-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECSTaskRoleArn`].OutputValue' --output text)

# Deploy services stack
aws cloudformation deploy \
    --template-file deployment/ecs-services.yaml \
    --stack-name financial-streaming-production-services \
    --parameter-overrides \
        Environment=production \
        ECSClusterName=$CLUSTER_NAME \
        ApplicationLoadBalancerArn=$ALB_ARN \
        ECSTaskExecutionRoleArn=$TASK_EXECUTION_ROLE_ARN \
        ECSTaskRoleArn=$TASK_ROLE_ARN \
        ECRRepositoryAPIServerURI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-api-server-production \
        ECRRepositoryStreamReceiverURI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-stream-receiver-production \
        ECRRepositoryDriverURI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-driver-production \
        ECRRepositoryMonitoringURI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/financial-streaming-monitoring-production \
        VpcId=vpc-xxxxxxxxx \
        PrivateSubnet1=subnet-xxxxxxxxx \
        PrivateSubnet2=subnet-xxxxxxxxx \
        APIServerDesiredCount=2 \
        StreamReceiverDesiredCount=2 \
        DriverDesiredCount=1 \
        MonitoringDesiredCount=1 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-2
```

### 5. Verify Deployment

```bash
# Get ALB DNS name
ALB_DNS=$(aws cloudformation describe-stacks --stack-name financial-streaming-production-cluster --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerDNS`].OutputValue' --output text)

# Test health endpoints
curl -f http://$ALB_DNS/health
curl -f http://$ALB_DNS:8002/health
curl -f http://$ALB_DNS:8001/health
curl -f http://$ALB_DNS:8080/health

# Test API endpoints
curl -f http://$ALB_DNS/api/v1/stocks
curl -f http://$ALB_DNS:8002/api/v1/stream/status
```

## 🔄 CI/CD Pipeline

### GitHub Actions Setup

1. **Repository Secrets**
   Add the following secrets to your GitHub repository:

   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_ACCOUNT_ID=your_account_id
   ```

2. **Workflow File**
   The CI/CD pipeline is defined in `.github/workflows/deployment.yml`

3. **Automated Deployment**
   - **Push to `develop`**: Deploys to staging
   - **Push to `main`**: Deploys to production
   - **Manual trigger**: Choose environment

### Pipeline Stages

1. **Test and Quality Checks**
   - Unit tests
   - Integration tests
   - API tests
   - Code linting
   - Security scanning

2. **Build and Push Images**
   - Build Docker images
   - Push to ECR
   - Cache optimization

3. **Deploy**
   - Deploy to staging/production
   - Health checks
   - Post-deployment tests

4. **Performance Testing**
   - Load testing
   - Performance validation

5. **Security and Documentation**
   - Vulnerability scanning
   - Dependency checks
   - Documentation generation

## 🔧 Configuration Management

### Environment Variables

The system uses environment-specific configuration:

```bash
# Production
ENVIRONMENT=production
LOG_LEVEL=INFO
ALPHA_VANTAGE_API_KEY=your_api_key
MONGODB_URI=mongodb://your-mongodb-uri
SNS_TOPIC_ARN=arn:aws:sns:region:account:topic

# Staging
ENVIRONMENT=staging
LOG_LEVEL=DEBUG
ALPHA_VANTAGE_API_KEY=your_staging_api_key
MONGODB_URI=mongodb://your-staging-mongodb-uri
SNS_TOPIC_ARN=arn:aws:sns:region:account:staging-topic
```

### AWS Systems Manager Parameter Store

Store sensitive configuration in AWS SSM:

```bash
# Store parameters
aws ssm put-parameter \
    --name "/financial-streaming/production/alpha-vantage-api-key" \
    --value "your-api-key" \
    --type "SecureString" \
    --region us-east-2

aws ssm put-parameter \
    --name "/financial-streaming/production/mongodb-uri" \
    --value "mongodb://your-uri" \
    --type "SecureString" \
    --region us-east-2
```

## 📊 Monitoring and Observability

### CloudWatch Metrics

The deployment includes comprehensive monitoring:

- **ECS Service Metrics**
  - CPU utilization
  - Memory utilization
  - Network I/O
  - Task count

- **Application Load Balancer Metrics**
  - Request count
  - Target response time
  - HTTP status codes
  - Healthy/unhealthy target count

- **Custom Application Metrics**
  - API response times
  - Stream processing rates
  - Error rates
  - Business metrics

### CloudWatch Logs

All services log to CloudWatch:

```
/ecs/financial-streaming-production
├── api-server
├── stream-receiver
├── driver
└── monitoring
```

### Health Checks

Each service exposes health endpoints:

- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health information
- `GET /metrics` - Prometheus metrics

## 🔒 Security Configuration

### IAM Roles and Policies

The deployment creates the following IAM roles:

1. **ECS Task Execution Role**
   - Pull images from ECR
   - Write logs to CloudWatch
   - Access SSM parameters
   - Access Secrets Manager

2. **ECS Task Role**
   - Publish to SNS
   - Access S3 buckets
   - Access other AWS services

3. **ECS Instance Role**
   - Register with ECS cluster
   - Pull images from ECR
   - Write logs to CloudWatch

### Security Groups

- **ALB Security Group**: Allows HTTP/HTTPS from internet
- **ECS Service Security Group**: Allows traffic from ALB
- **Private communication**: Services can communicate internally

### Network Security

- **VPC**: Isolated network environment
- **Public Subnets**: ALB and NAT gateways
- **Private Subnets**: ECS services
- **Security Groups**: Traffic filtering
- **Network ACLs**: Additional network security

## 📈 Auto Scaling

### ECS Service Auto Scaling

Services automatically scale based on CPU utilization:

```yaml
TargetTrackingScalingPolicy:
  TargetValue: 70.0  # 70% CPU utilization
  ScaleOutCooldown: 300  # 5 minutes
  ScaleInCooldown: 300   # 5 minutes
  MinCapacity: 1
  MaxCapacity: 10
```

### Cluster Auto Scaling

The ECS cluster scales based on demand:

```yaml
AutoScalingGroup:
  MinSize: 2
  MaxSize: 10
  DesiredCapacity: 2
  TargetTrackingScalingPolicy:
    TargetValue: 70.0  # 70% CPU utilization
```

## 🚨 Troubleshooting

### Common Issues

1. **Service Not Starting**
   ```bash
   # Check service events
   aws ecs describe-services \
       --cluster financial-streaming-production \
       --services financial-streaming-api-server-production \
       --query 'services[0].events'
   
   # Check task logs
   aws logs tail /ecs/financial-streaming-production --follow
   ```

2. **Health Check Failures**
   ```bash
   # Check target group health
   aws elbv2 describe-target-health \
       --target-group-arn your-target-group-arn
   
   # Check container health
   aws ecs describe-tasks \
       --cluster financial-streaming-production \
       --tasks your-task-arn
   ```

3. **Image Pull Issues**
   ```bash
   # Check ECR permissions
   aws ecr get-login-password --region us-east-2
   
   # Verify image exists
   aws ecr describe-images \
       --repository-name financial-streaming-api-server-production
   ```

### Debug Commands

```bash
# Get service status
aws ecs describe-services \
    --cluster financial-streaming-production \
    --services financial-streaming-api-server-production

# Get task details
aws ecs describe-tasks \
    --cluster financial-streaming-production \
    --tasks $(aws ecs list-tasks --cluster financial-streaming-production --service-name financial-streaming-api-server-production --query 'taskArns' --output text)

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /ecs/financial-streaming-production

# Monitor metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=financial-streaming-api-server-production \
    --start-time $(date -d '1 hour ago' --iso-8601=seconds) \
    --end-time $(date --iso-8601=seconds) \
    --period 300 \
    --statistics Average
```

## 🔄 Rolling Updates

### Blue-Green Deployment

For zero-downtime deployments:

1. **Deploy new version to separate service**
2. **Test new version**
3. **Switch traffic to new version**
4. **Decommission old version**

### Canary Deployment

For gradual rollouts:

1. **Deploy to 10% of traffic**
2. **Monitor metrics**
3. **Gradually increase to 100%**
4. **Rollback if issues detected**

## 📋 Maintenance

### Regular Tasks

1. **Update Base Images**
   ```bash
   # Update Python base image
   docker pull python:3.11-slim
   docker build --no-cache -t financial-streaming-api-server:latest ec2_api_server/
   ```

2. **Rotate Secrets**
   ```bash
   # Update API keys
   aws ssm put-parameter \
       --name "/financial-streaming/production/alpha-vantage-api-key" \
       --value "new-api-key" \
       --type "SecureString" \
       --overwrite
   ```

3. **Clean Up Old Images**
   ```bash
   # Remove images older than 30 days
   aws ecr list-images \
       --repository-name financial-streaming-api-server-production \
       --query 'imageDetails[?imagePushedAt<`'$(date -d '30 days ago' --iso-8601=seconds)'`].imageDigest' \
       --output text | while read digest; do
       aws ecr batch-delete-image \
           --repository-name financial-streaming-api-server-production \
           --image-ids imageDigest=$digest
   done
   ```

### Backup and Recovery

1. **Database Backups**
   ```bash
   # MongoDB backup
   mongodump --uri="your-mongodb-uri" --out=/backup/$(date +%Y%m%d)
   ```

2. **Configuration Backups**
   ```bash
   # Export SSM parameters
   aws ssm get-parameters-by-path \
       --path "/financial-streaming/production" \
       --recursive \
       --with-decryption > config-backup.json
   ```

## 🎯 Performance Optimization

### Resource Allocation

```yaml
# API Server (High CPU/Memory)
CPU: 1024 (1 vCPU)
Memory: 2048 MB

# Stream Receiver (High I/O)
CPU: 512 (0.5 vCPU)
Memory: 1024 MB

# Driver (Low resource)
CPU: 256 (0.25 vCPU)
Memory: 512 MB

# Monitoring (Low resource)
CPU: 256 (0.25 vCPU)
Memory: 512 MB
```

### Auto Scaling Tuning

```yaml
# Aggressive scaling for high traffic
TargetValue: 60.0  # Scale at 60% CPU
ScaleOutCooldown: 180  # 3 minutes
ScaleInCooldown: 300   # 5 minutes

# Conservative scaling for cost optimization
TargetValue: 80.0  # Scale at 80% CPU
ScaleOutCooldown: 300  # 5 minutes
ScaleInCooldown: 600   # 10 minutes
```

## 📞 Support and Monitoring

### Alerts and Notifications

Set up CloudWatch alarms for:

- **High CPU utilization** (>80%)
- **High memory utilization** (>85%)
- **High error rate** (>5%)
- **Service unavailable**
- **Health check failures**

### Contact Information

- **DevOps Team**: devops@company.com
- **On-Call Engineer**: +1-555-0123
- **Emergency Contact**: +1-555-9999

---

**🎉 Your Financial Data Streaming System is now production-ready with comprehensive deployment infrastructure!**

The system includes automated CI/CD pipelines, monitoring, auto-scaling, and security best practices for enterprise-grade reliability. 