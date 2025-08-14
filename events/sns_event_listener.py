#!/usr/bin/env python3
"""
SNS Event Listener for Financial Data Streaming System
Receives and processes events from other EC2 instances via SNS
"""

import boto3
import json
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import os

from .event_handler import get_event_handler
from .event_definitions import EventType, EventSource

logger = logging.getLogger(__name__)

class SNSEventListener:
    """Listens for SNS events and processes them"""
    
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
            logger.info(f"✅ SNS listener initialized for region: {self.aws_region}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SNS listener: {e}")
            self.sns_client = None
        
        # Event handler
        self.event_handler = get_event_handler()
        
        # Listening state
        self.is_listening = False
        self.listen_thread = None
        self.custom_handlers = {}
    
    def start_listening(self, poll_interval: int = 30):
        """Start listening for SNS events"""
        if self.is_listening:
            logger.warning("⚠️ Already listening for events")
            return False
        
        if not self.sns_client or not self.sns_topic_arn:
            logger.error("❌ SNS not configured, cannot start listening")
            return False
        
        self.is_listening = True
        self.listen_thread = threading.Thread(
            target=self._listen_loop,
            args=(poll_interval,),
            daemon=True
        )
        self.listen_thread.start()
        
        logger.info(f"🎧 Started listening for SNS events (poll interval: {poll_interval}s)")
        return True
    
    def stop_listening(self):
        """Stop listening for SNS events"""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=5)
        logger.info("🔇 Stopped listening for SNS events")
    
    def _listen_loop(self, poll_interval: int):
        """Main listening loop"""
        while self.is_listening:
            try:
                self._poll_for_messages()
                time.sleep(poll_interval)
            except Exception as e:
                logger.error(f"❌ Error in listening loop: {e}")
                time.sleep(poll_interval)
    
    def _poll_for_messages(self):
        """Poll for new SNS messages"""
        try:
            # Get messages from SNS topic
            response = self.sns_client.list_subscriptions_by_topic(
                TopicArn=self.sns_topic_arn
            )
            
            # For now, we'll simulate message polling
            # In a real implementation, you'd use SQS or HTTP endpoints
            logger.debug("🔍 Polling for SNS messages...")
            
        except Exception as e:
            logger.error(f"❌ Error polling for messages: {e}")
    
    def register_custom_handler(self, event_type: EventType, handler: Callable):
        """Register a custom handler for specific event types"""
        self.custom_handlers[event_type] = handler
        logger.info(f"✅ Registered custom handler for {event_type.value}")
    
    def unregister_custom_handler(self, event_type: EventType):
        """Unregister a custom handler"""
        if event_type in self.custom_handlers:
            del self.custom_handlers[event_type]
            logger.info(f"🔒 Unregistered custom handler for {event_type.value}")
    
    def process_message(self, message_body: str, message_attributes: Dict = None):
        """Process a received SNS message"""
        try:
            # Parse the message
            event_data = json.loads(message_body)
            
            # Process through event handler
            self.event_handler.process_event_from_json(message_body)
            
            # Call custom handlers if registered
            event_type = EventType(event_data.get('event_type'))
            if event_type in self.custom_handlers:
                try:
                    self.custom_handlers[event_type](event_data)
                except Exception as e:
                    logger.error(f"❌ Custom handler error for {event_type.value}: {e}")
            
            logger.info(f"📨 Processed SNS message: {event_data.get('event_type')}")
            
        except Exception as e:
            logger.error(f"❌ Error processing SNS message: {e}")
    
    def get_listening_status(self) -> Dict[str, Any]:
        """Get current listening status"""
        return {
            'is_listening': self.is_listening,
            'sns_configured': self.sns_client is not None and self.sns_topic_arn is not None,
            'topic_arn': self.sns_topic_arn,
            'region': self.aws_region,
            'custom_handlers': list(self.custom_handlers.keys())
        }

# Global SNS listener instance
sns_listener = SNSEventListener()

def get_sns_listener() -> SNSEventListener:
    """Get the global SNS listener instance"""
    return sns_listener

# Convenience functions
def start_event_listening(poll_interval: int = 30) -> bool:
    """Start listening for SNS events"""
    return sns_listener.start_listening(poll_interval)

def stop_event_listening():
    """Stop listening for SNS events"""
    sns_listener.stop_listening()

def register_custom_event_handler(event_type: EventType, handler: Callable):
    """Register a custom event handler"""
    sns_listener.register_custom_handler(event_type, handler)

def unregister_custom_event_handler(event_type: EventType):
    """Unregister a custom event handler"""
    sns_listener.unregister_custom_handler(event_type)

# Example custom handlers for different services
def api_server_event_handler(event_data: Dict[str, Any]):
    """Custom handler for API server events"""
    event_type = event_data.get('event_type')
    if event_type == 'batch_data_completed':
        logger.info(f"🎯 API Server: Batch completed with {event_data['metadata']['successful_symbols']} symbols")
    elif event_type == 'stock_data_loaded':
        logger.info(f"📈 API Server: Stock data loaded for {event_data['metadata']['symbol']}")

def driver_event_handler(event_data: Dict[str, Any]):
    """Custom handler for driver events"""
    event_type = event_data.get('event_type')
    if event_type == 'streaming_started':
        logger.info(f"🎬 Driver: Streaming started with {event_data['metadata']['stocks_count']} stocks")
    elif event_type == 'tick_generated':
        logger.debug(f"📈 Driver: Tick generated for {event_data['metadata']['symbol']}")

def stream_receiver_event_handler(event_data: Dict[str, Any]):
    """Custom handler for stream receiver events"""
    event_type = event_data.get('event_type')
    if event_type == 'system_status_update':
        logger.info(f"📊 Stream Receiver: Status update for {event_data['metadata']['service_name']}")

# Register example handlers
def register_example_handlers():
    """Register example event handlers"""
    register_custom_event_handler(EventType.BATCH_DATA_COMPLETED, api_server_event_handler)
    register_custom_event_handler(EventType.STOCK_DATA_LOADED, api_server_event_handler)
    register_custom_event_handler(EventType.STREAMING_STARTED, driver_event_handler)
    register_custom_event_handler(EventType.TICK_GENERATED, driver_event_handler)
    register_custom_event_handler(EventType.SYSTEM_STATUS_UPDATE, stream_receiver_event_handler)
    logger.info("✅ Example event handlers registered")

# Initialize example handlers
register_example_handlers() 