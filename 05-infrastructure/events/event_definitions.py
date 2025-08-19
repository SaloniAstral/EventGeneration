#!/usr/bin/env python3
"""
Event Definitions for Financial Data Streaming System
Defines all events that coordinate between EC2 instances
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json

class EventType(Enum):
    """Types of events in the system"""
    
    # Data Loading Events
    STOCK_DATA_LOADED = "stock_data_loaded"
    COMPANY_INFO_UPDATED = "company_info_updated"
    BATCH_DATA_COMPLETED = "batch_data_completed"
    
    # Streaming Events
    STREAMING_STARTED = "streaming_started"
    STREAMING_STOPPED = "streaming_stopped"
    TICK_GENERATED = "tick_generated"
    
    # System Events
    SYSTEM_STATUS_UPDATE = "system_status_update"
    ERROR_OCCURRED = "error_occurred"
    HEALTH_CHECK = "health_check"
    
    # Threshold Events
    DATA_THRESHOLD_REACHED = "data_threshold_reached"
    STREAMING_READY = "streaming_ready"

class EventSource(Enum):
    """Sources of events"""
    API_SERVER = "ec2_api_server"
    DRIVER = "ec2_driver"
    STREAM_RECEIVER = "ec2_stream_receiver"
    SYSTEM = "system"

@dataclass
class BaseEvent:
    """Base event class"""
    event_type: EventType
    event_source: EventSource
    timestamp: datetime
    event_id: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['event_source'] = self.event_source.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

@dataclass
class StockDataLoadedEvent(BaseEvent):
    """Event when stock data is loaded"""
    symbol: str
    records_count: int
    latest_date: str
    latest_price: float
    
    def __init__(self, symbol: str, records_count: int, latest_date: str, latest_price: float, source: EventSource = EventSource.API_SERVER):
        super().__init__(
            event_type=EventType.STOCK_DATA_LOADED,
            event_source=source,
            timestamp=datetime.utcnow(),
            event_id=f"stock_loaded_{symbol}_{datetime.utcnow().timestamp()}",
            metadata={
                "symbol": symbol,
                "records_count": records_count,
                "latest_date": latest_date,
                "latest_price": latest_price
            }
        )
        self.symbol = symbol
        self.records_count = records_count
        self.latest_date = latest_date
        self.latest_price = latest_price

@dataclass
class BatchDataCompletedEvent(BaseEvent):
    """Event when batch data loading is completed"""
    symbols_processed: int
    successful_symbols: int
    total_records: int
    symbols: list
    
    def __init__(self, symbols_processed: int, successful_symbols: int, total_records: int, symbols: list, source: EventSource = EventSource.API_SERVER):
        super().__init__(
            event_type=EventType.BATCH_DATA_COMPLETED,
            event_source=source,
            timestamp=datetime.utcnow(),
            event_id=f"batch_completed_{datetime.utcnow().timestamp()}",
            metadata={
                "symbols_processed": symbols_processed,
                "successful_symbols": successful_symbols,
                "total_records": total_records,
                "symbols": symbols
            }
        )
        self.symbols_processed = symbols_processed
        self.successful_symbols = successful_symbols
        self.total_records = total_records
        self.symbols = symbols

@dataclass
class DataThresholdReachedEvent(BaseEvent):
    """Event when data threshold is reached for streaming"""
    stock_count: int
    threshold: int
    symbols: list
    
    def __init__(self, stock_count: int, threshold: int, symbols: list, source: EventSource = EventSource.DRIVER):
        super().__init__(
            event_type=EventType.DATA_THRESHOLD_REACHED,
            event_source=source,
            timestamp=datetime.utcnow(),
            event_id=f"threshold_reached_{datetime.utcnow().timestamp()}",
            metadata={
                "stock_count": stock_count,
                "threshold": threshold,
                "symbols": symbols
            }
        )
        self.stock_count = stock_count
        self.threshold = threshold
        self.symbols = symbols

@dataclass
class StreamingStartedEvent(BaseEvent):
    """Event when Times Square streaming starts"""
    stocks_count: int
    tick_interval: float
    symbols: list
    
    def __init__(self, stocks_count: int, tick_interval: float, symbols: list, source: EventSource = EventSource.DRIVER):
        super().__init__(
            event_type=EventType.STREAMING_STARTED,
            event_source=source,
            timestamp=datetime.utcnow(),
            event_id=f"streaming_started_{datetime.utcnow().timestamp()}",
            metadata={
                "stocks_count": stocks_count,
                "tick_interval": tick_interval,
                "symbols": symbols
            }
        )
        self.stocks_count = stocks_count
        self.tick_interval = tick_interval
        self.symbols = symbols

@dataclass
class TickGeneratedEvent(BaseEvent):
    """Event when a tick is generated"""
    symbol: str
    price: float
    price_change: float
    tick_number: int
    stream_type: str
    
    def __init__(self, symbol: str, price: float, price_change: float, tick_number: int, stream_type: str = "times_square_simulation", source: EventSource = EventSource.DRIVER):
        super().__init__(
            event_type=EventType.TICK_GENERATED,
            event_source=source,
            timestamp=datetime.utcnow(),
            event_id=f"tick_{symbol}_{tick_number}_{datetime.utcnow().timestamp()}",
            metadata={
                "symbol": symbol,
                "price": price,
                "price_change": price_change,
                "tick_number": tick_number,
                "stream_type": stream_type
            }
        )
        self.symbol = symbol
        self.price = price
        self.price_change = price_change
        self.tick_number = tick_number
        self.stream_type = stream_type

@dataclass
class SystemStatusEvent(BaseEvent):
    """Event for system status updates"""
    service_name: str
    status: str
    message: str
    metrics: Dict[str, Any]
    
    def __init__(self, service_name: str, status: str, message: str, metrics: Dict[str, Any], source: EventSource = EventSource.SYSTEM):
        super().__init__(
            event_type=EventType.SYSTEM_STATUS_UPDATE,
            event_source=source,
            timestamp=datetime.utcnow(),
            event_id=f"status_{service_name}_{datetime.utcnow().timestamp()}",
            metadata={
                "service_name": service_name,
                "status": status,
                "message": message,
                "metrics": metrics
            }
        )
        self.service_name = service_name
        self.status = status
        self.message = message
        self.metrics = metrics

@dataclass
class ErrorEvent(BaseEvent):
    """Event for error reporting"""
    error_type: str
    error_message: str
    service_name: str
    severity: str  # "low", "medium", "high", "critical"
    
    def __init__(self, error_type: str, error_message: str, service_name: str, severity: str = "medium", source: EventSource = EventSource.SYSTEM):
        super().__init__(
            event_type=EventType.ERROR_OCCURRED,
            event_source=source,
            timestamp=datetime.utcnow(),
            event_id=f"error_{error_type}_{datetime.utcnow().timestamp()}",
            metadata={
                "error_type": error_type,
                "error_message": error_message,
                "service_name": service_name,
                "severity": severity
            }
        )
        self.error_type = error_type
        self.error_message = error_message
        self.service_name = service_name
        self.severity = severity

# Event factory functions
def create_stock_data_loaded_event(symbol: str, records_count: int, latest_date: str, latest_price: float) -> StockDataLoadedEvent:
    """Create a stock data loaded event"""
    return StockDataLoadedEvent(symbol, records_count, latest_date, latest_price)

def create_batch_completed_event(symbols_processed: int, successful_symbols: int, total_records: int, symbols: list) -> BatchDataCompletedEvent:
    """Create a batch completed event"""
    return BatchDataCompletedEvent(symbols_processed, successful_symbols, total_records, symbols)

def create_threshold_reached_event(stock_count: int, threshold: int, symbols: list) -> DataThresholdReachedEvent:
    """Create a threshold reached event"""
    return DataThresholdReachedEvent(stock_count, threshold, symbols)

def create_streaming_started_event(stocks_count: int, tick_interval: float, symbols: list) -> StreamingStartedEvent:
    """Create a streaming started event"""
    return StreamingStartedEvent(stocks_count, tick_interval, symbols)

def create_tick_event(symbol: str, price: float, price_change: float, tick_number: int) -> TickGeneratedEvent:
    """Create a tick generated event"""
    return TickGeneratedEvent(symbol, price, price_change, tick_number)

def create_system_status_event(service_name: str, status: str, message: str, metrics: Dict[str, Any]) -> SystemStatusEvent:
    """Create a system status event"""
    return SystemStatusEvent(service_name, status, message, metrics)

def create_error_event(error_type: str, error_message: str, service_name: str, severity: str = "medium") -> ErrorEvent:
    """Create an error event"""
    return ErrorEvent(error_type, error_message, service_name, severity) 