# 01-API-SERVER (EC2 Instance #1)
## Data Ingestion & REST API Service

### 🎯 **Purpose**
This service fetches stock data from Alpha Vantage API, stores it in MongoDB, and publishes SNS events when new data arrives.

### 📁 **Key Files**
- `main.py` - Main FastAPI application
- `data_service.py` - Alpha Vantage API integration  
- `sns_publisher.py` - AWS SNS event publishing
- `Dockerfile` - Container configuration

### 🚀 **Features**
- ✅ Real-time stock data fetching
- ✅ MongoDB data storage
- ✅ SNS event publishing
- ✅ REST API endpoints
- ✅ Health monitoring

### 🔧 **API Endpoints**
- `GET /health` - Service health check
- `GET /status` - Database and connection status
- `POST /fetch` - Trigger stock data fetching
- `GET /symbols` - List available symbols

### 📊 **Current Status**
- ✅ 500+ records stored for 5 symbols
- ✅ All connections healthy
- ✅ SNS events publishing successfully