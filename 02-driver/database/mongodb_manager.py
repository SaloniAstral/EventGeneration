#!/usr/bin/env python3
"""
Consolidated MongoDB Manager for Financial Data Streaming System
Combines connection management, models, and schema in one module
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, DuplicateKeyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class MongoDBManager:
    """Consolidated MongoDB manager for financial data"""
    
    def __init__(self):
        # MongoDB connection parameters
        self.connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/stockdata')
        self.database_name = os.getenv('MONGODB_DATABASE', 'stockdata')
        
        # Connection pool settings
        self.max_pool_size = int(os.getenv('MONGODB_MAX_POOL_SIZE', 10))
        self.min_pool_size = int(os.getenv('MONGODB_MIN_POOL_SIZE', 1))
        self.max_idle_time_ms = int(os.getenv('MONGODB_MAX_IDLE_TIME_MS', 30000))
        
        # Connection timeout settings
        self.server_selection_timeout_ms = int(os.getenv('MONGODB_SERVER_SELECTION_TIMEOUT_MS', 5000))
        self.connect_timeout_ms = int(os.getenv('MONGODB_CONNECT_TIMEOUT_MS', 20000))
        self.socket_timeout_ms = int(os.getenv('MONGODB_SOCKET_TIMEOUT_MS', 20000))
        
        # MongoDB client
        self.client: Optional[MongoClient] = None
        self.database = None
        
    def initialize_client(self):
        """Initialize MongoDB client with connection pooling"""
        try:
            self.client = MongoClient(
                self.connection_string,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                maxIdleTimeMS=self.max_idle_time_ms,
                serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                connectTimeoutMS=self.connect_timeout_ms,
                socketTimeoutMS=self.socket_timeout_ms,
                retryWrites=True,
                retryReads=True
            )
            
            # Get database
            self.database = self.client[self.database_name]
            
            # Create collections and indexes
            self.create_collections_and_indexes()
            
            logger.info(f"✅ MongoDB client initialized: {self.database_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB client: {e}")
            return False
    
    def create_collections_and_indexes(self):
        """Create all collections and indexes"""
        try:
            if self.database is None:
                return False
            
            self._create_companies_collection()
            self._create_stock_prices_collection()
            self._create_stock_ticks_collection()
            self._create_events_collection()
            self._create_system_status_collection()
            self._create_fetch_logs_collection()
                
            logger.info("✅ All MongoDB collections and indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collections and indexes: {e}")
            return False
    
    def _create_companies_collection(self):
        """Create companies collection with indexes"""
        collection = self.database.companies
        
        # Create indexes
        collection.create_index([("symbol", ASCENDING)], unique=True)
        collection.create_index([("sector", ASCENDING)])
        collection.create_index([("industry", ASCENDING)])
        collection.create_index([("company_name", TEXT)])
        
        logger.info("✅ Companies collection and indexes created")
    
    def _create_stock_prices_collection(self):
        """Create stock_prices collection with time-series indexes"""
        collection = self.database.stock_prices
        
        # Create indexes for time-series queries
        collection.create_index([("symbol", ASCENDING), ("date", DESCENDING)])
        collection.create_index([("date", DESCENDING)])
        collection.create_index([("symbol", ASCENDING)])
        collection.create_index([("symbol", ASCENDING), ("date", ASCENDING)], unique=True)
        
        logger.info("✅ Stock prices collection and indexes created")
    
    def _create_stock_ticks_collection(self):
        """Create stock_ticks collection for real-time streaming data"""
        collection = self.database.stock_ticks
        
        # Create indexes for streaming queries
        collection.create_index([("symbol", ASCENDING), ("timestamp", DESCENDING)])
        collection.create_index([("timestamp", DESCENDING)])
        collection.create_index([("stream_type", ASCENDING)])
        collection.create_index([("tick_number", DESCENDING)])
        
        # TTL index to automatically delete old ticks (keep 7 days)
        collection.create_index([("timestamp", ASCENDING)], expireAfterSeconds=7*24*60*60)
        
        logger.info("✅ Stock ticks collection and indexes created")
    
    def _create_events_collection(self):
        """Create events collection for SNS and system events"""
        collection = self.database.events
        
        # Create indexes for event queries
        collection.create_index([("event_type", ASCENDING), ("created_at", DESCENDING)])
        collection.create_index([("event_source", ASCENDING)])
        collection.create_index([("symbol", ASCENDING)])
        collection.create_index([("processed", ASCENDING)])
        collection.create_index([("created_at", DESCENDING)])
        
        # TTL index to automatically delete old events (keep 30 days)
        collection.create_index([("created_at", ASCENDING)], expireAfterSeconds=30*24*60*60)
        
        logger.info("✅ Events collection and indexes created")
    
    def _create_system_status_collection(self):
        """Create system_status collection for health monitoring"""
        collection = self.database.system_status
        
        # Create indexes for status queries
        collection.create_index([("service_name", ASCENDING), ("timestamp", DESCENDING)])
        collection.create_index([("status", ASCENDING)])
        collection.create_index([("timestamp", DESCENDING)])
        
        # TTL index to automatically delete old status (keep 7 days)
        collection.create_index([("timestamp", ASCENDING)], expireAfterSeconds=7*24*60*60)
        
        logger.info("✅ System status collection and indexes created")
    
    def _create_fetch_logs_collection(self):
        """Create fetch_logs collection for data fetch operations"""
        collection = self.database.fetch_logs
        
        # Create indexes for log queries
        collection.create_index([("symbol", ASCENDING), ("timestamp", DESCENDING)])
        collection.create_index([("status", ASCENDING)])
        collection.create_index([("timestamp", DESCENDING)])
        
        # TTL index to automatically delete old logs (keep 30 days)
        collection.create_index([("timestamp", ASCENDING)], expireAfterSeconds=30*24*60*60)
        
        logger.info("✅ Fetch logs collection and indexes created")
    
    @contextmanager
    def get_database(self):
        """Get MongoDB database context"""
        if not self.client:
            raise Exception("MongoDB client not initialized. Call initialize_client() first.")
        
        try:
            yield self.database
        except Exception as e:
            logger.error(f"❌ MongoDB database error: {e}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get MongoDB collection"""
        if self.database is None:
            self.initialize_client()
        return self.database[collection_name]
    
    # Data Operations
    def save_stock_data(self, symbol: str, time_series_data: dict) -> int:
        """Save stock price data to MongoDB from Alpha Vantage time series"""
        try:
            collection = self.get_collection('stock_prices')
            records_saved = 0
            
            for date_str, daily_data in time_series_data.items():
                # Parse date
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Invalid date format: {date_str}")
                    continue
                
                # Prepare document with Alpha Vantage format
                document = {
                    'symbol': symbol,
                    'date': date_obj,
                    'open_price': float(daily_data.get('1. open', 0)),
                    'high_price': float(daily_data.get('2. high', 0)),
                    'low_price': float(daily_data.get('3. low', 0)),
                    'close_price': float(daily_data.get('4. close', 0)),
                    'adjusted_close': float(daily_data.get('5. adjusted close', 0)) if daily_data.get('5. adjusted close') else None,
                    'volume': int(daily_data.get('5. volume', 0)),
                    'created_at': datetime.utcnow()
                }
                
                # Use upsert to avoid duplicates
                result = collection.update_one(
                    {'symbol': symbol, 'date': document['date']},
                    {'$set': document},
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count:
                    records_saved += 1
            
            logger.info(f"✅ Saved {records_saved} stock data records for {symbol}")
            return records_saved
            
        except Exception as e:
            logger.error(f"❌ Failed to save stock data for {symbol}: {e}")
            return 0
    
    def save_company_info(self, symbol: str, overview_data: dict) -> bool:
        """Save company information to MongoDB"""
        try:
            collection = self.get_collection('companies')
            
            # Prepare document with safe float conversion
            def safe_float(value, default=None):
                if value is None or value == 'None' or value == '':
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            document = {
                'symbol': symbol,
                'company_name': overview_data.get('Name', ''),
                'sector': overview_data.get('Sector', ''),
                'industry': overview_data.get('Industry', ''),
                'market_cap': safe_float(overview_data.get('MarketCapitalization')),
                'pe_ratio': safe_float(overview_data.get('PERatio')),
                'dividend_yield': safe_float(overview_data.get('DividendYield')),
                'description': overview_data.get('Description', ''),
                'updated_at': datetime.utcnow()
            }
            
            # Use upsert to avoid duplicates
            result = collection.update_one(
                {'symbol': symbol},
                {'$set': document},
                upsert=True
            )
            
            logger.info(f"✅ Saved company info for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save company info for {symbol}: {e}")
            return False
    
    def save_stock_tick(self, symbol: str, tick_data: dict) -> bool:
        """Save real-time stock tick data"""
        try:
            collection = self.get_collection('stock_ticks')
            
            # Prepare document
            document = {
                'symbol': symbol,
                'price': float(tick_data.get('price', 0)),
                'volume': int(tick_data.get('volume', 0)),
                'timestamp': tick_data.get('timestamp', datetime.utcnow()),
                'tick_number': tick_data.get('tick_number', 0),
                'stream_type': tick_data.get('stream_type', 'times_square_simulation'),
                'price_change': tick_data.get('price_change', 0),
                'current_price': tick_data.get('current_price', 0),
                'created_at': datetime.utcnow()
            }
            
            result = collection.insert_one(document)
            logger.info(f"✅ Saved tick data for {symbol}: tick #{document['tick_number']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save tick data for {symbol}: {e}")
            return False
    
    def create_event(self, event_type: str, event_source: str, symbol: str = None, message: str = None, metadata: dict = None) -> bool:
        """Create system event"""
        try:
            collection = self.get_collection('events')
            
            document = {
                'event_type': event_type,
                'event_source': event_source,
                'symbol': symbol,
                'message': message,
                'metadata': metadata or {},
                'processed': False,
                'created_at': datetime.utcnow()
            }
            
            result = collection.insert_one(document)
            logger.info(f"✅ Created event: {event_type} from {event_source}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create event: {e}")
            return False
    
    def log_fetch_operation(self, symbol: str, status: str, records_fetched: int = 0, error_message: str = None):
        """Log data fetch operation"""
        try:
            collection = self.get_collection('fetch_logs')
            
            document = {
                'symbol': symbol,
                'status': status,
                'records_fetched': records_fetched,
                'error_message': error_message,
                'timestamp': datetime.utcnow()
            }
            
            collection.insert_one(document)
            logger.info(f"✅ Logged fetch operation for {symbol}: {status}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log fetch operation: {e}")
    
    def get_stock_data(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get stock data for a symbol"""
        try:
            collection = self.get_collection('stock_prices')
            cursor = collection.find(
                {'symbol': symbol},
                {'_id': 0}
            ).sort('date', DESCENDING).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"❌ Failed to get stock data for {symbol}: {e}")
            return []
    
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get company information"""
        try:
            collection = self.get_collection('companies')
            return collection.find_one({'symbol': symbol}, {'_id': 0})
            
        except Exception as e:
            logger.error(f"❌ Failed to get company info for {symbol}: {e}")
            return None
    
    def get_all_symbols(self) -> List[str]:
        """Get all symbols from the companies collection"""
        try:
            collection = self.get_collection('companies')
            symbols = collection.distinct('symbol')
            symbols.sort()
            logger.info(f"✅ Retrieved {len(symbols)} symbols from companies collection")
            return symbols
            
        except Exception as e:
            logger.error(f"❌ Failed to get all symbols: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            collections = ['companies', 'stock_prices', 'stock_ticks', 'events', 'system_status', 'fetch_logs']
            
            logger.info(f"🔍 Getting database stats for collections: {collections}")
            
            for collection_name in collections:
                try:
                    collection = self.get_collection(collection_name)
                    count = collection.count_documents({})
                    stats[collection_name] = count
                    logger.info(f"📊 {collection_name}: {count} documents")
                except Exception as collection_error:
                    logger.error(f"❌ Failed to count {collection_name}: {collection_error}")
                    stats[collection_name] = 0
            
            logger.info(f"✅ Database stats completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            return {}
    
    def update_system_status(self, service_name: str, status: str, message: str = None, metrics: dict = None):
        """Update system status"""
        try:
            collection = self.get_collection('system_status')
            
            document = {
                'service_name': service_name,
                'status': status,
                'message': message,
                'metrics': metrics or {},
                'timestamp': datetime.utcnow()
            }
            
            collection.insert_one(document)
            logger.info(f"✅ Updated system status for {service_name}: {status}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update system status: {e}")
    
    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            if not self.client:
                return False
            
            # Ping the database
            self.client.admin.command('ping')
            logger.info("✅ MongoDB connection successful")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ MongoDB connection test failed: {e}")
            return False
    
    def close_client(self):
        """Close MongoDB client"""
        if self.client:
            self.client.close()
            logger.info("🔒 MongoDB client closed")
    
    def get_connection_info(self) -> dict:
        """Get connection information"""
        return {
            'connection_string': self.connection_string,
            'database_name': self.database_name,
            'max_pool_size': self.max_pool_size,
            'min_pool_size': self.min_pool_size,
            'connected': self.client is not None
        }

# Global instance
mongodb_manager = MongoDBManager()

def get_mongodb_manager() -> MongoDBManager:
    """Get MongoDB manager instance"""
    return mongodb_manager

def initialize_mongodb():
    """Initialize MongoDB connection"""
    return mongodb_manager.initialize_client()

def test_mongodb_connection():
    """Test MongoDB connection"""
    return mongodb_manager.test_connection()

def close_mongodb():
    """Close MongoDB connection"""
    mongodb_manager.close_client() 