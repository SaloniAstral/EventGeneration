#!/usr/bin/env python3
"""
Event Handler for Financial Data Streaming System
Processes and coordinates events between EC2 instances
"""

import json
import logging
from typing import Dict, Any, Callable, List
from datetime import datetime
from dataclasses import asdict

from .event_definitions import (
    EventType, EventSource, BaseEvent, StockDataLoadedEvent, 
    BatchDataCompletedEvent, DataThresholdReachedEvent, 
    StreamingStartedEvent, TickGeneratedEvent, SystemStatusEvent, ErrorEvent
)

logger = logging.getLogger(__name__)

class EventHandler:
    """Handles events and coordinates between EC2 instances"""
    
    def __init__(self):
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[BaseEvent] = []
        self.max_history = 1000  # Keep last 1000 events
        
    def register_handler(self, event_type: EventType, handler: Callable[[BaseEvent], None]):
        """Register a handler for a specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"✅ Registered handler for {event_type.value}")
    
    def unregister_handler(self, event_type: EventType, handler: Callable[[BaseEvent], None]):
        """Unregister a handler for a specific event type"""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            logger.info(f"🔒 Unregistered handler for {event_type.value}")
    
    def process_event(self, event: BaseEvent):
        """Process an event and call all registered handlers"""
        try:
            # Add to history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
            
            # Log the event
            logger.info(f"📡 Processing event: {event.event_type.value} from {event.event_source.value}")
            
            # Call registered handlers
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"❌ Handler error for {event.event_type.value}: {e}")
            else:
                logger.debug(f"⚠️ No handlers registered for {event.event_type.value}")
                
        except Exception as e:
            logger.error(f"❌ Error processing event: {e}")
    
    def process_event_from_json(self, event_json: str):
        """Process an event from JSON string"""
        try:
            event_data = json.loads(event_json)
            event = self._create_event_from_dict(event_data)
            if event:
                self.process_event(event)
        except Exception as e:
            logger.error(f"❌ Error processing event from JSON: {e}")
    
    def _create_event_from_dict(self, event_data: Dict[str, Any]) -> BaseEvent:
        """Create an event object from dictionary"""
        try:
            event_type = EventType(event_data.get('event_type'))
            event_source = EventSource(event_data.get('event_source'))
            
            if event_type == EventType.STOCK_DATA_LOADED:
                return StockDataLoadedEvent(
                    symbol=event_data['metadata']['symbol'],
                    records_count=event_data['metadata']['records_count'],
                    latest_date=event_data['metadata']['latest_date'],
                    latest_price=event_data['metadata']['latest_price'],
                    source=event_source
                )
            elif event_type == EventType.BATCH_DATA_COMPLETED:
                return BatchDataCompletedEvent(
                    symbols_processed=event_data['metadata']['symbols_processed'],
                    successful_symbols=event_data['metadata']['successful_symbols'],
                    total_records=event_data['metadata']['total_records'],
                    symbols=event_data['metadata']['symbols'],
                    source=event_source
                )
            elif event_type == EventType.DATA_THRESHOLD_REACHED:
                return DataThresholdReachedEvent(
                    stock_count=event_data['metadata']['stock_count'],
                    threshold=event_data['metadata']['threshold'],
                    symbols=event_data['metadata']['symbols'],
                    source=event_source
                )
            elif event_type == EventType.STREAMING_STARTED:
                return StreamingStartedEvent(
                    stocks_count=event_data['metadata']['stocks_count'],
                    tick_interval=event_data['metadata']['tick_interval'],
                    symbols=event_data['metadata']['symbols'],
                    source=event_source
                )
            elif event_type == EventType.TICK_GENERATED:
                return TickGeneratedEvent(
                    symbol=event_data['metadata']['symbol'],
                    price=event_data['metadata']['price'],
                    price_change=event_data['metadata']['price_change'],
                    tick_number=event_data['metadata']['tick_number'],
                    stream_type=event_data['metadata'].get('stream_type', 'times_square_simulation'),
                    source=event_source
                )
            elif event_type == EventType.SYSTEM_STATUS_UPDATE:
                return SystemStatusEvent(
                    service_name=event_data['metadata']['service_name'],
                    status=event_data['metadata']['status'],
                    message=event_data['metadata']['message'],
                    metrics=event_data['metadata']['metrics'],
                    source=event_source
                )
            elif event_type == EventType.ERROR_OCCURRED:
                return ErrorEvent(
                    error_type=event_data['metadata']['error_type'],
                    error_message=event_data['metadata']['error_message'],
                    service_name=event_data['metadata']['service_name'],
                    severity=event_data['metadata'].get('severity', 'medium'),
                    source=event_source
                )
            else:
                logger.warning(f"⚠️ Unknown event type: {event_type}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating event from dict: {e}")
            return None
    
    def get_event_history(self, event_type: EventType = None, limit: int = 100) -> List[BaseEvent]:
        """Get event history, optionally filtered by type"""
        if event_type:
            filtered_events = [e for e in self.event_history if e.event_type == event_type]
            return filtered_events[-limit:]
        else:
            return self.event_history[-limit:]
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get statistics about processed events"""
        stats = {
            'total_events': len(self.event_history),
            'events_by_type': {},
            'events_by_source': {},
            'recent_events': len([e for e in self.event_history if (datetime.utcnow() - e.timestamp).seconds < 300])  # Last 5 minutes
        }
        
        # Count by type
        for event in self.event_history:
            event_type = event.event_type.value
            event_source = event.event_source.value
            
            stats['events_by_type'][event_type] = stats['events_by_type'].get(event_type, 0) + 1
            stats['events_by_source'][event_source] = stats['events_by_source'].get(event_source, 0) + 1
        
        return stats

# Global event handler instance
event_handler = EventHandler()

def get_event_handler() -> EventHandler:
    """Get the global event handler instance"""
    return event_handler

# Default event handlers
def default_stock_data_loaded_handler(event: StockDataLoadedEvent):
    """Default handler for stock data loaded events"""
    logger.info(f"📈 Stock data loaded: {event.symbol} - {event.records_count} records - ${event.latest_price:.2f}")

def default_batch_completed_handler(event: BatchDataCompletedEvent):
    """Default handler for batch completed events"""
    logger.info(f"📊 Batch completed: {event.successful_symbols}/{event.symbols_processed} symbols - {event.total_records} records")

def default_threshold_reached_handler(event: DataThresholdReachedEvent):
    """Default handler for threshold reached events"""
    logger.info(f"🎯 Data threshold reached: {event.stock_count} stocks (threshold: {event.threshold})")

def default_streaming_started_handler(event: StreamingStartedEvent):
    """Default handler for streaming started events"""
    logger.info(f"🎬 Streaming started: {event.stocks_count} stocks - {event.tick_interval}s intervals")

def default_tick_generated_handler(event: TickGeneratedEvent):
    """Default handler for tick generated events"""
    logger.debug(f"📈 Tick generated: {event.symbol} - ${event.price:.2f} (change: {event.price_change:+.2f})")

def default_system_status_handler(event: SystemStatusEvent):
    """Default handler for system status events"""
    logger.info(f"📊 System status: {event.service_name} - {event.status} - {event.message}")

def default_error_handler(event: ErrorEvent):
    """Default handler for error events"""
    logger.error(f"❌ Error: {event.service_name} - {event.error_type} - {event.error_message} (severity: {event.severity})")

# Register default handlers
def register_default_handlers():
    """Register default event handlers"""
    handler = get_event_handler()
    
    handler.register_handler(EventType.STOCK_DATA_LOADED, default_stock_data_loaded_handler)
    handler.register_handler(EventType.BATCH_DATA_COMPLETED, default_batch_completed_handler)
    handler.register_handler(EventType.DATA_THRESHOLD_REACHED, default_threshold_reached_handler)
    handler.register_handler(EventType.STREAMING_STARTED, default_streaming_started_handler)
    handler.register_handler(EventType.TICK_GENERATED, default_tick_generated_handler)
    handler.register_handler(EventType.SYSTEM_STATUS_UPDATE, default_system_status_handler)
    handler.register_handler(EventType.ERROR_OCCURRED, default_error_handler)
    
    logger.info("✅ Default event handlers registered")

# Initialize default handlers
register_default_handlers() 