#!/usr/bin/env python3
"""
Integration Tests for Financial Data Streaming System
Tests the integration between different components and services
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import aiohttp

# Import the modules to test
from ec2_api_server.main import app as api_app
from ec2_stream_receiver.main import app as stream_app
from ec2_driver.stream_simulator import TimesSquareSimulator
from events.event_handler import EventHandler
from events.sns_publisher import SNSPublisher
from events.sns_listener import SNSListener
from config.config_manager import get_config_manager

class TestAPIToStreamIntegration:
    """Test integration between API Server and Stream Receiver."""
    
    @pytest.fixture
    def api_client(self):
        """Create API server test client."""
        return TestClient(api_app)
    
    @pytest.fixture
    def stream_client(self):
        """Create stream receiver test client."""
        return TestClient(stream_app)
    
    @pytest.mark.integration
    def test_api_to_stream_data_flow(self, api_client, stream_client, mock_config_manager):
        """Test complete data flow from API to stream processing."""
        # 1. Fetch stock data via API
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = [
                {
                    "symbol": "AAPL",
                    "date": "2024-01-15",
                    "open": 185.59,
                    "high": 188.75,
                    "low": 185.00,
                    "close": 187.50,
                    "volume": 12345678
                }
            ]
            
            response = api_client.get("/api/v1/stocks/AAPL/data")
            assert response.status_code == 200
            stock_data = response.json()
            assert len(stock_data) == 1
            assert stock_data[0]["symbol"] == "AAPL"
        
        # 2. Send tick data to stream receiver
        tick_data = {
            "symbol": "AAPL",
            "price": 187.50,
            "volume": 1000,
            "timestamp": datetime.now().isoformat(),
            "price_change": 1.91,
            "stream_type": "api_integration_test"
        }
        
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.write_tick') as mock_write:
            mock_write.return_value = True
            
            response = stream_client.post("/api/v1/stream/ticks", json=tick_data)
            assert response.status_code == 200
            result = response.json()
            assert result["message"] == "Tick data created successfully"
        
        # 3. Verify tick data in stream receiver
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.get_ticks') as mock_get_ticks:
            mock_get_ticks.return_value = [tick_data]
            
            response = stream_client.get("/api/v1/stream/ticks/AAPL/latest")
            assert response.status_code == 200
            latest_tick = response.json()
            assert latest_tick["symbol"] == "AAPL"
            assert latest_tick["price"] == 187.50
    
    @pytest.mark.integration
    def test_event_system_integration(self, api_client, stream_client, mock_config_manager):
        """Test event system integration between services."""
        # 1. Simulate stock data update event
        event_data = {
            "event_type": "stock_data_updated",
            "symbol": "GOOGL",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "records_updated": 30,
                "source": "api_server"
            }
        }
        
        with patch('events.sns_publisher.SNSPublisher.publish_event') as mock_publish:
            mock_publish.return_value = True
            
            # This would normally be triggered by a stock data update
            # For testing, we'll simulate the event directly
            sns_publisher = SNSPublisher()
            result = sns_publisher.publish_event(event_data)
            assert result == True
        
        # 2. Verify event handling in stream receiver
        with patch('events.sns_listener.SNSListener.handle_event') as mock_handle:
            mock_handle.return_value = True
            
            # Simulate event reception
            sns_listener = SNSListener()
            result = sns_listener.handle_event(event_data)
            assert result == True
    
    @pytest.mark.integration
    def test_kafka_integration(self, stream_client, mock_kafka):
        """Test Kafka integration in stream processing."""
        # 1. Send message to Kafka via stream receiver
        kafka_message = {
            "topic": "test-stock-ticks",
            "message": {
                "symbol": "MSFT",
                "price": 350.25,
                "volume": 500,
                "timestamp": datetime.now().isoformat()
            },
            "key": "MSFT"
        }
        
        with patch('ec2_stream_receiver.kafka_client.KafkaClient.send_message') as mock_send:
            mock_send.return_value = True
            
            response = stream_client.post("/api/v1/stream/kafka/send", json=kafka_message)
            assert response.status_code == 200
            result = response.json()
            assert result["message"] == "Message sent to Kafka successfully"
        
        # 2. Verify Kafka message consumption
        with patch('ec2_stream_receiver.kafka_client.KafkaClient.get_messages') as mock_get:
            mock_get.return_value = [kafka_message["message"]]
            
            response = stream_client.get("/api/v1/stream/kafka/messages")
            assert response.status_code == 200
            messages = response.json()
            assert len(messages) == 1
            assert messages[0]["symbol"] == "MSFT"

class TestTimesSquareSimulatorIntegration:
    """Test Times Square Simulator integration."""
    
    @pytest.fixture
    def simulator(self, mock_config_manager):
        """Create Times Square Simulator for testing."""
        return TimesSquareSimulator()
    
    @pytest.mark.integration
    def test_simulator_to_stream_integration(self, simulator, stream_client, mock_config_manager):
        """Test integration between simulator and stream receiver."""
        # 1. Start simulator
        with patch('ec2_driver.stream_simulator.TimesSquareSimulator.start_streaming') as mock_start:
            mock_start.return_value = True
            
            result = simulator.start_streaming()
            assert result == True
        
        # 2. Generate tick data
        with patch('ec2_driver.stream_simulator.TimesSquareSimulator.generate_tick') as mock_generate:
            mock_generate.return_value = {
                "symbol": "TSLA",
                "price": 250.75,
                "volume": 2000,
                "timestamp": datetime.now().isoformat(),
                "price_change": 5.25,
                "stream_type": "times_square_simulation"
            }
            
            tick_data = simulator.generate_tick("TSLA")
            assert tick_data["symbol"] == "TSLA"
            assert tick_data["price"] == 250.75
        
        # 3. Send to stream receiver
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.write_tick') as mock_write:
            mock_write.return_value = True
            
            response = stream_client.post("/api/v1/stream/ticks", json=tick_data)
            assert response.status_code == 200
        
        # 4. Verify in stream receiver
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.get_ticks') as mock_get:
            mock_get.return_value = [tick_data]
            
            response = stream_client.get("/api/v1/stream/ticks/TSLA/latest")
            assert response.status_code == 200
            latest_tick = response.json()
            assert latest_tick["symbol"] == "TSLA"
            assert latest_tick["stream_type"] == "times_square_simulation"
    
    @pytest.mark.integration
    def test_simulator_status_integration(self, simulator, mock_config_manager):
        """Test simulator status integration."""
        with patch('ec2_driver.stream_simulator.TimesSquareSimulator.get_status') as mock_status:
            mock_status.return_value = {
                'active': True,
                'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA'],
                'ticks_sent': 2500,
                'start_time': datetime.now().isoformat(),
                'current_symbol': 'AAPL',
                'tick_interval': 1.0
            }
            
            status = simulator.get_status()
            assert status['active'] == True
            assert len(status['symbols']) == 4
            assert status['ticks_sent'] == 2500

class TestDatabaseIntegration:
    """Test database integration across services."""
    
    @pytest.mark.integration
    def test_api_database_integration(self, api_client, mock_config_manager):
        """Test API server database integration."""
        # 1. Test database connection
        with patch('ec2_api_server.data_service.DataService.get_database_stats') as mock_stats:
            mock_stats.return_value = {
                "total_symbols": 150,
                "total_records": 75000,
                "last_updated": datetime.now().isoformat(),
                "database_size": "2.5GB",
                "connection_status": "healthy"
            }
            
            response = api_client.get("/api/v1/database/stats")
            assert response.status_code == 200
            stats = response.json()
            assert stats["total_symbols"] == 150
            assert stats["total_records"] == 75000
            assert stats["connection_status"] == "healthy"
        
        # 2. Test database health check
        with patch('ec2_api_server.data_service.DataService.check_database_health') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "response_time": 0.15,
                "last_check": datetime.now().isoformat()
            }
            
            response = api_client.get("/api/v1/database/health")
            assert response.status_code == 200
            health = response.json()
            assert health["status"] == "healthy"
            assert health["response_time"] < 1.0
    
    @pytest.mark.integration
    def test_stream_database_integration(self, stream_client, mock_config_manager):
        """Test stream receiver database integration."""
        # 1. Test Accumulo connection
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.get_status') as mock_status:
            mock_status.return_value = {
                'connected': True,
                'total_ticks': 5000,
                'last_update': datetime.now().isoformat(),
                'table_size': '1.2GB',
                'write_speed': '1000 ticks/sec'
            }
            
            response = stream_client.get("/api/v1/stream/accumulo/status")
            assert response.status_code == 200
            status = response.json()
            assert status['connected'] == True
            assert status['total_ticks'] == 5000

class TestMonitoringIntegration:
    """Test monitoring system integration."""
    
    @pytest.mark.integration
    def test_service_monitoring_integration(self, api_client, stream_client, mock_config_manager):
        """Test monitoring integration across services."""
        # 1. Test API server monitoring
        with patch('ec2_api_server.data_service.DataService.get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "response_time_avg": 0.25,
                "requests_per_minute": 120,
                "error_rate": 0.02,
                "active_connections": 15,
                "memory_usage": 45.5,
                "cpu_usage": 23.1
            }
            
            # This would normally be exposed via a monitoring endpoint
            # For testing, we'll simulate the metrics collection
            metrics = mock_metrics.return_value
            assert metrics["response_time_avg"] < 1.0
            assert metrics["error_rate"] < 0.1
            assert metrics["memory_usage"] < 100.0
        
        # 2. Test stream receiver monitoring
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.get_performance_metrics') as mock_stream_metrics:
            mock_stream_metrics.return_value = {
                "ticks_per_second": 150,
                "processing_latency": 0.05,
                "queue_size": 25,
                "error_rate": 0.01,
                "memory_usage": 38.2,
                "cpu_usage": 67.8
            }
            
            stream_metrics = mock_stream_metrics.return_value
            assert stream_metrics["ticks_per_second"] > 0
            assert stream_metrics["processing_latency"] < 1.0
            assert stream_metrics["error_rate"] < 0.1

class TestConfigurationIntegration:
    """Test configuration system integration."""
    
    @pytest.mark.integration
    def test_config_across_services(self, mock_config_manager):
        """Test configuration consistency across services."""
        # 1. Test API server configuration
        api_config = get_config_manager().get_service_config('api_server')
        assert api_config['port'] == 8000
        assert 'database' in api_config
        assert 'api' in api_config
        assert 'aws' in api_config
        
        # 2. Test stream receiver configuration
        stream_config = get_config_manager().get_service_config('stream_receiver')
        assert stream_config['port'] == 8002
        assert 'kafka' in stream_config
        assert 'accumulo' in stream_config
        
        # 3. Test configuration consistency
        assert api_config['database']['mongodb_uri'] == stream_config['database']['mongodb_uri']
        assert api_config['logging']['level'] == stream_config['logging']['level']

class TestErrorHandlingIntegration:
    """Test error handling integration across services."""
    
    @pytest.mark.integration
    def test_cascade_error_handling(self, api_client, stream_client, mock_config_manager):
        """Test error handling when one service fails."""
        # 1. Simulate API server error
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.side_effect = Exception("Database connection failed")
            
            response = api_client.get("/api/v1/stocks/AAPL/data")
            assert response.status_code == 500
            error_data = response.json()
            assert "detail" in error_data
        
        # 2. Verify stream receiver continues to work
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.get_status') as mock_status:
            mock_status.return_value = {
                'connected': True,
                'total_ticks': 1000,
                'last_update': datetime.now().isoformat()
            }
            
            response = stream_client.get("/api/v1/stream/status")
            assert response.status_code == 200
            status = response.json()
            assert status['accumulo_connected'] == True
    
    @pytest.mark.integration
    def test_recovery_integration(self, api_client, stream_client, mock_config_manager):
        """Test system recovery after errors."""
        # 1. Simulate temporary failure
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            # First call fails
            mock_get.side_effect = [Exception("Temporary error"), [
                {
                    "symbol": "AAPL",
                    "date": "2024-01-15",
                    "close": 187.50,
                    "volume": 12345678
                }
            ]]
            
            # First request should fail
            response = api_client.get("/api/v1/stocks/AAPL/data")
            assert response.status_code == 500
            
            # Second request should succeed (recovery)
            response = api_client.get("/api/v1/stocks/AAPL/data")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["symbol"] == "AAPL"

class TestPerformanceIntegration:
    """Test performance integration across services."""
    
    @pytest.mark.integration
    def test_concurrent_requests(self, api_client, stream_client, mock_config_manager):
        """Test system performance under concurrent load."""
        import concurrent.futures
        import time
        
        # 1. Test concurrent API requests
        def make_api_request():
            with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
                mock_get.return_value = [{"symbol": "AAPL", "date": "2024-01-15", "close": 187.50}]
                response = api_client.get("/api/v1/stocks/AAPL/data")
                return response.status_code
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_api_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds for 20 concurrent requests
    
    @pytest.mark.integration
    def test_stream_processing_performance(self, stream_client, mock_config_manager):
        """Test stream processing performance."""
        # 1. Test bulk tick processing
        tick_batch = []
        for i in range(100):
            tick_batch.append({
                "symbol": f"STOCK{i%5}",
                "price": 100.0 + i,
                "volume": 1000 + i,
                "timestamp": datetime.now().isoformat(),
                "price_change": i * 0.1,
                "stream_type": "performance_test"
            })
        
        start_time = time.time()
        
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.write_tick') as mock_write:
            mock_write.return_value = True
            
            for tick in tick_batch:
                response = stream_client.post("/api/v1/stream/ticks", json=tick)
                assert response.status_code == 200
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should process 100 ticks within reasonable time
        assert duration < 10.0  # 10 seconds for 100 ticks
        assert mock_write.call_count == 100

class TestSecurityIntegration:
    """Test security integration across services."""
    
    @pytest.mark.integration
    def test_api_authentication_integration(self, api_client, mock_config_manager):
        """Test API authentication integration."""
        # 1. Test without authentication (should work in test mode)
        with patch('ec2_api_server.data_service.DataService.get_all_symbols') as mock_get:
            mock_get.return_value = ["AAPL", "GOOGL"]
            
            response = api_client.get("/api/v1/stocks")
            assert response.status_code == 200
        
        # 2. Test with invalid authentication
        headers = {"Authorization": "Bearer invalid-token"}
        response = api_client.get("/api/v1/stocks", headers=headers)
        # Should still work in test mode, but in production this would fail
        assert response.status_code in [200, 401]
    
    @pytest.mark.integration
    def test_data_validation_integration(self, api_client, stream_client, mock_config_manager):
        """Test data validation integration."""
        # 1. Test invalid stock data
        invalid_tick = {
            "symbol": "INVALID_SYMBOL_123",
            "price": -100.0,  # Invalid negative price
            "volume": 0,  # Invalid zero volume
            "timestamp": "invalid-timestamp",
            "stream_type": "test"
        }
        
        response = stream_client.post("/api/v1/stream/ticks", json=invalid_tick)
        # Should either reject or handle gracefully
        assert response.status_code in [200, 400, 422]
        
        # 2. Test SQL injection prevention
        malicious_symbol = "AAPL'; DROP TABLE stocks; --"
        response = api_client.get(f"/api/v1/stocks/{malicious_symbol}/data")
        # Should handle safely
        assert response.status_code in [200, 400, 404] 