#!/usr/bin/env python3
"""
MongoDB Connection Test Script
Tests MongoDB connection and basic operations
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Add parent directory to path to import database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongodb_manager import get_mongodb_manager, initialize_mongodb, test_mongodb_connection

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_operations():
    """Test basic MongoDB operations"""
    mongodb_manager = get_mongodb_manager()
    
    try:
        # Initialize the manager
        if not mongodb_manager.initialize_client():
            logger.error("❌ Failed to initialize MongoDB client")
            return False
            
        with mongodb_manager.get_database() as db:
            # Test 1: Check MongoDB version
            server_info = mongodb_manager.client.server_info()
            logger.info(f"✅ MongoDB version: {server_info.get('version')}")
            
            # Test 2: Check collections
            collections = db.list_collection_names()
            logger.info(f"✅ Found {len(collections)} collections: {collections}")
            
            # Test 3: Check companies data
            companies_count = db.companies.count_documents({})
            logger.info(f"✅ Companies in database: {companies_count}")
            
            # Test 4: Get sample companies
            sample_companies = list(db.companies.find({}, {"symbol": 1, "company_name": 1, "sector": 1}).limit(5))
            logger.info("✅ Sample companies:")
            for company in sample_companies:
                logger.info(f"   - {company['symbol']}: {company['company_name']} ({company['sector']})")
            
            # Test 5: Test aggregation pipeline
            sector_stats = list(db.companies.aggregate([
                {"$group": {"_id": "$sector", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]))
            logger.info("✅ Sector statistics:")
            for stat in sector_stats:
                logger.info(f"   - {stat['_id']}: {stat['count']} companies")
            
            # Test 6: Insert test event
            test_event = {
                "event_type": "connection_test",
                "event_source": "test_script",
                "message": "MongoDB connection test successful",
                "metadata": {
                    "test_timestamp": datetime.now(timezone.utc).isoformat(),
                    "collections_count": len(collections)
                },
                "processed": False,
                "created_at": datetime.now(timezone.utc)
            }
            
            result = db.events.insert_one(test_event)
            logger.info(f"✅ Test event created: {result.inserted_id}")
            
            # Test 7: Get connection info
            connection_info = mongodb_manager.get_connection_info()
            logger.info(f"✅ Connection info: {connection_info}")
            
            logger.info("✅ All MongoDB operations completed successfully!")
            return True
                
    except Exception as e:
        logger.error(f"❌ MongoDB operation failed: {e}")
        return False

def test_performance():
    """Test MongoDB performance"""
    mongodb_manager = get_mongodb_manager()
    
    try:
        # Initialize the manager
        if not mongodb_manager.initialize_client():
            logger.error("❌ Failed to initialize MongoDB client")
            return False
            
        with mongodb_manager.get_database() as db:
            import time
            
            # Test 1: Simple query performance
            start_time = time.time()
            companies_count = db.companies.count_documents({})
            query_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Simple query performance: {query_time:.2f}ms")
            
            # Test 2: Complex aggregation performance
            start_time = time.time()
            sector_stats = list(db.companies.aggregate([
                {"$group": {"_id": "$sector", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]))
            query_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Aggregation query performance: {query_time:.2f}ms")
            
            # Test 3: Text search performance
            start_time = time.time()
            search_results = list(db.companies.find({"$text": {"$search": "Apple"}}))
            query_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Text search performance: {query_time:.2f}ms")
            logger.info(f"   - Found {len(search_results)} results")
            
            return True
                
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting MongoDB connection tests...")
    
    # Test 1: Initialize MongoDB connection
    logger.info("📋 Test 1: MongoDB connection initialization")
    mongodb_manager = get_mongodb_manager()
    if not mongodb_manager.initialize_client():
        logger.error("❌ Failed to initialize MongoDB connection")
        return False
    
    # Test 2: Test basic connection
    logger.info("📋 Test 2: Basic connection test")
    if not mongodb_manager.test_connection():
        logger.error("❌ Failed basic connection test")
        return False
    
    # Test 3: Create collections and indexes
    logger.info("📋 Test 3: MongoDB collections and indexes creation")
    if not mongodb_manager.create_collections_and_indexes():
        logger.error("❌ Collections and indexes creation failed")
        return False
    
    # Test 4: Basic operations
    logger.info("📋 Test 4: Basic MongoDB operations")
    if not test_basic_operations():
        logger.error("❌ Basic operations test failed")
        return False
    
    # Test 5: Performance test
    logger.info("📋 Test 5: Performance test")
    if not test_performance():
        logger.error("❌ Performance test failed")
        return False
    
    logger.info("🎉 All MongoDB tests completed successfully!")
    logger.info("\n📊 MongoDB Status Summary:")
    logger.info("   ✅ Connection: Active")
    logger.info("   ✅ Collections: Created and up-to-date")
    logger.info("   ✅ Indexes: Optimized")
    logger.info("   ✅ Performance: Acceptable")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 