# Financial Data Streaming System - Docker Deployment

This directory contains Docker configurations for deploying the Financial Data Streaming System on AWS or any containerized environment.

## 🏗️ Architecture

The system consists of 4 main services:

1. **MongoDB** - Database for storing stock data and events
2. **API Server** - Data ingestion service (port 8000)
3. **Driver** - Times Square streaming simulator (port 8001)
4. **Stream Receiver** - Real-time data processing (port 8002)
5. **Nginx** - Reverse proxy and load balancer (port 80)

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- AWS CLI configured (for SNS events)
- Alpha Vantage API key

### 1. Build and Deploy

```bash
# Navigate to docker directory
cd docker

# Full deployment (build + start + health check)
./build-and-deploy.sh deploy

# Or step by step:
./build-and-deploy.sh build    # Build images
./build-and-deploy.sh start    # Start services
./build-and-deploy.sh health   # Check health
./build-and-deploy.sh status   # Show status
```

### 2. Access Services

- **API Server**: http://localhost:8000
- **Stream Receiver**: http://localhost:8002
- **Nginx Proxy**: http://localhost:80
- **Health Checks**: 
  - http://localhost:8000/health
  - http://localhost:8002/health
  - http://localhost/status

### 3. View Logs

```bash
./build-and-deploy.sh logs
```

### 4. Stop Services

```bash
./build-and-deploy.sh stop
```

## 📁 File Structure

```
docker/
├── docker-compose.yml         # Service orchestration
├── nginx.conf                 # Nginx configuration
├── init-mongo.js              # MongoDB initialization
├── build-and-deploy.sh        # Deployment script
└── README.md                  # This file

Note: Each service has its own Dockerfile in its directory
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# AWS Configuration
AWS_REGION=us-east-2
SNS_TOPIC_ARN=arn:aws:sns:us-east-2:000936194577:financial-data-events

# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=your_api_key_here

# MongoDB Configuration
MONGODB_URI=mongodb://admin:password123@mongodb:27017/stockdata?authSource=admin
MONGODB_DATABASE=stockdata

# Streaming Configuration
STOCK_THRESHOLD=5
TICK_INTERVAL=1.0
```

### Service Configuration

Each service can be configured independently:

#### API Server
- **Port**: 8000
- **Health Check**: `/health`
- **Dependencies**: MongoDB

#### Driver
- **Port**: 8001
- **Dependencies**: MongoDB, API Server
- **Configuration**: Stock threshold, tick interval

#### Stream Receiver
- **Port**: 8002
- **Health Check**: `/health`
- **Dependencies**: MongoDB

#### Nginx
- **Port**: 80
- **Features**: Load balancing, rate limiting, WebSocket support
- **Status**: `/status`

## 🐳 Docker Images

### Building Images

```bash
# Build all images
docker build -f ec2-api-server/Dockerfile -t financial-api-server:latest ./ec2-api-server
docker build -f ec2-driver/Dockerfile -t financial-driver:latest ./ec2-driver
docker build -f ec2-stream-receiver/Dockerfile -t financial-stream-receiver:latest ./ec2-stream-receiver
```

### Image Details

- **Base Image**: `python:3.11-slim`
- **Security**: Non-root user (`appuser`)
- **Health Checks**: Built-in health monitoring
- **Optimization**: Multi-stage builds for smaller images

## 📊 Monitoring

### Health Checks

All services include health check endpoints:

```bash
# Check individual services
curl http://localhost:8000/health  # API Server
curl http://localhost:8002/health  # Stream Receiver

# Check via Nginx
curl http://localhost/health       # Main health check
curl http://localhost/status       # Nginx status
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api-server
docker-compose logs -f driver
docker-compose logs -f stream-receiver
```

## 🔄 Deployment Commands

### Development

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api-server

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production

```bash
# Full deployment
./build-and-deploy.sh deploy

# Update services
./build-and-deploy.sh build
./build-and-deploy.sh restart

# Cleanup
./build-and-deploy.sh cleanup
```

## 🚀 AWS Deployment

### ECS Deployment

1. **Build and Push Images**:
```bash
# Tag images for ECR
docker tag financial-api-server:latest your-account.dkr.ecr.us-east-2.amazonaws.com/financial-api-server:latest

# Push to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-2.amazonaws.com
docker push your-account.dkr.ecr.us-east-2.amazonaws.com/financial-api-server:latest
```

2. **Create ECS Task Definitions**:
   - Use the provided Dockerfiles
   - Configure environment variables
   - Set up service discovery

3. **Deploy to ECS**:
   - Create ECS clusters
   - Deploy services
   - Configure load balancers

### EKS Deployment

1. **Create Kubernetes manifests**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: financial-api-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: financial-api-server
  template:
    metadata:
      labels:
        app: financial-api-server
    spec:
      containers:
      - name: api-server
        image: financial-api-server:latest
        ports:
        - containerPort: 8000
```

2. **Deploy to EKS**:
```bash
kubectl apply -f k8s/
```

## 🔒 Security

### Best Practices

- **Non-root users**: All containers run as non-root
- **Secrets management**: Use AWS Secrets Manager for sensitive data
- **Network isolation**: Services communicate via internal network
- **Rate limiting**: Nginx provides rate limiting
- **Health checks**: All services have health monitoring

### Security Configuration

```bash
# Run with security options
docker run --security-opt=no-new-privileges \
           --cap-drop=ALL \
           -p 8000:8000 \
           financial-api-server:latest
```

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**:
```bash
# Check port usage
netstat -tulpn | grep :8000
```

2. **MongoDB connection issues**:
```bash
# Check MongoDB logs
docker-compose logs mongodb
```

3. **Service not starting**:
```bash
# Check service logs
docker-compose logs api-server
```

4. **Health check failures**:
```bash
# Check service status
./build-and-deploy.sh health
```

### Debug Commands

```bash
# Enter container
docker-compose exec api-server bash

# Check environment variables
docker-compose exec api-server env

# Check network connectivity
docker-compose exec api-server ping mongodb
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale API Server
docker-compose up -d --scale api-server=3

# Scale Stream Receiver
docker-compose up -d --scale stream-receiver=2
```

### Load Balancing

Nginx automatically load balances between multiple instances:

```nginx
upstream api_servers {
    server api-server:8000;
    server api-server:8000;
    server api-server:8000;
}
```

## 🔄 Updates

### Rolling Updates

```bash
# Build new images
./build-and-deploy.sh build

# Update services
docker-compose up -d --no-deps api-server
```

### Zero-Downtime Deployment

```bash
# Blue-green deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📞 Support

For issues or questions:

1. Check the logs: `./build-and-deploy.sh logs`
2. Verify configuration: `./build-and-deploy.sh health`
3. Review this documentation
4. Check the main project README

---

**🎉 Your Financial Data Streaming System is now containerized and ready for production deployment!** 