# 🚀 EventGeneration - Financial Data Streaming System

## 📋 Project Overview

This repository contains a complete **Financial Data Streaming System** built on AWS with real-time data processing capabilities. The system simulates a Times Square-style ticker display with live stock data streaming.

## 🏗️ Architecture

The system consists of **4 main EC2 instances**, each with a dedicated branch:

### 📁 Branch Organization

| Branch | Purpose | Description |
|--------|---------|-------------|
| **`main`** | Core Infrastructure | Docker, config, shared utilities |
| **`ec2-api-server`** | Data Ingestion | Fetches stock data from Alpha Vantage API |
| **`ec2-driver`** | Streaming Simulator | Times Square-style ticker display |
| **`ec2-stream-receiver`** | Stream Processing | Real-time data processing and Kafka pipeline |
| **`monitoring-dashboard`** | System Monitoring | Real-time monitoring and health checks |

**⚠️ Important:** Each branch contains only its specific EC2 instance code + shared infrastructure. 

**💡 Pro Tip:** GitHub's "Download ZIP" only gives you the main branch. Use our **Complete ZIP** to get ALL EC2 instance code in one package!

## 🔧 Technology Stack

- **AWS**: EC2, SNS (event system)
- **MongoDB**: Data storage
- **Kafka**: Real-time streaming
- **FastAPI**: REST APIs
- **Docker**: Containerization
- **Alpha Vantage**: Stock data API

## 🚀 Quick Start

### **Option 1: Download Complete ZIP (Recommended for Non-Developers)**
**Get ALL your code without Git knowledge!**

📦 **[Download Complete ZIP](EventGeneration-Complete-AllCode.zip)** - Contains all EC2 instance code organized by folder

**What's in the ZIP:**
- ✅ **main/** - Core infrastructure
- ✅ **ec2-api-server/** - Data ingestion & REST API
- ✅ **ec2-driver/** - Times Square streaming simulator
- ✅ **ec2-stream-receiver/** - Real-time stream processing
- ✅ **monitoring-dashboard/** - System monitoring

### **Option 2: Git Clone (For Developers)**
1. **Clone the repository:**
   ```bash
   git clone https://github.com/SaloniAstral/EventGeneration.git
   cd EventGeneration
   ```

2. **Access all branches (IMPORTANT!):**
   ```bash
   # See all available branches
   git branch -r
   
   # Switch to specific EC2 instance branches
   git checkout ec2-api-server      # Data ingestion
   git checkout ec2-driver          # Streaming simulator
   git checkout ec2-stream-receiver # Stream processing
   git checkout monitoring-dashboard # System monitoring
   ```

3. **Start the system:**
   ```bash
   ./quick_start.sh
   ```

## 📊 System Flow

1. **Data Ingestion** (`ec2-api-server`): Fetches stock data from Alpha Vantage
2. **Event Notification**: Sends SNS events when data is ready
3. **Streaming Simulation** (`ec2-driver`): Simulates Times Square ticker display
4. **Real-time Processing** (`ec2-stream-receiver`): Processes streaming data
5. **Monitoring** (`monitoring-dashboard`): Provides real-time system monitoring

## 📦 **Complete ZIP Package Structure**

When you download our **Complete ZIP**, you get this organized structure:

```
EventGeneration-Complete-AllCode/
├── main/                           # Core infrastructure
│   ├── config/                     # Configuration management
│   ├── database/                   # MongoDB manager
│   ├── shared/                     # Kafka client & utilities
│   ├── docker/                     # Docker configuration
│   └── docs/                       # Documentation
│
├── ec2-api-server/                 # Data ingestion & REST API
│   ├── main.py                     # FastAPI server
│   ├── alpha_vantage_client.py     # Stock data fetcher
│   ├── data_service.py             # Data flow orchestrator
│   └── sns_publisher.py            # AWS SNS events
│
├── ec2-driver/                     # Times Square streaming simulator
│   ├── main.py                     # Streaming simulator
│   ├── mongodb_database_reader.py  # Database reader
│   ├── config/                     # Configuration
│   ├── shared/                     # Shared utilities
│   └── database/                   # MongoDB manager
│
├── ec2-stream-receiver/            # Real-time stream processing
│   ├── main.py                     # Stream processor
│   ├── accumulo_client.py          # In-memory buffer
│   ├── config/                     # Configuration
│   ├── shared/                     # Shared utilities
│   └── database/                   # MongoDB manager
│
└── monitoring-dashboard/            # System monitoring
    ├── monitoring_dashboard.py      # Main dashboard
    ├── health_checker.py            # Health monitoring
    ├── metrics_collector.py         # Performance metrics
    ├── config/                      # Configuration
    ├── shared/                      # Shared utilities
    └── database/                    # MongoDB manager
```

## 🎯 Key Features

- ✅ **Real-time stock data streaming**
- ✅ **Times Square-style ticker simulation**
- ✅ **Event-driven architecture**
- ✅ **Real-time monitoring dashboard**
- ✅ **Scalable AWS infrastructure**
- ✅ **Docker containerization**

## 📖 Documentation

Each branch contains detailed documentation and simple comments explaining the code functionality.

## 🔧 Troubleshooting

### **"I only see main branch files!"**
If you only see the main branch content, you need to access other branches:

```bash
# List all available branches
git branch -r

# Switch to see EC2-API-Server code
git checkout ec2-api-server

# Switch to see EC2-Driver code  
git checkout ec2-driver

# Switch to see EC2-Stream-Receiver code
git checkout ec2-stream-receiver

# Switch to see Monitoring-Dashboard code
git checkout monitoring-dashboard
```

### **"How do I see all code at once?"**
Each branch contains only its specific functionality. This is intentional for clean organization. Switch between branches to explore different components.

## 🤝 Contributing

This is a demonstration project for financial data streaming systems.

---

**Built for AWS Financial Data Streaming** 🎯
