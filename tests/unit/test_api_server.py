#!/usr/bin/env python3
"""
Unit Tests for API Server
Tests individual components and functions of the API Server
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import the modules to test
from ec2_api_server.main import app
from ec2_api_server.data_service import DataService
from ec2_api_server.alpha_vantage_client import AlphaVantageClient
from ec2_api_server.sns_publisher import SNSPublisher

class TestAlphaVantageClient:
    """Test Alpha Vantage API client."""
    
    @pytest.fixture
    def client(self):
        """Create Alpha Vantage client for testing."""
        return AlphaVantageClient(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_fetch_stock_data_success(self, client, mock_alpha_vantage):
        """Test successful stock data fetching."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = Mock(return_value={
                "Meta Data": {
                    "1. Information": "Daily Prices",
                    "2. Symbol": "AAPL",
                    "3. Last Refreshed": "2024-01-15"
                },
                "Time Series (Daily)": {
                    "2024-01-15": {
                        "1. open": "185.59",
                        "2. high": "188.75",
                        "3. low": "185.00",
                        "4. close": "187.50",
                        "5. volume": "12345678"
                    }
                }
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await client.fetch_stock_data("AAPL")
            
            assert result is not None
            assert "Meta Data" in result
            assert "Time Series (Daily)" in result
            assert result["Meta Data"]["2. Symbol"] == "AAPL"
    
    @pytest.mark.asyncio
    async def test_fetch_stock_data_error(self, client):
        """Test stock data fetching with error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 400
            mock_response.text = "Bad Request"
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(Exception):
                await client.fetch_stock_data("INVALID")
    
    @pytest.mark.asyncio
    async def test_fetch_company_overview_success(self, client):
        """Test successful company overview fetching."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = Mock(return_value={
                "Symbol": "AAPL",
                "Name": "Apple Inc",
                "Sector": "Technology",
                "Industry": "Consumer Electronics",
                "MarketCapitalization": "3000000000000"
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await client.fetch_company_overview("AAPL")
            
            assert result is not None
            assert result["Symbol"] == "AAPL"
            assert result["Name"] == "Apple Inc"
            assert result["Sector"] == "Technology"
    
    def test_build_url(self, client):
        """Test URL building for API requests."""
        url = client._build_url("TIME_SERIES_DAILY", {"symbol": "AAPL"})
        
        assert "alphavantage.co" in url
        assert "function=TIME_SERIES_DAILY" in url
        assert "symbol=AAPL" in url
        assert "apikey=test-key" in url

class TestDataService:
    """Test Data Service component."""
    
    @pytest.fixture
    def data_service(self, mock_config_manager):
        """Create Data Service for testing."""
        return DataService()
    
    def test_parse_stock_data(self, data_service):
        """Test stock data parsing."""
        raw_data = {
            "Meta Data": {
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2024-01-15"
            },
            "Time Series (Daily)": {
                "2024-01-15": {
                    "1. open": "185.59",
                    "2. high": "188.75",
                    "3. low": "185.00",
                    "4. close": "187.50",
                    "5. volume": "12345678"
                }
            }
        }
        
        parsed_data = data_service.parse_stock_data(raw_data)
        
        assert len(parsed_data) == 1
        stock_record = parsed_data[0]
        assert stock_record["symbol"] == "AAPL"
        assert stock_record["date"] == "2024-01-15"
        assert stock_record["open"] == 185.59
        assert stock_record["high"] == 188.75
        assert stock_record["low"] == 185.00
        assert stock_record["close"] == 187.50
        assert stock_record["volume"] == 12345678
    
    def test_parse_company_data(self, data_service):
        """Test company data parsing."""
        raw_data = {
            "Symbol": "AAPL",
            "Name": "Apple Inc",
            "Sector": "Technology",
            "Industry": "Consumer Electronics",
            "Description": "Apple designs and manufactures...",
            "MarketCapitalization": "3000000000000",
            "PERatio": "30.5"
        }
        
        parsed_data = data_service.parse_company_data(raw_data)
        
        assert parsed_data["symbol"] == "AAPL"
        assert parsed_data["name"] == "Apple Inc"
        assert parsed_data["sector"] == "Technology"
        assert parsed_data["industry"] == "Consumer Electronics"
        assert parsed_data["description"] == "Apple designs and manufactures..."
        assert parsed_data["market_cap"] == "3000000000000"
        assert parsed_data["pe_ratio"] == "30.5"
    
    def test_validate_symbol(self, data_service):
        """Test symbol validation."""
        # Valid symbols
        assert data_service.validate_symbol("AAPL") == True
        assert data_service.validate_symbol("GOOGL") == True
        assert data_service.validate_symbol("MSFT") == True
        
        # Invalid symbols
        assert data_service.validate_symbol("") == False
        assert data_service.validate_symbol("A" * 11) == False  # Too long
        assert data_service.validate_symbol("123") == False  # Numbers only
        assert data_service.validate_symbol("A@PL") == False  # Invalid characters
    
    def test_calculate_price_change(self, data_service):
        """Test price change calculation."""
        # Positive change
        change = data_service.calculate_price_change(100.0, 110.0)
        assert change == 10.0
        
        # Negative change
        change = data_service.calculate_price_change(100.0, 90.0)
        assert change == -10.0
        
        # No change
        change = data_service.calculate_price_change(100.0, 100.0)
        assert change == 0.0
    
    def test_format_currency(self, data_service):
        """Test currency formatting."""
        # Large numbers
        assert data_service.format_currency(1000000000) == "$1.00B"
        assert data_service.format_currency(1500000000) == "$1.50B"
        assert data_service.format_currency(1000000) == "$1.00M"
        assert data_service.format_currency(1500000) == "$1.50M"
        
        # Small numbers
        assert data_service.format_currency(1000) == "$1.00K"
        assert data_service.format_currency(1500) == "$1.50K"
        assert data_service.format_currency(100) == "$100.00"

class TestSNSPublisher:
    """Test SNS Publisher component."""
    
    @pytest.fixture
    def sns_publisher(self, mock_config_manager):
        """Create SNS Publisher for testing."""
        return SNSPublisher()
    
    def test_publish_event_success(self, sns_publisher, mock_sns):
        """Test successful event publishing."""
        event_data = {
            "event_type": "stock_data_updated",
            "symbol": "AAPL",
            "timestamp": datetime.now().isoformat()
        }
        
        result = sns_publisher.publish_event(event_data)
        
        assert result == True
        mock_sns.publish.assert_called_once()
    
    def test_publish_event_failure(self, sns_publisher):
        """Test event publishing failure."""
        with patch('boto3.client') as mock_boto3:
            mock_sns = Mock()
            mock_sns.publish.side_effect = Exception("SNS Error")
            mock_boto3.return_value = mock_sns
            
            event_data = {"event_type": "test"}
            
            result = sns_publisher.publish_event(event_data)
            
            assert result == False
    
    def test_format_message(self, sns_publisher):
        """Test message formatting."""
        event_data = {
            "event_type": "stock_data_updated",
            "symbol": "AAPL",
            "timestamp": "2024-01-15T10:30:00"
        }
        
        message = sns_publisher._format_message(event_data)
        
        assert "stock_data_updated" in message
        assert "AAPL" in message
        assert "2024-01-15T10:30:00" in message

class TestAPIServerEndpoints:
    """Test API Server endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
    
    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_get_all_stocks(self, client, mock_config_manager):
        """Test get all stocks endpoint."""
        with patch('ec2_api_server.data_service.DataService.get_all_symbols') as mock_get:
            mock_get.return_value = ["AAPL", "GOOGL", "MSFT"]
            
            response = client.get("/api/v1/stocks")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            assert "AAPL" in [stock["symbol"] for stock in data]
    
    def test_get_stock_data(self, client, mock_config_manager):
        """Test get stock data endpoint."""
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = [
                {
                    "symbol": "AAPL",
                    "date": "2024-01-15",
                    "close": 187.50,
                    "volume": 12345678
                }
            ]
            
            response = client.get("/api/v1/stocks/AAPL/data")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["symbol"] == "AAPL"
    
    def test_get_stock_data_not_found(self, client, mock_config_manager):
        """Test get stock data for non-existent symbol."""
        with patch('ec2_api_server.data_service.DataService.get_stock_data') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/stocks/INVALID/data")
            
            assert response.status_code == 404
    
    def test_get_latest_stock_data(self, client, mock_config_manager):
        """Test get latest stock data endpoint."""
        with patch('ec2_api_server.data_service.DataService.get_latest_stock_data') as mock_get:
            mock_get.return_value = {
                "symbol": "AAPL",
                "date": "2024-01-15",
                "close": 187.50,
                "volume": 12345678
            }
            
            response = client.get("/api/v1/stocks/AAPL/latest")
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["close"] == 187.50
    
    def test_get_current_price(self, client, mock_config_manager):
        """Test get current price endpoint."""
        with patch('ec2_api_server.data_service.DataService.get_current_price') as mock_get:
            mock_get.return_value = 187.50
            
            response = client.get("/api/v1/stocks/AAPL/price")
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["price"] == 187.50
    
    def test_get_company_info(self, client, mock_config_manager):
        """Test get company info endpoint."""
        with patch('ec2_api_server.data_service.DataService.get_company_info') as mock_get:
            mock_get.return_value = {
                "symbol": "AAPL",
                "name": "Apple Inc",
                "sector": "Technology",
                "industry": "Consumer Electronics"
            }
            
            response = client.get("/api/v1/stocks/AAPL/company")
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["name"] == "Apple Inc"
            assert data["sector"] == "Technology"
    
    def test_search_stocks(self, client, mock_config_manager):
        """Test search stocks endpoint."""
        with patch('ec2_api_server.data_service.DataService.search_stocks') as mock_search:
            mock_search.return_value = [
                {"symbol": "AAPL", "name": "Apple Inc"},
                {"symbol": "AAPL.L", "name": "Apple Inc London"}
            ]
            
            response = client.post("/api/v1/search", json={
                "query": "Apple",
                "limit": 10
            })
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert "Apple" in data[0]["name"]
    
    def test_get_events(self, client, mock_config_manager):
        """Test get events endpoint."""
        with patch('ec2_api_server.data_service.DataService.get_recent_events') as mock_get:
            mock_get.return_value = [
                {
                    "event_id": "test-1",
                    "event_type": "stock_data_updated",
                    "timestamp": "2024-01-15T10:30:00"
                }
            ]
            
            response = client.get("/api/v1/events")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["event_type"] == "stock_data_updated"
    
    def test_get_database_stats(self, client, mock_config_manager):
        """Test get database stats endpoint."""
        with patch('ec2_api_server.data_service.DataService.get_database_stats') as mock_get:
            mock_get.return_value = {
                "total_symbols": 100,
                "total_records": 50000,
                "last_updated": "2024-01-15T10:30:00"
            }
            
            response = client.get("/api/v1/database/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_symbols"] == 100
            assert data["total_records"] == 50000
    
    def test_delete_stock_data(self, client, mock_config_manager):
        """Test delete stock data endpoint."""
        with patch('ec2_api_server.data_service.DataService.delete_stock_data') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete("/api/v1/stocks/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Stock data deleted successfully"
    
    def test_refresh_stock_data(self, client, mock_config_manager):
        """Test refresh stock data endpoint."""
        with patch('ec2_api_server.data_service.DataService.refresh_stock_data') as mock_refresh:
            mock_refresh.return_value = True
            
            response = client.post("/api/v1/stocks/AAPL/refresh")
            
            assert response.status_code == 202
            data = response.json()
            assert data["message"] == "Stock data refresh started"

class TestErrorHandling:
    """Test error handling in API Server."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_invalid_symbol_validation(self, client):
        """Test invalid symbol validation."""
        response = client.get("/api/v1/stocks/INVALID_SYMBOL_123/data")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid symbol" in data["detail"]
    
    def test_missing_required_fields(self, client):
        """Test missing required fields in requests."""
        response = client.post("/api/v1/search", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_internal_server_error(self, client, mock_config_manager):
        """Test internal server error handling."""
        with patch('ec2_api_server.data_service.DataService.get_all_symbols') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            response = client.get("/api/v1/stocks")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

class TestDataValidation:
    """Test data validation functions."""
    
    def test_validate_date_format(self):
        """Test date format validation."""
        from ec2_api_server.data_service import DataService
        
        data_service = DataService()
        
        # Valid dates
        assert data_service.validate_date("2024-01-15") == True
        assert data_service.validate_date("2023-12-31") == True
        
        # Invalid dates
        assert data_service.validate_date("2024-13-01") == False  # Invalid month
        assert data_service.validate_date("2024-01-32") == False  # Invalid day
        assert data_service.validate_date("invalid-date") == False
        assert data_service.validate_date("") == False
    
    def test_validate_price_range(self):
        """Test price range validation."""
        from ec2_api_server.data_service import DataService
        
        data_service = DataService()
        
        # Valid prices
        assert data_service.validate_price(0.01) == True
        assert data_service.validate_price(100.0) == True
        assert data_service.validate_price(10000.0) == True
        
        # Invalid prices
        assert data_service.validate_price(-1.0) == False
        assert data_service.validate_price(0.0) == False
        assert data_service.validate_price(100000.0) == False  # Too high
    
    def test_validate_volume(self):
        """Test volume validation."""
        from ec2_api_server.data_service import DataService
        
        data_service = DataService()
        
        # Valid volumes
        assert data_service.validate_volume(1) == True
        assert data_service.validate_volume(1000000) == True
        assert data_service.validate_volume(1000000000) == True
        
        # Invalid volumes
        assert data_service.validate_volume(-1) == False
        assert data_service.validate_volume(0) == False 