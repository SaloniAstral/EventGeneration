# 🧪 MANAGER TESTING GUIDE
## Complete System Verification for Clean Structure

### ⚡ **One-Command Demo**
```bash
# From 05-infrastructure directory:
./update_aws_credentials.sh && docker-compose -f docker-compose-simple.yml up -d
```

### 🔍 **System Health Check**
```bash
# Wait 60 seconds, then verify all services:
curl http://localhost:8000/health  # API Server
curl http://localhost:8001/health  # Driver  
curl http://localhost:8002/health  # Stream Receiver
curl http://localhost:3000/health  # Monitoring Dashboard
```

### 📊 **Data Flow Test**
```bash
# Trigger stock data fetch:
curl -X POST "http://localhost:8000/fetch" -H "Content-Type: application/json" -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'

# Wait 2 minutes, then check streaming:
curl "http://localhost:8002/api/v1/stream/ticks/recent?limit=5"
# Should return real-time tick data
```

### 🎮 **Live Dashboard**
Open http://localhost:3000 in browser to see:
- Real-time metrics and charts
- System health indicators  
- Live streaming visualization

### ✅ **Expected Results**
- **8 containers** all healthy
- **Database records** > 300
- **Real-time ticks** flowing
- **Live dashboard** showing metrics

**This demonstrates a production-ready financial streaming system with advanced AWS architecture!**
