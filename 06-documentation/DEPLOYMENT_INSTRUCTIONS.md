# Deployment Instructions
## Complete Setup Guide for Production Deployment

### 🔧 **Prerequisites**
- Docker & Docker Compose installed
- AWS credentials configured
- Alpha Vantage API key
- Minimum 8GB RAM, 4 CPU cores

### ⚡ **Quick Start (Recommended)**
```bash
# 1. Update AWS credentials
./update_aws_credentials.sh

# 2. Start entire system
docker-compose -f docker-compose-simple.yml up -d

# 3. Verify all services are healthy
docker-compose -f docker-compose-simple.yml ps

# 4. Trigger data ingestion
curl -X POST "http://localhost:8000/fetch" \\
  -H "Content-Type: application/json" \\
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]}'

# 5. View real-time dashboard
open http://localhost:3000
```

### 🏗️ **Manual Step-by-Step Setup**

#### Step 1: Infrastructure Services
```bash
# Start databases and messaging
docker-compose -f docker-compose-simple.yml up -d mongodb redis zookeeper kafka
```

#### Step 2: API Server (Data Ingestion)
```bash
# Start data ingestion service
docker-compose -f docker-compose-simple.yml up -d api-server

# Verify health
curl http://localhost:8000/health
```

#### Step 3: Driver (Event Processing)  
```bash
# Start event-driven streaming driver
docker-compose -f docker-compose-simple.yml up -d driver

# Verify health
curl http://localhost:8001/health
```

#### Step 4: Stream Receiver (Real-time Processing)
```bash
# Start real-time stream processor
docker-compose -f docker-compose-simple.yml up -d stream-receiver

# Verify health  
curl http://localhost:8002/health
```

#### Step 5: Monitoring Dashboard
```bash
# Start monitoring and visualization
docker-compose -f docker-compose-simple.yml up -d monitoring

# Access dashboard
open http://localhost:3000
```

### 🧪 **Testing the Complete Pipeline**

#### Test 1: Data Ingestion
```bash
# Trigger stock data fetch
curl -X POST "http://localhost:8000/fetch" \\
  -H "Content-Type: application/json" \\
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'

# Check status
curl http://localhost:8000/status
```

#### Test 2: Times Square Streaming
```bash
# Verify driver started streaming (after 5+ symbols)
curl http://localhost:8001/health

# Should show: "streaming": true
```

#### Test 3: Real-time Processing
```bash
# Check stream receiver records
curl http://localhost:8002/status

# View recent ticks (Times Square style)
curl "http://localhost:8002/api/v1/stream/ticks/recent?limit=5"
```

#### Test 4: Monitoring Dashboard
```bash
# Access live dashboard
curl http://localhost:3000/health

# Open in browser for real-time visualization
open http://localhost:3000
```

### 🔍 **Troubleshooting**

#### Service Health Checks
```bash
# Check all container status
docker-compose -f docker-compose-simple.yml ps

# View logs for specific service
docker-compose -f docker-compose-simple.yml logs api-server
docker-compose -f docker-compose-simple.yml logs driver  
docker-compose -f docker-compose-simple.yml logs stream-receiver
```

#### Common Issues

1. **Driver not streaming**
   - Ensure 5+ symbols in database
   - Check SNS event configuration
   - Verify driver logs

2. **Stream receiver showing 0 records**
   - Check driver is sending ticks
   - Verify network connectivity
   - Check stream-receiver logs

3. **AWS credentials issues**
   - Run `./update_aws_credentials.sh`
   - Verify SNS topic ARN
   - Check AWS token expiration

### 📊 **Performance Monitoring**

#### Key Metrics to Monitor
- **API Server**: Database records, fetch success rate
- **Driver**: Streaming status, symbols ready count  
- **Stream Receiver**: Record count, processing rate
- **System**: CPU, memory, network usage

#### Monitoring Endpoints
```bash
curl http://localhost:8000/status  # API Server metrics
curl http://localhost:8001/health  # Driver status
curl http://localhost:8002/status  # Stream metrics
curl http://localhost:3000/health  # Overall health
```

### 🚀 **Production Deployment**

#### For AWS EC2 Deployment
1. Launch 3 EC2 instances (t3.medium or larger)
2. Install Docker on each instance
3. Deploy services across instances:
   - EC2 #1: API Server + MongoDB
   - EC2 #2: Driver + Kafka  
   - EC2 #3: Stream Receiver + Redis
4. Configure security groups for inter-service communication
5. Set up Application Load Balancer for external access

#### Environment Variables
```bash
# Required for production
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
SNS_TOPIC_ARN=your-topic-arn
ALPHA_VANTAGE_API_KEY=your-api-key
```

### 📋 **Maintenance**

#### Regular Tasks
- Monitor disk usage (MongoDB data growth)
- Rotate logs periodically
- Update AWS credentials before expiration
- Monitor Alpha Vantage API usage limits

#### Backup Strategy
- MongoDB data: Daily automated backups
- Configuration files: Version controlled
- Log archival: Weekly compression and archival
