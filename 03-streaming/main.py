#!/usr/bin/env python3
"""
EC2 Stream Receiver - Real-time Data Processing
==============================================

This is the stream processor that:
- Receives real-time stock ticks from the driver
- Stores data in simulated Accumulo (in-memory buffer)
- Processes and transforms the data
- Sends processed data to Kafka for downstream consumption
- Provides health monitoring and processing status

Think of this as the "data processor" that handles real-time streaming data.
"""

import asyncio
import logging
import os
import aiohttp
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
from contextlib import asynccontextmanager

import redis
import sys
sys.path.append('/app')
from shared.kafka_client import get_kafka_client
from config.config_manager import config
from accumulo_client import SimulatedAccumuloClient

# Pydantic models for request/response
class TickData(BaseModel):
    symbol: str
    price: float
    volume: int
    timestamp: str
    price_change: Optional[float] = None
    stream_type: str = "times_square_simulation"

class KafkaMessage(BaseModel):
    topic: str
    message: Dict
    key: Optional[str] = None

class StreamStatus(BaseModel):
    accumulo_connected: bool
    kafka_producer_connected: bool
    kafka_consumer_connected: bool
    total_ticks_processed: int
    total_messages_sent: int
    timestamp: str

class TickStatistics(BaseModel):
    symbol: str
    total_ticks: int
    latest_price: float
    price_change_24h: float
    volume_24h: int
    last_tick_time: str

# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="EC2 Stream Receiver API",
    description="Real-time stock data processing with simulated Accumulo",
    version="1.0.0"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    logger.info("🚀 Starting EC2 Stream Receiver...")
    
    # Connect to Accumulo
    if accumulo_client.connect():
        logger.info("✅ Connected to Accumulo")
    else:
        logger.error("❌ Failed to connect to Accumulo")
    
    # Connect to Kafka
    if kafka_client.initialize_producer():
        logger.info("✅ Connected to Kafka producer")
    else:
        logger.error("❌ Failed to connect to Kafka producer")
    
    if kafka_client.initialize_consumer():
        logger.info("✅ Connected to Kafka consumer")
    else:
        logger.error("❌ Failed to connect to Kafka consumer")
    
    yield
    
    # Shutdown
    logger.info("🔌 Shutting down EC2 Stream Receiver...")
    accumulo_client.disconnect()

app = FastAPI(
    title="EC2 Stream Receiver API",
    description="Real-time stock data processing with simulated Accumulo",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
kafka_client = get_kafka_client()
accumulo_client = SimulatedAccumuloClient()



@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "EC2 Stream Receiver API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "phase": "4"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    accumulo_status = accumulo_client.get_status()
    kafka_info = kafka_client.get_status()
    return {
        "status": "healthy",
        "accumulo": accumulo_status,
        "kafka": kafka_info,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ticks")
async def get_ticks(symbol: str = None, limit: int = 100):
    """Get stock ticks from Accumulo"""
    try:
        ticks = accumulo_client.read_stock_ticks(symbol=symbol, limit=limit)
        return {
            "ticks": ticks,
            "count": len(ticks),
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting ticks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ticks/{symbol}")
async def get_ticks_by_symbol(symbol: str, limit: int = 50):
    """Get ticks for a specific symbol"""
    try:
        ticks = accumulo_client.read_stock_ticks(symbol=symbol, limit=limit)
        return {
            "symbol": symbol,
            "ticks": ticks,
            "count": len(ticks),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting ticks for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get system status"""
    try:
        accumulo_status = accumulo_client.get_status()
        kafka_info = kafka_client.get_status()
        return {
            "service": "EC2 Stream Receiver",
            "status": "running",
            "phase": "4",
            "accumulo": accumulo_status,
            "kafka": kafka_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ticks")
async def write_tick(tick_data: Dict):
    """Write a stock tick to Accumulo and Kafka"""
    try:
        # Write to Accumulo
        accumulo_success = accumulo_client.write_stock_tick(tick_data)
        
        # Send to Kafka
        kafka_success = kafka_client.send_message(kafka_client.topic_name, tick_data, key=tick_data.get("symbol"))
        
        if accumulo_success and kafka_success:
            return {
                "message": "Tick written successfully",
                "symbol": tick_data.get("symbol"),
                "accumulo": "success",
                "kafka": "success",
                "timestamp": datetime.now().isoformat()
            }
        else:
            status = {
                "accumulo": "success" if accumulo_success else "failed",
                "kafka": "success" if kafka_success else "failed"
            }
            raise HTTPException(status_code=500, detail=f"Partial failure: {status}")
    except Exception as e:
        logger.error(f"❌ Error writing tick: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kafka/messages")
async def get_kafka_messages(limit: int = 10):
    """Get recent messages from Kafka"""
    try:
        messages = kafka_client.consume_messages(timeout_ms=5000, max_messages=limit)
        return {
            "messages": messages,
            "count": len(messages),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting Kafka messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/kafka/send")
async def send_kafka_message(message: Dict):
    """Send a message to Kafka"""
    try:
        success = kafka_client.send_message(kafka_client.topic_name, message, key=message.get("symbol"))
        if success:
            return {
                "message": "Message sent to Kafka successfully",
                "symbol": message.get("symbol"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send message to Kafka")
    except Exception as e:
        logger.error(f"❌ Error sending Kafka message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced REST API endpoints

@app.get("/api/v1/stream/status", response_model=StreamStatus)
async def get_stream_status():
    """Get comprehensive stream processing status"""
    try:
        accumulo_status = accumulo_client.get_status()
        kafka_info = kafka_client.get_status()
        
        return StreamStatus(
            accumulo_connected=accumulo_status.get('connected', False),
            kafka_producer_connected=kafka_info.get('producer_connected', False),
            kafka_consumer_connected=kafka_info.get('consumer_connected', False),
            total_ticks_processed=accumulo_status.get('total_ticks', 0),
            total_messages_sent=kafka_info.get('messages_sent', 0),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting stream status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stream/ticks", response_model=List[TickData])
async def get_all_ticks(limit: int = 100, symbol: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None):
    """Get all ticks with filtering options"""
    try:
        ticks = accumulo_client.read_stock_ticks(symbol=symbol, limit=limit)
        
        # Apply time filtering if provided
        if start_time or end_time:
            filtered_ticks = []
            for tick in ticks:
                tick_time = tick.get('timestamp')
                if start_time and tick_time < start_time:
                    continue
                if end_time and tick_time > end_time:
                    continue
                filtered_ticks.append(tick)
            ticks = filtered_ticks
        
        return [TickData(**tick) for tick in ticks]
    except Exception as e:
        logger.error(f"Error getting ticks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stream/ticks/{symbol}/latest")
async def get_latest_tick(symbol: str):
    """Get the latest tick for a symbol"""
    try:
        ticks = accumulo_client.read_stock_ticks(symbol=symbol, limit=1)
        if not ticks:
            raise HTTPException(status_code=404, detail=f"No ticks found for {symbol}")
        
        return TickData(**ticks[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest tick for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stream/ticks/{symbol}/statistics", response_model=TickStatistics)
async def get_tick_statistics(symbol: str):
    """Get tick statistics for a symbol"""
    try:
        ticks = accumulo_client.read_stock_ticks(symbol=symbol, limit=1000)
        if not ticks:
            raise HTTPException(status_code=404, detail=f"No ticks found for {symbol}")
        
        # Calculate statistics
        total_ticks = len(ticks)
        latest_price = ticks[0].get('price', 0) if ticks else 0
        latest_time = ticks[0].get('timestamp', '') if ticks else ''
        
        # Calculate 24h change (simplified)
        if len(ticks) > 1:
            price_change_24h = latest_price - ticks[-1].get('price', latest_price)
        else:
            price_change_24h = 0
        
        # Calculate 24h volume
        volume_24h = sum(tick.get('volume', 0) for tick in ticks[:24])  # Last 24 ticks
        
        return TickStatistics(
            symbol=symbol,
            total_ticks=total_ticks,
            latest_price=latest_price,
            price_change_24h=price_change_24h,
            volume_24h=volume_24h,
            last_tick_time=latest_time
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tick statistics for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stream/symbols")
async def get_active_symbols():
    """Get all symbols that have tick data"""
    try:
        # Get active symbols from accumulo
        symbols = accumulo_client.get_active_symbols()
        return {
            "symbols": symbols,
            "count": len(symbols),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting active symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stream/ticks/recent")
async def get_recent_ticks(limit: int = 10):
    """Get recent tick data from Accumulo"""
    try:
        ticks = accumulo_client.get_recent_ticks(limit)
        return {
            "ticks": ticks,
            "count": len(ticks),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recent ticks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/stream/ticks", response_model=TickData)
async def create_tick(tick_data: TickData):
    """Create a new tick entry"""
    try:
        # Write to Accumulo
        success = accumulo_client.write_stock_tick(tick_data.dict())
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write tick to Accumulo")
        
        # Send to Kafka
        kafka_client.send_message(tick_data.dict(), key=tick_data.symbol)
        
        return tick_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tick: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stream/kafka/messages")
async def get_kafka_messages_enhanced(limit: int = 10, topic: Optional[str] = None):
    """Get recent Kafka messages with enhanced filtering"""
    try:
        messages = kafka_client.consume_messages(timeout_ms=5000, max_messages=limit)
        return {
            "messages": messages,
            "count": len(messages),
            "topic": topic or config.KAFKA_TOPIC_NAME,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting Kafka messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/stream/kafka/send", response_model=Dict)
async def send_kafka_message_enhanced(message: KafkaMessage):
    """Send a message to Kafka with enhanced options"""
    try:
        success = kafka_client.send_message(message.message, key=message.key or message.message.get("symbol"))
        
        if success:
            return {
                "message": "Message sent to Kafka",
                "topic": message.topic,
                "key": message.key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send message to Kafka")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending Kafka message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stream/accumulo/status")
async def get_accumulo_status():
    """Get detailed Accumulo status"""
    try:
        status = accumulo_client.get_status()
        return {
            "accumulo": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting Accumulo status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stream/performance")
async def get_performance_metrics():
    """Get stream processing performance metrics"""
    try:
        # Get basic metrics
        accumulo_status = accumulo_client.get_status()
        kafka_info = kafka_client.get_status()
        
        # Calculate performance metrics
        total_ticks = accumulo_status.get('total_ticks', 0)
        messages_sent = kafka_info.get('messages_sent', 0)
        
        # Simulate processing rate (ticks per second)
        processing_rate = total_ticks / max(1, (datetime.now() - datetime(2024, 1, 1)).total_seconds())
        
        return {
            "performance": {
                "total_ticks_processed": total_ticks,
                "total_messages_sent": messages_sent,
                "processing_rate_tps": round(processing_rate, 2),
                "accumulo_write_success_rate": 0.99,  # Simulated
                "kafka_send_success_rate": 0.98,      # Simulated
                "average_processing_time_ms": 15      # Simulated
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("🎯 Starting EC2 Stream Receiver with Simulated Accumulo...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.STREAM_RECEIVER_PORT,
        log_level=config.LOG_LEVEL.lower()
    ) 