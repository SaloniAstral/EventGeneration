# Financial Data Streaming System - API Documentation

Complete REST API documentation for the Financial Data Streaming System with real-time stock data processing.

## 🏗️ Architecture Overview

The system consists of 3 main services, each with its own API:

1. **API Server** (Port 8000) - Data ingestion and management
2. **Stream Receiver** (Port 8002) - Real-time data processing
3. **Driver** (Port 8001) - Times Square streaming simulator

## 📡 API Server Endpoints

Base URL: `http://localhost:8000`

### 🔍 Core Endpoints

#### `GET /`
- **Description**: Root endpoint with system information
- **Response**: System status and version information

#### `GET /health`
- **Description**: Health check endpoint
- **Response**: Service health status

#### `GET /status`
- **Description**: Comprehensive system status
- **Response**: `SystemStatus` object with all service metrics

### 📊 Stock Data Management

#### `GET /api/v1/stocks`
- **Description**: Get status of all stocks in the database
- **Response**: `List[SymbolStatus]`
- **Example**:
```bash
curl http://localhost:8000/api/v1/stocks
```

#### `GET /api/v1/stocks/{symbol}/data`
- **Description**: Get stock data with filtering options
- **Parameters**:
  - `symbol` (path): Stock symbol
  - `limit` (query): Number of records (default: 100)
  - `start_date` (query): Start date filter (YYYY-MM-DD)
  - `end_date` (query): End date filter (YYYY-MM-DD)
- **Response**: `List[StockDataResponse]`
- **Example**:
```bash
curl "http://localhost:8000/api/v1/stocks/AAPL/data?limit=50&start_date=2024-01-01"
```

#### `GET /api/v1/stocks/{symbol}/latest`
- **Description**: Get the latest stock data for a symbol
- **Response**: `StockDataResponse`
- **Example**:
```bash
curl http://localhost:8000/api/v1/stocks/AAPL/latest
```

#### `GET /api/v1/stocks/{symbol}/price`
- **Description**: Get current price for a symbol
- **Response**: Current price with timestamp
- **Example**:
```bash
curl http://localhost:8000/api/v1/stocks/AAPL/price
```

#### `GET /api/v1/stocks/{symbol}/company`
- **Description**: Get detailed company information
- **Response**: `CompanyInfoResponse`
- **Example**:
```bash
curl http://localhost:8000/api/v1/stocks/AAPL/company
```

### 🔍 Search and Discovery

#### `POST /api/v1/search`
- **Description**: Search stocks by symbol or company name
- **Request Body**: `SearchRequest`
- **Response**: `List[SymbolStatus]`
- **Example**:
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AAPL", "limit": 10}'
```

### 📡 Event System

#### `GET /api/v1/events`
- **Description**: Get recent system events
- **Parameters**:
  - `limit` (query): Number of events (default: 50)
  - `event_type` (query): Filter by event type
- **Response**: `List[EventResponse]`
- **Example**:
```bash
curl "http://localhost:8000/api/v1/events?limit=20&event_type=stock_data_loaded"
```

#### `GET /api/v1/events/stats`
- **Description**: Get event system statistics
- **Response**: Event statistics and metrics
- **Example**:
```bash
curl http://localhost:8000/api/v1/events/stats
```

### 🗄️ Database Management

#### `GET /api/v1/database/stats`
- **Description**: Get database statistics
- **Response**: Database metrics and performance data
- **Example**:
```bash
curl http://localhost:8000/api/v1/database/stats
```

#### `GET /api/v1/database/health`
- **Description**: Check database health
- **Response**: Database health status
- **Example**:
```bash
curl http://localhost:8000/api/v1/database/health
```

### 🔄 Data Operations

#### `POST /fetch`
- **Description**: Fetch data for specific symbols
- **Request Body**: `FetchRequest`
- **Response**: Fetch operation results
- **Example**:
```bash
curl -X POST http://localhost:8000/fetch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOGL"], "outputsize": "compact"}'
```

#### `POST /fetch-all`
- **Description**: Fetch data for all configured symbols
- **Response**: Batch fetch operation results
- **Example**:
```bash
curl -X POST http://localhost:8000/fetch-all
```

#### `POST /api/v1/stocks/{symbol}/refresh`
- **Description**: Refresh data for a specific symbol
- **Response**: Refresh operation status
- **Example**:
```bash
curl -X POST http://localhost:8000/api/v1/stocks/AAPL/refresh
```

#### `DELETE /api/v1/stocks/{symbol}`
- **Description**: Delete all data for a symbol
- **Response**: Deletion confirmation
- **Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/stocks/AAPL
```

## 🌊 Stream Receiver Endpoints

Base URL: `http://localhost:8002`

### 🔍 Core Endpoints

#### `GET /`
- **Description**: Root endpoint
- **Response**: Service information

#### `GET /health`
- **Description**: Health check
- **Response**: Service health status

#### `GET /status`
- **Description**: System status
- **Response**: Accumulo and Kafka status

### 📊 Stream Processing

#### `GET /api/v1/stream/status`
- **Description**: Get comprehensive stream processing status
- **Response**: `StreamStatus`
- **Example**:
```bash
curl http://localhost:8002/api/v1/stream/status
```

#### `GET /api/v1/stream/ticks`
- **Description**: Get all ticks with filtering options
- **Parameters**:
  - `limit` (query): Number of ticks (default: 100)
  - `symbol` (query): Filter by symbol
  - `start_time` (query): Start time filter
  - `end_time` (query): End time filter
- **Response**: `List[TickData]`
- **Example**:
```bash
curl "http://localhost:8002/api/v1/stream/ticks?symbol=AAPL&limit=50"
```

#### `GET /api/v1/stream/ticks/{symbol}/latest`
- **Description**: Get the latest tick for a symbol
- **Response**: `TickData`
- **Example**:
```bash
curl http://localhost:8002/api/v1/stream/ticks/AAPL/latest
```

#### `GET /api/v1/stream/ticks/{symbol}/statistics`
- **Description**: Get tick statistics for a symbol
- **Response**: `TickStatistics`
- **Example**:
```bash
curl http://localhost:8002/api/v1/stream/ticks/AAPL/statistics
```

#### `GET /api/v1/stream/symbols`
- **Description**: Get all symbols that have tick data
- **Response**: List of active symbols
- **Example**:
```bash
curl http://localhost:8002/api/v1/stream/symbols
```

#### `POST /api/v1/stream/ticks`
- **Description**: Create a new tick entry
- **Request Body**: `TickData`
- **Response**: `TickData`
- **Example**:
```bash
curl -X POST http://localhost:8002/api/v1/stream/ticks \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "price": 150.25,
    "volume": 1000000,
    "timestamp": "2024-01-15T10:30:00Z",
    "price_change": 1.25
  }'
```

### 🚀 Kafka Integration

#### `GET /api/v1/stream/kafka/messages`
- **Description**: Get recent Kafka messages with enhanced filtering
- **Parameters**:
  - `limit` (query): Number of messages (default: 10)
  - `topic` (query): Topic filter
- **Response**: Kafka messages
- **Example**:
```bash
curl "http://localhost:8002/api/v1/stream/kafka/messages?limit=20"
```

#### `POST /api/v1/stream/kafka/send`
- **Description**: Send a message to Kafka with enhanced options
- **Request Body**: `KafkaMessage`
- **Response**: Send confirmation
- **Example**:
```bash
curl -X POST http://localhost:8002/api/v1/stream/kafka/send \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "stock-ticks",
    "message": {"symbol": "AAPL", "price": 150.25},
    "key": "AAPL"
  }'
```

### 📈 Performance Monitoring

#### `GET /api/v1/stream/performance`
- **Description**: Get stream processing performance metrics
- **Response**: Performance statistics
- **Example**:
```bash
curl http://localhost:8002/api/v1/stream/performance
```

#### `GET /api/v1/stream/accumulo/status`
- **Description**: Get detailed Accumulo status
- **Response**: Accumulo metrics
- **Example**:
```bash
curl http://localhost:8002/api/v1/stream/accumulo/status
```

## 📋 Data Models

### StockDataResponse
```json
{
  "symbol": "AAPL",
  "date": "2024-01-15",
  "open_price": 150.00,
  "high_price": 152.50,
  "low_price": 149.75,
  "close_price": 151.25,
  "volume": 50000000
}
```

### SymbolStatus
```json
{
  "symbol": "AAPL",
  "has_data": true,
  "latest_date": "2024-01-15",
  "latest_price": 151.25,
  "has_company_info": true,
  "company_name": "Apple Inc.",
  "total_records": 100
}
```

### CompanyInfoResponse
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "description": "Apple Inc. designs, manufactures, and markets smartphones...",
  "market_cap": "2.5T",
  "pe_ratio": "25.5"
}
```

### TickData
```json
{
  "symbol": "AAPL",
  "price": 150.25,
  "volume": 1000000,
  "timestamp": "2024-01-15T10:30:00Z",
  "price_change": 1.25,
  "stream_type": "times_square_simulation"
}
```

### EventResponse
```json
{
  "event_id": "stock_loaded_AAPL_1234567890",
  "event_type": "stock_data_loaded",
  "event_source": "ec2_api_server",
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "symbol": "AAPL",
    "records_count": 100,
    "latest_price": 151.25
  }
}
```

## 🔐 Authentication & Security

Currently, the APIs are open for development. For production deployment:

1. **API Keys**: Implement API key authentication
2. **Rate Limiting**: Configure rate limiting per endpoint
3. **HTTPS**: Use HTTPS for all communications
4. **CORS**: Configure CORS policies appropriately

## 📊 Error Handling

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

Error responses include:
```json
{
  "detail": "Error message description"
}
```

## 🚀 Usage Examples

### Complete Workflow Example

1. **Fetch stock data**:
```bash
curl -X POST http://localhost:8000/fetch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOGL", "MSFT"], "outputsize": "compact"}'
```

2. **Check data status**:
```bash
curl http://localhost:8000/api/v1/stocks/AAPL/latest
```

3. **Monitor events**:
```bash
curl http://localhost:8000/api/v1/events?limit=10
```

4. **View stream processing**:
```bash
curl http://localhost:8002/api/v1/stream/status
```

5. **Get real-time ticks**:
```bash
curl http://localhost:8002/api/v1/stream/ticks/AAPL/latest
```

### Monitoring Dashboard

Create a simple monitoring dashboard:

```bash
# System health
curl http://localhost:8000/health
curl http://localhost:8002/health

# Performance metrics
curl http://localhost:8000/api/v1/database/stats
curl http://localhost:8002/api/v1/stream/performance

# Event statistics
curl http://localhost:8000/api/v1/events/stats
```

## 🔧 Configuration

### Environment Variables

```bash
# API Server
MONGODB_URI=mongodb://localhost:27017/stockdata
ALPHA_VANTAGE_API_KEY=your_api_key
AWS_REGION=us-east-2
SNS_TOPIC_ARN=arn:aws:sns:us-east-2:account:topic

# Stream Receiver
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=stock-ticks
ACCUMULO_INSTANCE=stockdata
```

### Docker Deployment

```bash
# Start all services
cd docker
./build-and-deploy.sh deploy

# Access APIs
curl http://localhost:8000/health  # API Server
curl http://localhost:8002/health  # Stream Receiver
```

## 📈 Performance Considerations

1. **Pagination**: Use `limit` parameter for large datasets
2. **Caching**: Implement caching for frequently accessed data
3. **Filtering**: Use date and symbol filters to reduce data transfer
4. **Background Processing**: Use background tasks for data fetching

## 🔄 WebSocket Support

For real-time streaming, consider implementing WebSocket endpoints:

```javascript
// Example WebSocket connection
const ws = new WebSocket('ws://localhost:8002/ws/ticks');
ws.onmessage = function(event) {
    const tick = JSON.parse(event.data);
    console.log('New tick:', tick);
};
```

---

**🎉 Your Financial Data Streaming System now has a complete REST API for all operations!** 