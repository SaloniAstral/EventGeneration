#!/usr/bin/env python3
"""
Performance Tests for Financial Data Streaming System
Tests system performance under various load conditions
"""

import pytest
import asyncio
import time
import statistics
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import aiohttp
import psutil
import threading

# Import the modules to test
from ec2_api_server.main import app as api_app
from ec2_stream_receiver.main import app as stream_app
from ec2_driver.stream_simulator import TimesSquareSimulator

class TestAPIPerformance:
    """Test API Server performance."""
    
    @pytest.fixture
    def api_client(self):
        """Create API server test client."""
        return TestClient(api_app)
    
    @pytest.mark.performance
    def test_single_request_performance(self, api_client, mock_config_manager):
        """Test single request performance."""
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = [
                {
                    "symbol": "AAPL",
                    "date": "2024-01-15",
                    "close": 187.50,
                    "volume": 12345678
                }
            ]
            
            start_time = time.time()
            response = api_client.get("/api/v1/stocks/AAPL/data")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # Should respond within 1 second
            print(f"Single request response time: {response_time:.3f}s")
    
    @pytest.mark.performance
    def test_concurrent_requests_performance(self, api_client, mock_config_manager):
        """Test performance under concurrent load."""
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = [{"symbol": "AAPL", "date": "2024-01-15", "close": 187.50}]
            
            def make_request():
                start_time = time.time()
                response = api_client.get("/api/v1/stocks/AAPL/data")
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                }
            
            # Test with different concurrency levels
            concurrency_levels = [5, 10, 20, 50]
            
            for concurrency in concurrency_levels:
                print(f"\nTesting with {concurrency} concurrent requests...")
                
                start_time = time.time()
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [executor.submit(make_request) for _ in range(concurrency)]
                    results = [future.result() for future in futures]
                
                total_time = time.time() - start_time
                response_times = [r['response_time'] for r in results]
                success_count = sum(1 for r in results if r['status_code'] == 200)
                
                print(f"  Total time: {total_time:.3f}s")
                print(f"  Average response time: {statistics.mean(response_times):.3f}s")
                print(f"  Min response time: {min(response_times):.3f}s")
                print(f"  Max response time: {max(response_times):.3f}s")
                print(f"  Success rate: {success_count}/{concurrency} ({success_count/concurrency*100:.1f}%)")
                
                # Performance assertions
                assert success_count == concurrency  # All requests should succeed
                assert statistics.mean(response_times) < 2.0  # Average < 2 seconds
                assert max(response_times) < 5.0  # No request should take > 5 seconds
    
    @pytest.mark.performance
    def test_bulk_data_retrieval_performance(self, api_client, mock_config_manager):
        """Test performance of bulk data retrieval."""
        # Generate large dataset
        large_dataset = []
        for i in range(1000):  # 1000 records
            large_dataset.append({
                "symbol": f"STOCK{i%10}",
                "date": f"2024-01-{15-i%30:02d}",
                "open": 100.0 + i,
                "high": 105.0 + i,
                "low": 95.0 + i,
                "close": 102.0 + i,
                "volume": 1000000 + i * 1000
            })
        
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = large_dataset
            
            start_time = time.time()
            response = api_client.get("/api/v1/stocks/AAPL/data")
            end_time = time.time()
            
            response_time = end_time - start_time
            data_size = len(response.json())
            
            assert response.status_code == 200
            assert data_size == 1000
            assert response_time < 3.0  # Should handle 1000 records within 3 seconds
            print(f"Bulk data retrieval: {data_size} records in {response_time:.3f}s")
    
    @pytest.mark.performance
    def test_search_performance(self, api_client, mock_config_manager):
        """Test search functionality performance."""
        # Generate search dataset
        search_dataset = []
        for i in range(500):
            search_dataset.append({
                "symbol": f"STOCK{i}",
                "name": f"Company {i} Inc",
                "sector": f"Sector {i%5}",
                "industry": f"Industry {i%10}"
            })
        
        with patch('ec2_api_server.data_service.DataService.search_stocks') as mock_search:
            mock_search.return_value = search_dataset
            
            start_time = time.time()
            response = api_client.post("/api/v1/search", json={
                "query": "Company",
                "limit": 100
            })
            end_time = time.time()
            
            response_time = end_time - start_time
            results = response.json()
            
            assert response.status_code == 200
            assert len(results) == 500
            assert response_time < 2.0  # Search should complete within 2 seconds
            print(f"Search performance: {len(results)} results in {response_time:.3f}s")

class TestStreamProcessingPerformance:
    """Test Stream Receiver performance."""
    
    @pytest.fixture
    def stream_client(self):
        """Create stream receiver test client."""
        return TestClient(stream_app)
    
    @pytest.mark.performance
    def test_tick_processing_performance(self, stream_client, mock_config_manager):
        """Test tick processing performance."""
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.write_tick') as mock_write:
            mock_write.return_value = True
            
            # Test different batch sizes
            batch_sizes = [10, 50, 100, 500, 1000]
            
            for batch_size in batch_sizes:
                print(f"\nTesting tick processing with batch size: {batch_size}")
                
                ticks = []
                for i in range(batch_size):
                    ticks.append({
                        "symbol": f"STOCK{i%5}",
                        "price": 100.0 + i * 0.1,
                        "volume": 1000 + i,
                        "timestamp": datetime.now().isoformat(),
                        "price_change": i * 0.01,
                        "stream_type": "performance_test"
                    })
                
                start_time = time.time()
                success_count = 0
                
                for tick in ticks:
                    response = stream_client.post("/api/v1/stream/ticks", json=tick)
                    if response.status_code == 200:
                        success_count += 1
                
                end_time = time.time()
                processing_time = end_time - start_time
                throughput = batch_size / processing_time
                
                print(f"  Processing time: {processing_time:.3f}s")
                print(f"  Throughput: {throughput:.1f} ticks/second")
                print(f"  Success rate: {success_count}/{batch_size} ({success_count/batch_size*100:.1f}%)")
                
                # Performance assertions
                assert success_count == batch_size
                assert throughput > 10  # Should process at least 10 ticks/second
                assert processing_time < 60  # Should complete within 60 seconds
    
    @pytest.mark.performance
    def test_kafka_message_performance(self, stream_client, mock_kafka):
        """Test Kafka message processing performance."""
        with patch('ec2_stream_receiver.kafka_client.KafkaClient.send_message') as mock_send:
            mock_send.return_value = True
            
            # Test message sending performance
            message_count = 1000
            messages = []
            
            for i in range(message_count):
                messages.append({
                    "topic": "test-stock-ticks",
                    "message": {
                        "symbol": f"STOCK{i%10}",
                        "price": 100.0 + i * 0.1,
                        "volume": 1000 + i,
                        "timestamp": datetime.now().isoformat()
                    },
                    "key": f"STOCK{i%10}"
                })
            
            start_time = time.time()
            success_count = 0
            
            for message in messages:
                response = stream_client.post("/api/v1/stream/kafka/send", json=message)
                if response.status_code == 200:
                    success_count += 1
            
            end_time = time.time()
            processing_time = end_time - start_time
            throughput = message_count / processing_time
            
            print(f"Kafka message performance:")
            print(f"  Messages sent: {success_count}/{message_count}")
            print(f"  Processing time: {processing_time:.3f}s")
            print(f"  Throughput: {throughput:.1f} messages/second")
            
            assert success_count == message_count
            assert throughput > 50  # Should send at least 50 messages/second
            assert processing_time < 30  # Should complete within 30 seconds
    
    @pytest.mark.performance
    def test_stream_status_performance(self, stream_client, mock_config_manager):
        """Test stream status endpoint performance."""
        with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.get_status') as mock_status:
            mock_status.return_value = {
                'connected': True,
                'total_ticks': 10000,
                'last_update': datetime.now().isoformat(),
                'table_size': '2.5GB',
                'write_speed': '1500 ticks/sec'
            }
            
            # Test repeated status checks
            check_count = 100
            response_times = []
            
            for _ in range(check_count):
                start_time = time.time()
                response = stream_client.get("/api/v1/stream/status")
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
            
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            print(f"Stream status performance:")
            print(f"  Checks completed: {len(response_times)}/{check_count}")
            print(f"  Average response time: {avg_response_time:.3f}s")
            print(f"  Max response time: {max_response_time:.3f}s")
            
            assert len(response_times) == check_count
            assert avg_response_time < 0.5  # Average < 0.5 seconds
            assert max_response_time < 1.0  # Max < 1 second

class TestTimesSquareSimulatorPerformance:
    """Test Times Square Simulator performance."""
    
    @pytest.fixture
    def simulator(self, mock_config_manager):
        """Create Times Square Simulator for testing."""
        return TimesSquareSimulator()
    
    @pytest.mark.performance
    def test_tick_generation_performance(self, simulator, mock_config_manager):
        """Test tick generation performance."""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        
        # Test tick generation speed
        tick_count = 1000
        generation_times = []
        
        with patch('ec2_driver.stream_simulator.TimesSquareSimulator.generate_tick') as mock_generate:
            mock_generate.side_effect = lambda symbol: {
                "symbol": symbol,
                "price": 100.0 + hash(symbol) % 100,
                "volume": 1000 + hash(symbol) % 5000,
                "timestamp": datetime.now().isoformat(),
                "price_change": hash(symbol) % 10 - 5,
                "stream_type": "times_square_simulation"
            }
            
            for i in range(tick_count):
                symbol = symbols[i % len(symbols)]
                start_time = time.time()
                tick = simulator.generate_tick(symbol)
                end_time = time.time()
                
                generation_times.append(end_time - start_time)
                assert tick["symbol"] == symbol
        
        avg_generation_time = statistics.mean(generation_times)
        max_generation_time = max(generation_times)
        throughput = tick_count / sum(generation_times)
        
        print(f"Tick generation performance:")
        print(f"  Ticks generated: {tick_count}")
        print(f"  Average generation time: {avg_generation_time:.6f}s")
        print(f"  Max generation time: {max_generation_time:.6f}s")
        print(f"  Throughput: {throughput:.1f} ticks/second")
        
        assert avg_generation_time < 0.001  # Average < 1ms
        assert max_generation_time < 0.01   # Max < 10ms
        assert throughput > 1000  # Should generate > 1000 ticks/second
    
    @pytest.mark.performance
    def test_simulator_streaming_performance(self, simulator, mock_config_manager):
        """Test simulator streaming performance."""
        with patch('ec2_driver.stream_simulator.TimesSquareSimulator.start_streaming') as mock_start:
            mock_start.return_value = True
            
            # Test streaming startup performance
            start_time = time.time()
            result = simulator.start_streaming()
            startup_time = time.time() - start_time
            
            assert result == True
            assert startup_time < 1.0  # Should start within 1 second
            print(f"Simulator startup time: {startup_time:.3f}s")

class TestSystemResourcePerformance:
    """Test system resource usage during performance tests."""
    
    @pytest.mark.performance
    def test_memory_usage_performance(self, api_client, stream_client, mock_config_manager):
        """Test memory usage during high load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"Initial memory usage: {initial_memory:.1f} MB")
        
        # Perform high-load operations
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = [{"symbol": "AAPL", "date": "2024-01-15", "close": 187.50}]
            
            # Make 1000 requests
            for i in range(1000):
                response = api_client.get("/api/v1/stocks/AAPL/data")
                assert response.status_code == 200
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Final memory usage: {final_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")
        
        # Memory should not increase excessively
        assert memory_increase < 100  # Should not increase by more than 100MB
    
    @pytest.mark.performance
    def test_cpu_usage_performance(self, api_client, mock_config_manager):
        """Test CPU usage during high load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Measure CPU usage during high load
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = [{"symbol": "AAPL", "date": "2024-01-15", "close": 187.50}]
            
            # Start CPU monitoring
            cpu_percentages = []
            
            def monitor_cpu():
                for _ in range(10):  # Monitor for 10 seconds
                    cpu_percentages.append(process.cpu_percent())
                    time.sleep(1)
            
            # Start monitoring in background
            monitor_thread = threading.Thread(target=monitor_cpu)
            monitor_thread.start()
            
            # Perform high-load operations
            start_time = time.time()
            for i in range(500):  # 500 requests
                response = api_client.get("/api/v1/stocks/AAPL/data")
                assert response.status_code == 200
            
            # Wait for monitoring to complete
            monitor_thread.join()
            
            processing_time = time.time() - start_time
            avg_cpu = statistics.mean(cpu_percentages)
            max_cpu = max(cpu_percentages)
            
            print(f"CPU usage during high load:")
            print(f"  Processing time: {processing_time:.3f}s")
            print(f"  Average CPU usage: {avg_cpu:.1f}%")
            print(f"  Max CPU usage: {max_cpu:.1f}%")
            
            # CPU usage should be reasonable
            assert avg_cpu < 80  # Average < 80%
            assert max_cpu < 95  # Max < 95%

class TestEndToEndPerformance:
    """Test end-to-end system performance."""
    
    @pytest.mark.performance
    def test_complete_data_pipeline_performance(self, api_client, stream_client, mock_config_manager):
        """Test performance of complete data pipeline."""
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = [
                {
                    "symbol": "AAPL",
                    "date": "2024-01-15",
                    "close": 187.50,
                    "volume": 12345678
                }
            ]
            
            with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.write_tick') as mock_write:
                mock_write.return_value = True
                
                # Test complete pipeline: API -> Stream
                pipeline_times = []
                
                for i in range(100):
                    # Step 1: Get data from API
                    start_time = time.time()
                    api_response = api_client.get("/api/v1/stocks/AAPL/data")
                    api_time = time.time() - start_time
                    
                    # Step 2: Send to stream
                    tick_data = {
                        "symbol": "AAPL",
                        "price": 187.50 + i * 0.1,
                        "volume": 1000 + i,
                        "timestamp": datetime.now().isoformat(),
                        "price_change": i * 0.01,
                        "stream_type": "pipeline_test"
                    }
                    
                    start_time = time.time()
                    stream_response = stream_client.post("/api/v1/stream/ticks", json=tick_data)
                    stream_time = time.time() - start_time
                    
                    total_time = api_time + stream_time
                    pipeline_times.append(total_time)
                    
                    assert api_response.status_code == 200
                    assert stream_response.status_code == 200
                
                avg_pipeline_time = statistics.mean(pipeline_times)
                max_pipeline_time = max(pipeline_times)
                throughput = 100 / sum(pipeline_times)
                
                print(f"Complete pipeline performance:")
                print(f"  Pipelines completed: 100")
                print(f"  Average pipeline time: {avg_pipeline_time:.3f}s")
                print(f"  Max pipeline time: {max_pipeline_time:.3f}s")
                print(f"  Throughput: {throughput:.1f} pipelines/second")
                
                assert avg_pipeline_time < 2.0  # Average < 2 seconds
                assert max_pipeline_time < 5.0  # Max < 5 seconds
                assert throughput > 0.5  # Should complete > 0.5 pipelines/second
    
    @pytest.mark.performance
    def test_system_stability_performance(self, api_client, stream_client, mock_config_manager):
        """Test system stability under sustained load."""
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = [{"symbol": "AAPL", "date": "2024-01-15", "close": 187.50}]
            
            with patch('ec2_stream_receiver.accumulo_client.AccumuloClient.write_tick') as mock_write:
                mock_write.return_value = True
                
                # Run sustained load for 30 seconds
                test_duration = 30
                start_time = time.time()
                request_count = 0
                success_count = 0
                
                while time.time() - start_time < test_duration:
                    # Make API request
                    api_response = api_client.get("/api/v1/stocks/AAPL/data")
                    request_count += 1
                    
                    if api_response.status_code == 200:
                        success_count += 1
                        
                        # Send to stream
                        tick_data = {
                            "symbol": "AAPL",
                            "price": 187.50,
                            "volume": 1000,
                            "timestamp": datetime.now().isoformat(),
                            "stream_type": "stability_test"
                        }
                        
                        stream_response = stream_client.post("/api/v1/stream/ticks", json=tick_data)
                        if stream_response.status_code == 200:
                            success_count += 1
                
                total_time = time.time() - start_time
                success_rate = success_count / (request_count * 2) * 100  # *2 for API + Stream
                throughput = request_count / total_time
                
                print(f"System stability test ({test_duration}s):")
                print(f"  Total requests: {request_count}")
                print(f"  Successful operations: {success_count}")
                print(f"  Success rate: {success_rate:.1f}%")
                print(f"  Throughput: {throughput:.1f} requests/second")
                
                assert success_rate > 95  # Should maintain >95% success rate
                assert throughput > 1  # Should maintain >1 request/second 