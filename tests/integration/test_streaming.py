#!/usr/bin/env python3
"""
Integration Tests for Streaming Components
Tests Kafka and Accumulo integration
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from shared.kafka_client import SharedKafkaClient
from ec2_stream_receiver.real_accumulo_client import RealAccumuloClient

@pytest.mark.integration
class TestStreamingIntegration:
    """Integration tests for streaming components"""
    
    @pytest.fixture(scope="class")
    async def kafka_client(self):
        """Initialize Kafka client"""
        client = SharedKafkaClient()
        assert client.initialize_producer(), "Failed to initialize Kafka producer"
        assert client.initialize_consumer(), "Failed to initialize Kafka consumer"
        yield client
        client.close()
    
    @pytest.fixture(scope="class")
    async def accumulo_client(self):
        """Initialize Accumulo client"""
        client = RealAccumuloClient()
        assert client.connect(), "Failed to connect to Accumulo"
        yield client
        client.disconnect()
    
    async def test_kafka_producer_consumer(self, kafka_client):
        """Test Kafka producer and consumer integration"""
        # Test data
        test_message = {
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send message
        success = kafka_client.send_message(
            topic="test-stock-ticks",
            message=test_message,
            key="AAPL"
        )
        assert success, "Failed to send message to Kafka"
        
        # Receive message
        messages = kafka_client.get_latest_messages(limit=1)
        assert len(messages) == 1, "Failed to receive message from Kafka"
        assert messages[0]["symbol"] == "AAPL", "Received wrong message"
    
    async def test_accumulo_write_read(self, accumulo_client):
        """Test Accumulo write and read operations"""
        # Test data
        test_tick = {
            "symbol": "GOOGL",
            "price": 2500.0,
            "volume": 1000,
            "timestamp": datetime.now().isoformat(),
            "tick_number": 1,
            "price_change": 10.0,
            "current_price": 2510.0,
            "stream_type": "test"
        }
        
        # Write tick
        success = accumulo_client.write_stock_tick(test_tick)
        assert success, "Failed to write tick to Accumulo"
        
        # Read ticks
        ticks = accumulo_client.read_stock_ticks(symbol="GOOGL", limit=1)
        assert len(ticks) == 1, "Failed to read tick from Accumulo"
        assert ticks[0]["symbol"] == "GOOGL", "Read wrong tick data"
    
    async def test_streaming_pipeline(self, kafka_client, accumulo_client):
        """Test complete streaming pipeline"""
        # Test data
        test_ticks = [
            {
                "symbol": "MSFT",
                "price": 300.0,
                "volume": 500,
                "timestamp": datetime.now().isoformat(),
                "tick_number": i,
                "price_change": 1.0,
                "current_price": 301.0,
                "stream_type": "test"
            }
            for i in range(5)
        ]
        
        # Send ticks through Kafka
        for tick in test_ticks:
            success = kafka_client.send_message(
                topic="test-stock-ticks",
                message=tick,
                key="MSFT"
            )
            assert success, f"Failed to send tick {tick['tick_number']} to Kafka"
        
        # Write ticks to Accumulo
        for tick in test_ticks:
            success = accumulo_client.write_stock_tick(tick)
            assert success, f"Failed to write tick {tick['tick_number']} to Accumulo"
        
        # Verify Kafka messages
        messages = kafka_client.get_latest_messages(limit=5)
        assert len(messages) == 5, "Failed to receive all messages from Kafka"
        assert all(m["symbol"] == "MSFT" for m in messages), "Received wrong messages"
        
        # Verify Accumulo data
        ticks = accumulo_client.read_stock_ticks(symbol="MSFT", limit=5)
        assert len(ticks) == 5, "Failed to read all ticks from Accumulo"
        assert all(t["symbol"] == "MSFT" for t in ticks), "Read wrong tick data"
    
    async def test_error_handling(self, kafka_client, accumulo_client):
        """Test error handling in streaming pipeline"""
        # Test invalid Kafka message
        with pytest.raises(Exception):
            kafka_client.send_message(
                topic="test-stock-ticks",
                message={"invalid": "message"},
                key=None
            )
        
        # Test invalid Accumulo write
        with pytest.raises(Exception):
            accumulo_client.write_stock_tick({"invalid": "tick"})
        
        # Test non-existent symbol
        ticks = accumulo_client.read_stock_ticks(symbol="NONEXISTENT")
        assert len(ticks) == 0, "Should return empty list for non-existent symbol"
    
    async def test_performance(self, kafka_client, accumulo_client):
        """Test streaming performance"""
        # Generate test data
        test_ticks = [
            {
                "symbol": "PERF",
                "price": 100.0,
                "volume": 100,
                "timestamp": datetime.now().isoformat(),
                "tick_number": i,
                "price_change": 0.1,
                "current_price": 100.1,
                "stream_type": "performance_test"
            }
            for i in range(100)
        ]
        
        # Measure Kafka performance
        start_time = datetime.now()
        for tick in test_ticks:
            kafka_client.send_message(
                topic="test-stock-ticks",
                message=tick,
                key="PERF"
            )
        kafka_time = (datetime.now() - start_time).total_seconds()
        assert kafka_time < 5.0, "Kafka writes too slow"
        
        # Measure Accumulo performance
        start_time = datetime.now()
        for tick in test_ticks:
            accumulo_client.write_stock_tick(tick)
        accumulo_time = (datetime.now() - start_time).total_seconds()
        assert accumulo_time < 10.0, "Accumulo writes too slow"
        
        # Verify data consistency
        kafka_messages = kafka_client.get_latest_messages(limit=100)
        accumulo_ticks = accumulo_client.read_stock_ticks(symbol="PERF", limit=100)
        
        assert len(kafka_messages) == len(accumulo_ticks) == 100, "Data loss detected"
        assert all(
            k["tick_number"] == a["tick_number"]
            for k, a in zip(kafka_messages, accumulo_ticks)
        ), "Data inconsistency detected"