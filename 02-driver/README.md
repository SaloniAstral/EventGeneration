# 02-DRIVER (EC2 Instance #2)  
## Event Processing & Times Square Simulation

### 🎯 **Purpose**
This service listens for SNS events, monitors database for sufficient data (5+ symbols), then starts Times Square-style live streaming simulation.

### 📁 **Key Files**
- `main.py` - Main streaming driver application
- `mongodb_database_reader.py` - Database monitoring
- `stream_simulator.py` - Times Square simulation logic
- `Dockerfile` - Container configuration

### 🚀 **Features**
- ✅ SNS event listening
- ✅ Database threshold monitoring
- ✅ Times Square simulation (100ms intervals)
- ✅ Real-time tick generation
- ✅ Automatic streaming initiation

### 🎮 **Times Square Simulation**
- **Speed**: 100ms per tick (like real NYSE)
- **Style**: Live price updates with random variations
- **Volume**: 1M shares per tick
- **Symbols**: AAPL, MSFT, GOOGL, TSLA, AMZN

### 📊 **Current Status**
- ✅ Streaming ACTIVE
- ✅ 5 symbols ready
- ✅ 2,237+ ticks sent to stream processor
- ✅ Threshold requirement met