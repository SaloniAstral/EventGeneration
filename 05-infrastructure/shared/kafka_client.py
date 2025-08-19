#!/usr/bin/env python3
"""
Shared Kafka Client for Financial Data Streaming System
Consolidated Kafka producer and consumer functionality
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_manager import config

logger = logging.getLogger(__name__)

class SharedKafkaClient:
    """Shared Kafka client for producer and consumer operations"""
    
    def __init__(self):
        self.bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS
        self.topic_name = config.KAFKA_TOPIC_NAME
        self.group_id = config.KAFKA_GROUP_ID
        
        self.producer: Optional[KafkaProducer] = None
        self.consumer: Optional[KafkaConsumer] = None
        
    def initialize_producer(self) -> bool:
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            
            logger.info(f"✅ Kafka producer initialized: {self.bootstrap_servers}")
            return True
            
        except NoBrokersAvailable as e:
            logger.error(f"❌ No Kafka brokers available: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka producer: {e}")
            return False
    
    def initialize_consumer(self, topics: list = None, auto_offset_reset: str = 'latest') -> bool:
        """Initialize Kafka consumer"""
        try:
            topics_to_consume = topics or [self.topic_name]
            
            self.consumer = KafkaConsumer(
                *topics_to_consume,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                consumer_timeout_ms=1000
            )
            
            logger.info(f"✅ Kafka consumer initialized: {topics_to_consume}")
            return True
            
        except NoBrokersAvailable as e:
            logger.error(f"❌ No Kafka brokers available: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka consumer: {e}")
            return False
    
    def send_message(self, topic: str, message: Dict[str, Any], key: str = None) -> bool:
        """Send message to Kafka topic"""
        try:
            if not self.producer:
                if not self.initialize_producer():
                    return False
            
            future = self.producer.send(topic, value=message, key=key)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"✅ Message sent to {topic} [partition: {record_metadata.partition}, offset: {record_metadata.offset}]")
            return True
            
        except KafkaError as e:
            logger.error(f"❌ Kafka error sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False
    
    def send_stock_tick(self, tick_data: Dict[str, Any]) -> bool:
        """Send stock tick data to Kafka"""
        try:
            # Add metadata
            message = {
                'type': 'stock_tick',
                'data': tick_data,
                'timestamp': tick_data.get('timestamp'),
                'symbol': tick_data.get('symbol')
            }
            
            return self.send_message(self.topic_name, message, key=tick_data.get('symbol'))
            
        except Exception as e:
            logger.error(f"❌ Failed to send stock tick: {e}")
            return False
    
    def consume_messages(self, callback: Callable[[Dict[str, Any]], None], timeout_ms: int = 1000, max_messages: int = 10):
        """Consume messages from Kafka with callback"""
        try:
            if not self.consumer:
                if not self.initialize_consumer():
                    return False
            
            message_count = 0
            
            for message in self.consumer:
                try:
                    # Process message
                    callback(message.value)
                    message_count += 1
                    
                    # Check if we've reached max messages
                    if max_messages and message_count >= max_messages:
                        break
                        
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error consuming messages: {e}")
            return False
    
    def get_latest_messages(self, topic: str = None, limit: int = 10) -> list:
        """Get latest messages from topic"""
        try:
            if not self.consumer:
                if not self.initialize_consumer([topic or self.topic_name]):
                    return []
            
            messages = []
            message_count = 0
            
            for message in self.consumer:
                messages.append({
                    'topic': message.topic,
                    'partition': message.partition,
                    'offset': message.offset,
                    'key': message.key,
                    'value': message.value,
                    'timestamp': message.timestamp
                })
                
                message_count += 1
                if message_count >= limit:
                    break
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error getting latest messages: {e}")
            return []
    
    def close_producer(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()
            self.producer = None
            logger.info("🔒 Kafka producer closed")
    
    def close_consumer(self):
        """Close Kafka consumer"""
        if self.consumer:
            self.consumer.close()
            self.consumer = None
            logger.info("🔒 Kafka consumer closed")
    
    def close(self):
        """Close both producer and consumer"""
        self.close_producer()
        self.close_consumer()
    
    def get_status(self) -> Dict[str, Any]:
        """Get Kafka client status"""
        return {
            'bootstrap_servers': self.bootstrap_servers,
            'topic_name': self.topic_name,
            'group_id': self.group_id,
            'producer_connected': self.producer is not None,
            'consumer_connected': self.consumer is not None
        }

# Global instance
kafka_client = SharedKafkaClient()

def get_kafka_client() -> SharedKafkaClient:
    """Get Kafka client instance"""
    return kafka_client

def send_stock_tick(tick_data: Dict[str, Any]) -> bool:
    """Send stock tick data to Kafka"""
    return kafka_client.send_stock_tick(tick_data)

def initialize_kafka_producer() -> bool:
    """Initialize Kafka producer"""
    return kafka_client.initialize_producer()

def initialize_kafka_consumer(topics: list = None) -> bool:
    """Initialize Kafka consumer"""
    return kafka_client.initialize_consumer(topics)

def close_kafka():
    """Close Kafka connections"""
    kafka_client.close() 