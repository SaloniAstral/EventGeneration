#!/usr/bin/env python3
"""
Test Event System for Financial Data Streaming
Demonstrates real-time coordination between EC2 instances
"""

import time
import logging
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .event_definitions import (
    EventType, EventSource, create_stock_data_loaded_event,
    create_batch_completed_event, create_threshold_reached_event,
    create_streaming_started_event, create_tick_event
)
from .event_handler import get_event_handler
from .sns_event_publisher import get_sns_publisher
from .sns_event_listener import get_sns_listener

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_event_creation():
    """Test creating different types of events"""
    logger.info("🧪 Testing Event Creation...")
    
    # Test stock data loaded event
    stock_event = create_stock_data_loaded_event(
        symbol="AAPL",
        records_count=100,
        latest_date="2024-01-15",
        latest_price=150.25
    )
    logger.info(f"✅ Created stock event: {stock_event.event_id}")
    
    # Test batch completed event
    batch_event = create_batch_completed_event(
        symbols_processed=10,
        successful_symbols=8,
        total_records=800,
        symbols=["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "NFLX", "AMD"]
    )
    logger.info(f"✅ Created batch event: {batch_event.event_id}")
    
    # Test threshold reached event
    threshold_event = create_threshold_reached_event(
        stock_count=15,
        threshold=10,
        symbols=["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "NFLX", "AMD", "INTC", "ORCL", "CRM", "ADBE", "PYPL", "UBER", "SNOW"]
    )
    logger.info(f"✅ Created threshold event: {threshold_event.event_id}")
    
    # Test streaming started event
    streaming_event = create_streaming_started_event(
        stocks_count=15,
        tick_interval=1.0,
        symbols=["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "NFLX", "AMD", "INTC", "ORCL", "CRM", "ADBE", "PYPL", "UBER", "SNOW"]
    )
    logger.info(f"✅ Created streaming event: {streaming_event.event_id}")
    
    # Test tick event
    tick_event = create_tick_event(
        symbol="AAPL",
        price=150.25,
        price_change=1.25,
        tick_number=42
    )
    logger.info(f"✅ Created tick event: {tick_event.event_id}")
    
    return [stock_event, batch_event, threshold_event, streaming_event, tick_event]

def test_event_processing():
    """Test processing events through the event handler"""
    logger.info("🧪 Testing Event Processing...")
    
    # Get event handler
    handler = get_event_handler()
    
    # Create test events
    events = test_event_creation()
    
    # Process each event
    for event in events:
        logger.info(f"📡 Processing event: {event.event_type.value}")
        handler.process_event(event)
        time.sleep(0.5)  # Small delay between events
    
    # Get event statistics
    stats = handler.get_event_stats()
    logger.info(f"📊 Event Statistics: {stats}")

def test_sns_publisher():
    """Test SNS event publishing"""
    logger.info("🧪 Testing SNS Event Publishing...")
    
    # Get SNS publisher
    publisher = get_sns_publisher()
    
    # Test connection
    if publisher.test_connection():
        logger.info("✅ SNS connection successful")
        
        # Test publishing events
        try:
            # Test stock data loaded
            success = publisher.publish_stock_data_loaded("AAPL", 100, "2024-01-15", 150.25)
            logger.info(f"📡 Stock data event published: {success}")
            
            # Test batch completed
            success = publisher.publish_batch_completed(10, 8, 800, ["AAPL", "GOOGL", "MSFT"])
            logger.info(f"📡 Batch completed event published: {success}")
            
            # Test threshold reached
            success = publisher.publish_threshold_reached(15, 10, ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"])
            logger.info(f"📡 Threshold reached event published: {success}")
            
        except Exception as e:
            logger.error(f"❌ Error publishing events: {e}")
    else:
        logger.warning("⚠️ SNS not configured, skipping publishing tests")

def test_sns_listener():
    """Test SNS event listening"""
    logger.info("🧪 Testing SNS Event Listening...")
    
    # Get SNS listener
    listener = get_sns_listener()
    
    # Get listening status
    status = listener.get_listening_status()
    logger.info(f"📡 Listener Status: {status}")
    
    # Test starting listener
    if status['sns_configured']:
        success = listener.start_listening(poll_interval=10)
        logger.info(f"🎧 Started listening: {success}")
        
        # Let it run for a few seconds
        time.sleep(5)
        
        # Stop listening
        listener.stop_listening()
        logger.info("🔇 Stopped listening")
    else:
        logger.warning("⚠️ SNS not configured, skipping listener tests")

def test_event_coordination():
    """Test real-time coordination between services"""
    logger.info("🧪 Testing Event Coordination...")
    
    # Simulate API Server events
    logger.info("📡 Simulating API Server events...")
    
    # Simulate stock data loaded
    stock_event = create_stock_data_loaded_event("AAPL", 100, "2024-01-15", 150.25)
    get_event_handler().process_event(stock_event)
    
    # Simulate batch completed
    batch_event = create_batch_completed_event(10, 8, 800, ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"])
    get_event_handler().process_event(batch_event)
    
    time.sleep(1)
    
    # Simulate Driver events
    logger.info("📡 Simulating Driver events...")
    
    # Simulate threshold reached
    threshold_event = create_threshold_reached_event(15, 10, ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"])
    get_event_handler().process_event(threshold_event)
    
    # Simulate streaming started
    streaming_event = create_streaming_started_event(15, 1.0, ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"])
    get_event_handler().process_event(streaming_event)
    
    time.sleep(1)
    
    # Simulate tick events
    logger.info("📡 Simulating tick events...")
    for i in range(5):
        tick_event = create_tick_event(f"STOCK{i%5}", 100 + i, 1.0 + i*0.1, i+1)
        get_event_handler().process_event(tick_event)
        time.sleep(0.2)
    
    # Get final statistics
    stats = get_event_handler().get_event_stats()
    logger.info(f"📊 Final Event Statistics: {stats}")

def main():
    """Run all event system tests"""
    logger.info("🚀 Starting Event System Tests...")
    logger.info("=" * 50)
    
    try:
        # Test 1: Event Creation
        test_event_creation()
        logger.info("-" * 30)
        
        # Test 2: Event Processing
        test_event_processing()
        logger.info("-" * 30)
        
        # Test 3: SNS Publisher
        test_sns_publisher()
        logger.info("-" * 30)
        
        # Test 4: SNS Listener
        test_sns_listener()
        logger.info("-" * 30)
        
        # Test 5: Event Coordination
        test_event_coordination()
        logger.info("-" * 30)
        
        logger.info("✅ All Event System tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 