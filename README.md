# 🚀 EventGeneration - Financial Data Streaming System

## 📋 Project Overview

This repository contains a complete **Financial Data Streaming System** built on AWS with real-time data processing capabilities. The system simulates a Times Square-style ticker display with live stock data streaming.

## 🏗️ Architecture

The system consists of **4 main EC2 instances**, each with a dedicated branch:

### 📁 Branch Organization

| Branch | Purpose | Description |
|--------|---------|-------------|
| **`event-generation-main`** | Core Infrastructure | Docker, config, shared utilities |
| **`ec2-api-server`** | Data Ingestion | Fetches stock data from Alpha Vantage API |
| **`ec2-driver`** | Streaming Simulator | Times Square-style ticker display |
| **`ec2-stream-receiver`** | Stream Processing | Real-time data processing and Kafka pipeline |
| **`monitoring-dashboard`** | System Monitoring | Real-time monitoring and health checks |

## 🔧 Technology Stack

- **AWS**: EC2, SNS (event system)
- **MongoDB**: Data storage
- **Kafka**: Real-time streaming
- **FastAPI**: REST APIs
- **Docker**: Containerization
- **Alpha Vantage**: Stock data API

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Astral-Trading/EventGeneration.git
   cd EventGeneration
   ```

2. **Switch to the main branch:**
   ```bash
   git checkout event-generation-main
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

## 🎯 Key Features

- ✅ **Real-time stock data streaming**
- ✅ **Times Square-style ticker simulation**
- ✅ **Event-driven architecture**
- ✅ **Real-time monitoring dashboard**
- ✅ **Scalable AWS infrastructure**
- ✅ **Docker containerization**

## 📖 Documentation

Each branch contains detailed documentation and simple comments explaining the code functionality.

## 🤝 Contributing

This is a demonstration project for financial data streaming systems.

---

**Built for AWS Financial Data Streaming** 🎯
