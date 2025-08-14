#!/usr/bin/env python3
"""
Pytest Configuration and Shared Test Fixtures
Provides common test setup, fixtures, and utilities for the Financial Data Streaming System
"""

import pytest
import asyncio
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator, AsyncGenerator
from unittest.mock import Mock, patch, MagicMock
import aiohttp
from fastapi.testclient import TestClient
import mongomock
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import project modules
from ec2_api_server.main import app as api_app
from ec2_stream_receiver.main import app as stream_app
from ec2_driver.stream_simulator import TimesSquareSimulator
from config.config_manager import get_config_manager, SystemConfig
from events.event_handler import EventHandler
from events.sns_publisher import SNSPublisher
from events.sns_listener import SNSListener

# Test configuration
TEST_CONFIG = {
    "environment": "test",
    "debug": True,
    "database": {
        "mongodb_uri": "mongodb://localhost:27017/test_stockdata",
        "mongodb_database": "test_stockdata",
        "connection_timeout": 5000,
        "max_pool_size": 10,
        "retry_writes": True
    },
    "api": {
        "alpha_vantage_api_key": "test-api-key",
        "alpha_vantage_base_url": "https://www.alphavantage.co/query",
        "api_rate_limit": 10,
        "request_timeout": 10,
        "max_retries": 2
    },
    "aws": {
        "region": "us-east-2",
        "sns_topic_arn": "arn:aws:sns:us-east-2:123456789012:test-topic",
        "use_iam_role": False
    },
    "kafka": {
        "bootstrap_servers": "localhost:9092",
        "topic": "test-stock-ticks",
        "group_id": "test-financial-streaming-group",
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True
    },
    "accumulo": {
        "instance_name": "test-stockdata",
        "zookeeper_hosts": "localhost:2181",
        "username": "root",
        "password": "secret",
        "table_name": "test_stock_ticks"
    },
    "service": {
        "api_server_host": "127.0.0.1",
        "api_server_port": 8000,
        "stream_receiver_host": "127.0.0.1",
        "stream_receiver_port": 8002,
        "driver_host": "127.0.0.1",
        "driver_port": 8001,
        "monitoring_host": "127.0.0.1",
        "monitoring_port": 8080
    },
    "logging": {
        "level": "DEBUG",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file_path": "test_logs/app.log",
        "max_file_size": 1024 * 1024,  # 1MB
        "backup_count": 2
    },
    "security": {
        "enable_ssl": False,
        "ssl_cert_path": "",
        "ssl_key_path": "",
        "cors_origins": ["http://localhost:3000"],
        "api_key_required": False,
        "jwt_secret": "test-jwt-secret"
    },
    "monitoring": {
        "health_check_interval": 5,
        "metrics_collection_interval": 10,
        "alert_check_interval": 10,
        "response_time_warning": 1.0,
        "response_time_error": 2.0,
        "error_rate_warning": 0.1,
        "error_rate_error": 0.2
    }
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Provide test configuration."""
    return TEST_CONFIG

@pytest.fixture(scope="session")
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="financial_streaming_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def mock_mongodb():
    """Mock MongoDB for testing."""
    with mongomock.patch(servers=(('localhost', 27017),)):
        yield

@pytest.fixture(scope="function")
def mock_config_manager():
    """Mock configuration manager for testing."""
    with patch('config.config_manager.get_config_manager') as mock:
        # Create a mock config manager
        config_manager = Mock()
        config_manager.get_config.return_value = SystemConfig(
            environment="test",
            debug=True,
            database=Mock(mongodb_uri="mongodb://localhost:27017/test_stockdata"),
            api=Mock(alpha_vantage_api_key="test-api-key"),
            aws=Mock(sns_topic_arn="arn:aws:sns:us-east-2:123456789012:test-topic"),
            kafka=Mock(bootstrap_servers="localhost:9092"),
            service=Mock(
                api_server_port=8000,
                stream_receiver_port=8002,
                driver_port=8001,
                monitoring_port=8080
            ),
            logging=Mock(level="DEBUG"),
            security=Mock(enable_ssl=False, api_key_required=False),
            monitoring=Mock(health_check_interval=5)
        )
        config_manager.get_service_config.return_value = {
            'host': '127.0.0.1',
            'port': 8000,
            'database': {'mongodb_uri': 'mongodb://localhost:27017/test_stockdata'},
            'api': {'alpha_vantage_api_key': 'test-api-key'},
            'aws': {'sns_topic_arn': 'arn:aws:sns:us-east-2:123456789012:test-topic'},
            'logging': {'level': 'DEBUG'},
            'security': {'enable_ssl': False, 'api_key_required': False}
        }
        mock.return_value = config_manager
        yield config_manager

@pytest.fixture(scope="function")
def mock_alpha_vantage():
    """Mock Alpha Vantage API responses."""
    mock_responses = {
        "TIME_SERIES_DAILY": {
            "Meta Data": {
                "1. Information": "Daily Prices (open, high, low, close) and Volumes",
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2024-01-15",
                "4. Output Size": "Compact",
                "5. Time Zone": "US/Eastern"
            },
            "Time Series (Daily)": {
                "2024-01-15": {
                    "1. open": "185.59",
                    "2. high": "188.75",
                    "3. low": "185.00",
                    "4. close": "187.50",
                    "5. volume": "12345678"
                },
                "2024-01-14": {
                    "1. open": "184.00",
                    "2. high": "186.50",
                    "3. low": "183.50",
                    "4. close": "185.59",
                    "5. volume": "11234567"
                }
            }
        },
        "OVERVIEW": {
            "Symbol": "AAPL",
            "AssetType": "Common Stock",
            "Name": "Apple Inc",
            "Description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables and accessories worldwide.",
            "CIK": "320193",
            "Exchange": "NASDAQ",
            "Currency": "USD",
            "Country": "USA",
            "Sector": "Technology",
            "Industry": "Consumer Electronics",
            "Address": "One Apple Park Way, Cupertino, CA, United States, 95014",
            "FiscalYearEnd": "September",
            "LatestQuarter": "2023-12-31",
            "MarketCapitalization": "3000000000000",
            "EBITDA": "120000000000",
            "PERatio": "30.5",
            "PEGRatio": "2.1",
            "BookValue": "4.5",
            "DividendPerShare": "0.92",
            "DividendYield": "0.5",
            "EPS": "6.15",
            "RevenuePerShareTTM": "23.45",
            "ProfitMargin": "25.5",
            "OperatingMarginTTM": "30.2",
            "ReturnOnAssetsTTM": "18.5",
            "ReturnOnEquityTTM": "150.2",
            "RevenueTTM": "394328000000",
            "GrossProfitTTM": "170782000000",
            "DilutedEPSTTM": "6.15",
            "QuarterlyEarningsGrowthYOY": "13.1",
            "QuarterlyRevenueGrowthYOY": "8.1",
            "AnalystTargetPrice": "200.00",
            "TrailingPE": "30.5",
            "ForwardPE": "28.2",
            "PriceToBookRatio": "35.2",
            "PriceToSalesRatioTTM": "7.6",
            "EVToRevenue": "7.8",
            "EVToEBITDA": "25.0",
            "Beta": "1.2",
            "52WeekHigh": "198.23",
            "52WeekLow": "124.17",
            "50DayMovingAverage": "185.50",
            "200DayMovingAverage": "175.20",
            "SharesOutstanding": "15728700480",
            "DividendDate": "2024-02-15",
            "ExDividendDate": "2024-02-08"
        }
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        async def mock_response(*args, **kwargs):
            mock_resp = Mock()
            mock_resp.status = 200
            mock_resp.json = asyncio.coroutine(lambda: mock_responses.get("TIME_SERIES_DAILY", {}))
            return mock_resp
        
        mock_get.return_value = mock_response()
        yield mock_get

@pytest.fixture(scope="function")
def mock_sns():
    """Mock AWS SNS for testing."""
    with patch('boto3.client') as mock_boto3:
        mock_sns_client = Mock()
        mock_sns_client.publish.return_value = {
            'MessageId': 'test-message-id-12345',
            'ResponseMetadata': {
                'RequestId': 'test-request-id',
                'HTTPStatusCode': 200
            }
        }
        mock_boto3.return_value = mock_sns_client
        yield mock_sns_client

@pytest.fixture(scope="function")
def mock_kafka():
    """Mock Kafka for testing."""
    with patch('kafka.KafkaProducer') as mock_producer, \
         patch('kafka.KafkaConsumer') as mock_consumer:
        
        # Mock producer
        mock_producer_instance = Mock()
        mock_producer_instance.send.return_value = Mock()
        mock_producer_instance.flush.return_value = None
        mock_producer.return_value = mock_producer_instance
        
        # Mock consumer
        mock_consumer_instance = Mock()
        mock_consumer_instance.__iter__.return_value = []
        mock_consumer.return_value = mock_consumer_instance
        
        yield {
            'producer': mock_producer_instance,
            'consumer': mock_consumer_instance
        }

@pytest.fixture(scope="function")
def mock_accumulo():
    """Mock Accumulo for testing."""
    with patch('accumulo_client.AccumuloClient') as mock_client:
        mock_instance = Mock()
        mock_instance.get_status.return_value = {
            'connected': True,
            'total_ticks': 1000,
            'last_update': datetime.now().isoformat()
        }
        mock_instance.write_tick.return_value = True
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture(scope="function")
def api_client():
    """Create a test client for the API server."""
    with TestClient(api_app) as client:
        yield client

@pytest.fixture(scope="function")
def stream_client():
    """Create a test client for the stream receiver."""
    with TestClient(stream_app) as client:
        yield client

@pytest.fixture(scope="function")
def mock_event_handler():
    """Mock event handler for testing."""
    with patch('events.event_handler.EventHandler') as mock:
        mock_instance = Mock()
        mock_instance.publish_event.return_value = True
        mock_instance.handle_event.return_value = True
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture(scope="function")
def sample_stock_data():
    """Provide sample stock data for testing."""
    return {
        "symbol": "AAPL",
        "date": "2024-01-15",
        "open": 185.59,
        "high": 188.75,
        "low": 185.00,
        "close": 187.50,
        "volume": 12345678,
        "adjusted_close": 187.50,
        "dividend_amount": 0.0,
        "split_coefficient": 1.0
    }

@pytest.fixture(scope="function")
def sample_tick_data():
    """Provide sample tick data for testing."""
    return {
        "symbol": "AAPL",
        "price": 187.50,
        "volume": 1000,
        "timestamp": datetime.now().isoformat(),
        "price_change": 1.91,
        "stream_type": "times_square_simulation"
    }

@pytest.fixture(scope="function")
def sample_company_data():
    """Provide sample company data for testing."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables and accessories worldwide.",
        "market_cap": "3000000000000",
        "pe_ratio": "30.5"
    }

@pytest.fixture(scope="function")
def mock_times_square_simulator():
    """Mock Times Square Simulator for testing."""
    with patch('ec2_driver.stream_simulator.TimesSquareSimulator') as mock:
        mock_instance = Mock()
        mock_instance.start_streaming.return_value = True
        mock_instance.stop_streaming.return_value = True
        mock_instance.get_status.return_value = {
            'active': True,
            'symbols': ['AAPL', 'GOOGL', 'MSFT'],
            'ticks_sent': 1500,
            'start_time': datetime.now().isoformat()
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture(scope="function")
def mock_monitoring_dashboard():
    """Mock monitoring dashboard for testing."""
    with patch('monitoring.dashboard.MonitoringService') as mock:
        mock_instance = Mock()
        mock_instance.start_monitoring.return_value = True
        mock_instance.stop_monitoring.return_value = True
        mock_instance.get_status.return_value = {
            'active': True,
            'services_monitored': 3,
            'alerts_count': 0,
            'last_check': datetime.now().isoformat()
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture(scope="function")
def test_database():
    """Create a test database connection."""
    # This would be replaced with actual test database setup
    # For now, we'll use a mock
    with patch('pymongo.MongoClient') as mock_client:
        mock_db = Mock()
        mock_collection = Mock()
        mock_collection.insert_one.return_value = Mock(inserted_id="test_id")
        mock_collection.find.return_value = []
        mock_collection.find_one.return_value = None
        mock_collection.update_one.return_value = Mock(modified_count=1)
        mock_collection.delete_one.return_value = Mock(deleted_count=1)
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value.__getitem__.return_value = mock_db
        yield mock_db

@pytest.fixture(scope="function")
def async_client():
    """Create an async HTTP client for testing."""
    async def _async_client():
        async with aiohttp.ClientSession() as session:
            yield session
    
    return _async_client

@pytest.fixture(scope="function")
def performance_metrics():
    """Provide performance metrics for testing."""
    return {
        "response_time": 0.15,
        "throughput": 1000,
        "error_rate": 0.01,
        "cpu_usage": 45.5,
        "memory_usage": 67.2,
        "disk_usage": 23.1
    }

# Test utilities
class TestUtils:
    """Utility functions for testing."""
    
    @staticmethod
    def create_test_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test event."""
        return {
            "event_id": f"test-event-{datetime.now().timestamp()}",
            "event_type": event_type,
            "event_source": "test",
            "timestamp": datetime.now().isoformat(),
            "metadata": data
        }
    
    @staticmethod
    def assert_response_structure(response, expected_fields: list):
        """Assert that response has expected structure."""
        assert response.status_code == 200
        data = response.json()
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
    
    @staticmethod
    def assert_error_response(response, expected_status: int = 400):
        """Assert that response is an error."""
        assert response.status_code == expected_status
        data = response.json()
        assert "detail" in data or "error" in data
    
    @staticmethod
    def create_mock_stock_data(symbol: str, days: int = 30) -> list:
        """Create mock stock data for testing."""
        data = []
        base_price = 100.0
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            price_change = (i % 10 - 5) * 0.5  # Random price movement
            data.append({
                "symbol": symbol,
                "date": date.strftime("%Y-%m-%d"),
                "open": base_price + price_change,
                "high": base_price + price_change + 2.0,
                "low": base_price + price_change - 2.0,
                "close": base_price + price_change + 1.0,
                "volume": 1000000 + (i * 10000),
                "adjusted_close": base_price + price_change + 1.0,
                "dividend_amount": 0.0,
                "split_coefficient": 1.0
            })
        return data

# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")

def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add default markers based on test file location
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        elif "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance) 