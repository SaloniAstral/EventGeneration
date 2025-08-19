#!/usr/bin/env python3
"""
MongoDB Database Reader - Stock Data Access
==========================================

This file reads stock data from the MongoDB database for the streaming simulator.
It handles:
- Reading stock prices and company information
- Filtering data by symbols and time ranges
- Data formatting for streaming
- Connection management and error handling

Think of this as the "data reader" that gets stock data from the database for streaming.
"""

import requests
import logging
from typing import Dict, List, Optional
import sys
sys.path.append('/app')
from config.config_manager import config
import sys
import os
from datetime import datetime

# Add parent directory to path to import database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database.mongodb_manager import get_mongodb_manager, initialize_mongodb
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logging.warning("⚠️ MongoDB dependencies not available, using API fallback")

logger = logging.getLogger(__name__)

class MongoDBStockDataReader:
    """Reads stock data from MongoDB database or API"""
    
    def __init__(self):
        # Use Docker service name for internal communication
        self.api_base_url = "http://api-server:8000"
        self.client = None
        self.database = None
        
        # Initialize MongoDB if available
        if MONGODB_AVAILABLE:
            try:
                if initialize_mongodb():
                    self.client = get_mongodb_manager().client
                    self.database = get_mongodb_manager().database
                    logger.info("✅ MongoDB database initialized")
                else:
                    logger.warning("⚠️ Failed to initialize MongoDB, using API fallback")
            except Exception as e:
                logger.error(f"❌ MongoDB initialization failed: {e}")
    
    def get_stock_count(self) -> int:
        """Get total number of stocks with data"""
        if self.database is not None:
            try:
                collection = self.database.stock_prices
                count = len(collection.distinct('symbol'))
                logger.info(f"✅ Found {count} stocks in MongoDB database")
                return count
            except Exception as e:
                logger.error(f"❌ MongoDB query failed: {e}")
        
        # Fallback to API
        try:
            response = requests.get(f"{self.api_base_url}/status")
            if response.status_code == 200:
                data = response.json()
                if data and 'unique_symbols' in data:
                    count = data['unique_symbols']
                    logger.info(f"✅ Found {count} stocks via API")
                    return count
        except Exception as e:
            logger.error(f"❌ API query failed: {e}")
        
        return 0
    
    async def get_symbol_count(self) -> int:
        """Async version of get_stock_count for use in async contexts"""
        return self.get_stock_count()
    
    async def get_all_tickers(self) -> List[Dict]:
        """Async version of get_latest_stock_prices for use in async contexts"""
        return self.get_latest_stock_prices()
    
    async def get_all_symbols(self) -> List[str]:
        """Async version of get_stocks_with_data for use in async contexts"""
        return self.get_stocks_with_data()
    
    def get_stocks_with_data(self) -> List[str]:
        """Get list of stock symbols with data"""
        if self.database is not None:
            try:
                collection = self.database.stock_prices
                symbols = collection.distinct('symbol')
                symbols.sort()
                logger.info(f"✅ Retrieved {len(symbols)} stock symbols from MongoDB")
                return symbols
            except Exception as e:
                logger.error(f"❌ MongoDB query failed: {e}")
        
        # Fallback to API
        try:
            response = requests.get(f"{self.api_base_url}/symbols")
            if response.status_code == 200:
                data = response.json()
                if data and 'symbols' in data:
                    symbols = data['symbols']
                    logger.info(f"✅ Retrieved {len(symbols)} stock symbols via API")
                    return symbols
        except Exception as e:
            logger.error(f"❌ API query failed: {e}")
        
        return []
    
    def get_stock_data(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get stock data for a specific symbol"""
        if self.database is not None:
            try:
                collection = self.database.stock_prices
                cursor = collection.find(
                    {'symbol': symbol},
                    {'_id': 0}  # Exclude MongoDB _id
                ).sort('date', -1).limit(limit)
                
                data = list(cursor)
                logger.info(f"✅ Retrieved {len(data)} records for {symbol} from MongoDB")
                return data
            except Exception as e:
                logger.error(f"❌ MongoDB query failed: {e}")
        
        # Fallback to API
        try:
            response = requests.get(f"{self.api_base_url}/stock-data/{symbol}?limit={limit}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Retrieved {len(data)} records for {symbol} via API")
                return data
        except Exception as e:
            logger.error(f"❌ API query failed: {e}")
        
        return []
    
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get company information for a symbol"""
        if self.database:
            try:
                collection = self.database.companies
                company = collection.find_one(
                    {'symbol': symbol},
                    {'_id': 0}  # Exclude MongoDB _id
                )
                
                if company:
                    logger.info(f"✅ Retrieved company info for {symbol} from MongoDB")
                    return company
                else:
                    logger.info(f"⚠️ No company info found for {symbol} in MongoDB")
                    return None
            except Exception as e:
                logger.error(f"❌ MongoDB query failed: {e}")
        
        # Fallback to API
        try:
            response = requests.get(f"{self.api_base_url}/company-info/{symbol}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Retrieved company info for {symbol} via API")
                return data
        except Exception as e:
            logger.error(f"❌ API query failed: {e}")
        
        return None
    
    def get_latest_stock_prices(self) -> List[Dict]:
        """Get latest stock prices for all symbols"""
        # Try API first since MongoDB connection might not work in driver container
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/stocks")
            if response.status_code == 200:
                data = response.json()
                # Convert to the expected format
                formatted_data = []
                for stock in data:
                    if stock.get('has_data') and stock.get('latest_price') is not None:
                        formatted_data.append({
                            'symbol': stock['symbol'],
                            'close_price': stock['latest_price'] if stock['latest_price'] > 0 else 100.0,  # Default price if 0
                            'volume': 1000000  # Default volume
                        })
                logger.info(f"✅ Retrieved latest prices for {len(formatted_data)} symbols via API")
                return formatted_data
        except Exception as e:
            logger.error(f"❌ API query failed: {e}")
        
        # Fallback to MongoDB if API fails
        if self.database:
            try:
                collection = self.database.stock_prices
                
                # Use aggregation to get latest price for each symbol
                pipeline = [
                    {
                        '$sort': {'date': -1}
                    },
                    {
                        '$group': {
                            '_id': '$symbol',
                            'latest_data': {'$first': '$$ROOT'}
                        }
                    },
                    {
                        '$replaceRoot': {'newRoot': '$latest_data'}
                    },
                    {
                        '$project': {'_id': 0}
                    }
                ]
                
                cursor = collection.aggregate(pipeline)
                data = list(cursor)
                logger.info(f"✅ Retrieved latest prices for {len(data)} symbols from MongoDB")
                return data
            except Exception as e:
                logger.error(f"❌ MongoDB aggregation failed: {e}")
        
        return []
    
    def check_database_health(self) -> Dict[str, any]:
        """Check database health and connectivity"""
        health_status = {
            'mongodb_available': MONGODB_AVAILABLE,
            'mongodb_connected': False,
            'api_available': False,
            'total_symbols': 0,
            'total_records': 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Check MongoDB health
        if self.database:
            try:
                # Test connection
                self.database.command('ping')
                health_status['mongodb_connected'] = True
                
                # Get basic stats
                stock_prices_collection = self.database.stock_prices
                health_status['total_symbols'] = len(stock_prices_collection.distinct('symbol'))
                health_status['total_records'] = stock_prices_collection.count_documents({})
                
                logger.info("✅ MongoDB health check passed")
            except Exception as e:
                logger.error(f"❌ MongoDB health check failed: {e}")
        
        # Check API health
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            health_status['api_available'] = response.status_code == 200
            logger.info("✅ API health check passed")
        except Exception as e:
            logger.error(f"❌ API health check failed: {e}")
        
        return health_status
    
    def get_database_stats(self) -> Dict[str, any]:
        """Get detailed database statistics"""
        stats = {
            'collections': {},
            'total_symbols': 0,
            'total_records': 0,
            'latest_update': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.database:
            try:
                collections = ['companies', 'stock_prices', 'stock_ticks', 'events', 'system_status', 'fetch_logs']
                
                for collection_name in collections:
                    collection = self.database[collection_name]
                    count = collection.count_documents({})
                    stats['collections'][collection_name] = count
                
                # Get total symbols
                stock_prices_collection = self.database.stock_prices
                stats['total_symbols'] = len(stock_prices_collection.distinct('symbol'))
                stats['total_records'] = stock_prices_collection.count_documents({})
                
                # Get latest update
                latest_record = stock_prices_collection.find_one(
                    sort=[('created_at', -1)]
                )
                if latest_record and 'created_at' in latest_record:
                    stats['latest_update'] = latest_record['created_at'].isoformat()
                
                logger.info("✅ MongoDB stats retrieved successfully")
            except Exception as e:
                logger.error(f"❌ Failed to get MongoDB stats: {e}")
        
        return stats
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("🔒 MongoDB connection closed")

# Global reader instance
stock_data_reader = MongoDBStockDataReader()

def get_stock_data_reader() -> MongoDBStockDataReader:
    """Get the global stock data reader instance"""
    return stock_data_reader 