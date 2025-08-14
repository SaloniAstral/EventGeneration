#!/usr/bin/env python3
"""
Enhanced SNS Event Publisher for Financial Data Streaming System
Integrates with event system for real-time coordination between EC2 instances
"""

import boto3
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

from .event_definitions import (
    EventType, EventSource, BaseEvent, StockDataLoadedEvent, 
    BatchDataCompletedEvent, DataThresholdReachedEvent, 
    StreamingStartedEvent, TickGeneratedEvent, SystemStatusEvent, ErrorEvent,
    create_stock_data_loaded_event, create_batch_completed_event,
    create_threshold_reached_event, create_streaming_started_event,
    create_tick_event, create_system_status_event, create_error_event
)

logger = logging.getLogger(__name__)

class SNSEventPublisher:
    """Enhanced SNS publisher that integrates with event system"""
    
    def __init__(self):
        # AWS Configuration
        self.aws_region = os.getenv('AWS_REGION', 'us-east-2')
        self.sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
        
        # Initialize SNS client
        try:
            self.sns_client = boto3.client(
                'sns',
                region_name=self.aws_region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=os.getenv('AWS_SESSION_TOKEN')
            )
            logger.info(f"✅ SNS client initialized for region: {self.aws_region}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SNS client: {e}")
            self.sns_client = None
    
    def publish_event(self, event: BaseEvent) -> bool:
        """Publish an event to SNS"""
        if not self.sns_client or not self.sns_topic_arn:
            logger.warning("⚠️ SNS not configured, event not published")
            return False
        
        try:
            # Convert event to JSON
            event_json = event.to_json()
            
            # Publish to SNS
            response = self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Message=event_json,
                Subject=f"Financial Data Event: {event.event_type.value}",
                MessageAttributes={
                    'EventType': {
                        'DataType': 'String',
                        'StringValue': event.event_type.value
                    },
                    'EventSource': {
                        'DataType': 'String',
                        'StringValue': event.event_source.value
                    },
                    'Timestamp': {
                        'DataType': 'String',
                        'StringValue': event.timestamp.isoformat()
                    }
                }
            )
            
            logger.info(f"📡 Published event {event.event_type.value} to SNS: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish event to SNS: {e}")
            return False
    
    def publish_stock_data_loaded(self, symbol: str, records_count: int, latest_date: str, latest_price: float) -> bool:
        """Publish stock data loaded event"""
        event = create_stock_data_loaded_event(symbol, records_count, latest_date, latest_price)
        return self.publish_event(event)
    
    def publish_batch_completed(self, symbols_processed: int, successful_symbols: int, total_records: int, symbols: list) -> bool:
        """Publish batch completed event"""
        event = create_batch_completed_event(symbols_processed, successful_symbols, total_records, symbols)
        return self.publish_event(event)
    
    def publish_threshold_reached(self, stock_count: int, threshold: int, symbols: list) -> bool:
        """Publish threshold reached event"""
        event = create_threshold_reached_event(stock_count, threshold, symbols)
        return self.publish_event(event)
    
    def publish_streaming_started(self, stocks_count: int, tick_interval: float, symbols: list) -> bool:
        """Publish streaming started event"""
        event = create_streaming_started_event(stocks_count, tick_interval, symbols)
        return self.publish_event(event)
    
    def publish_tick_generated(self, symbol: str, price: float, price_change: float, tick_number: int) -> bool:
        """Publish tick generated event"""
        event = create_tick_event(symbol, price, price_change, tick_number)
        return self.publish_event(event)
    
    def publish_system_status(self, service_name: str, status: str, message: str, metrics: Dict[str, Any]) -> bool:
        """Publish system status event"""
        event = create_system_status_event(service_name, status, message, metrics)
        return self.publish_event(event)
    
    def publish_error(self, error_type: str, error_message: str, service_name: str, severity: str = "medium") -> bool:
        """Publish error event"""
        event = create_error_event(error_type, error_message, service_name, severity)
        return self.publish_event(event)
    
    def test_connection(self) -> bool:
        """Test SNS connection"""
        if not self.sns_client or not self.sns_topic_arn:
            logger.warning("⚠️ SNS not configured")
            return False
        
        try:
            # Try to get topic attributes
            response = self.sns_client.get_topic_attributes(TopicArn=self.sns_topic_arn)
            logger.info(f"✅ SNS connection test successful: {self.sns_topic_arn}")
            return True
        except Exception as e:
            logger.error(f"❌ SNS connection test failed: {e}")
            return False

# Global SNS publisher instance
sns_publisher = SNSEventPublisher()

def get_sns_publisher() -> SNSEventPublisher:
    """Get the global SNS publisher instance"""
    return sns_publisher

# Convenience functions for backward compatibility
def publish_stock_data_loaded(symbol: str, records_count: int, latest_date: str, latest_price: float) -> bool:
    """Publish stock data loaded event"""
    return sns_publisher.publish_stock_data_loaded(symbol, records_count, latest_date, latest_price)

def publish_batch_completed(symbols_processed: int, successful_symbols: int, total_records: int, symbols: list) -> bool:
    """Publish batch completed event"""
    return sns_publisher.publish_batch_completed(symbols_processed, successful_symbols, total_records, symbols)

def publish_threshold_reached(stock_count: int, threshold: int, symbols: list) -> bool:
    """Publish threshold reached event"""
    return sns_publisher.publish_threshold_reached(stock_count, threshold, symbols)

def publish_streaming_started(stocks_count: int, tick_interval: float, symbols: list) -> bool:
    """Publish streaming started event"""
    return sns_publisher.publish_streaming_started(stocks_count, tick_interval, symbols)

def publish_tick_generated(symbol: str, price: float, price_change: float, tick_number: int) -> bool:
    """Publish tick generated event"""
    return sns_publisher.publish_tick_generated(symbol, price, price_change, tick_number)

def publish_system_status(service_name: str, status: str, message: str, metrics: Dict[str, Any]) -> bool:
    """Publish system status event"""
    return sns_publisher.publish_system_status(service_name, status, message, metrics)

def publish_error(error_type: str, error_message: str, service_name: str, severity: str = "medium") -> bool:
    """Publish error event"""
    return sns_publisher.publish_error(error_type, error_message, service_name, severity) 