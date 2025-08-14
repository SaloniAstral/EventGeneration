# Financial Data Streaming Architecture Flow

## System Overview
Real-time financial data streaming system built on AWS with 3 EC2 instances working together to simulate NYSE Times Square ticker updates.

## Architecture Components

### 1. EC2 API Server (Data Ingestion)
- **Purpose**: Fetch and store historical financial data
- **Function**:
  - Fetch 6+ months data for 50+ stocks from Alpha Vantage
  - Store in PostgreSQL/MongoDB
  - Send SNS event: "Data loaded for AAPL, GOOGL, MSFT..."

### 2. EC2 Driver (Stream Simulation)
- **Purpose**: Simulate real-time streaming like NYC Times Square
- **Function**:
  - Wait for "enough complex data" (30-40 stocks loaded)
  - Start Times Square simulation:
    - AAPL price → 1 second → GOOGL price → 1 second → MSFT price...
  - Feed to Accumulo continuously

### 3. EC2 Stream Receiver (Real-time Processing)
- **Purpose**: Handle continuous streaming data processing
- **Function**:
  - Receive from Accumulo
  - Process through Kafka
  - Provide REST API for processed data

## Data Flow
```
Alpha Vantage API → EC2 API Server → Database + SNS → EC2 Driver → Accumulo → Kafka → EC2 Stream Receiver → REST API
```

## Key Technologies
- **AWS**: EC2, SNS
- **Database**: PostgreSQL/MongoDB (compiled database)
- **Streaming**: Accumulo (buffer), Kafka (processing)
- **API**: Alpha Vantage Premium API
- **Simulation**: Times Square style ticker updates (1 stock/second)

## Requirements
- 50+ stock symbols for complexity
- 6+ months historical data
- Real-time simulation speed
- Continuous streaming loop
- REST API for data access 