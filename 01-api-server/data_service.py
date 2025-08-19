#!/usr/bin/env python3
"""
Data Service - Data Flow Orchestrator
====================================

This file manages the complete data flow process:
- Fetches stock data from Alpha Vantage
- Stores data in MongoDB database
- Sends SNS events to notify other services
- Handles scheduling and retries
- Manages data quality and validation

Think of this as the "conductor" that orchestrates the entire data collection process.
"""

import time
import os
import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional
from alpha_vantage_client import AlphaVantageClient
from database.mongodb_manager import get_mongodb_manager
from sns_publisher import SNSPublisher
from config.config_manager import config
from events.sns_event_publisher import get_sns_publisher, publish_stock_data_loaded, publish_batch_completed
import logging

logger = logging.getLogger(__name__)

class DataService:
    """Service for managing stock data operations"""
    
    def __init__(self):
        self.alpha_vantage = AlphaVantageClient()
        self.db_manager = get_mongodb_manager()
        self.sns_publisher = SNSPublisher()
        self.data_quality_url = os.getenv('DATA_QUALITY_URL', 'http://localhost:8003')
    
    async def validate_stock_data(self, data: Dict) -> Dict:
        """Validate stock data using data quality service"""
        try:
            async with aiohttp.ClientSession() as session:
                validation_request = {
                    "data": data,
                    "data_type": "stock_data",
                    "validate_and_clean": True
                }
                
                async with session.post(
                    f"{self.data_quality_url}/api/v1/validate",
                    json=validation_request,
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "is_valid": result.get("is_acceptable", True),
                            "quality_score": result.get("quality_score", 1.0),
                            "validation_summary": result.get("validation_summary", {}),
                            "errors": [r for r in result.get("validation_results", []) if not r.get("passed", True)]
                        }
                    else:
                        logger.warning(f"Data quality service returned {response.status}")
                        return {"is_valid": True, "quality_score": 1.0, "errors": []}
        except Exception as e:
            logger.warning(f"Data quality validation failed: {e}")
            return {"is_valid": True, "quality_score": 1.0, "errors": []}
        
    def fetch_and_store_symbol(self, symbol: str, outputsize: str = 'compact') -> Dict:
        """
        Fetch and store data for a single symbol
        
        Args:
            symbol: Stock symbol to fetch
            outputsize: 'compact' (100 days) or 'full' (up to 20 years)
            
        Returns:
            Dictionary with results
        """
        result = {
            'symbol': symbol,
            'success': False,
            'records_fetched': 0,
            'records_saved': 0,
            'company_info_saved': False,
            'error': None,
            'latest_date': None
        }
        
        try:
            logger.info(f"🔄 Fetching data for {symbol}...")
            
            # Fetch stock data
            stock_data = self.alpha_vantage.get_stock_daily(symbol, outputsize)
            
            if not stock_data or 'Time Series (Daily)' not in stock_data:
                error_msg = f"No data received for {symbol}"
                logger.error(error_msg)
                result['error'] = error_msg
                self.sns_publisher.publish_error(symbol, error_msg, "data_fetch")
                return result
            
            # Get the time series data
            time_series = stock_data['Time Series (Daily)']
            dates = list(time_series.keys())
            
            if not dates:
                error_msg = f"No dates found in data for {symbol}"
                logger.error(error_msg)
                result['error'] = error_msg
                self.sns_publisher.publish_error(symbol, error_msg, "data_processing")
                return result
            
            result['records_fetched'] = len(dates)
            result['latest_date'] = dates[0]  # Most recent date
            
            # Save stock data to database
            records_saved = self.db_manager.save_stock_data(symbol, time_series)
            result['records_saved'] = records_saved
            
            # Log the fetch operation
            self.db_manager.log_fetch_operation(
                symbol=symbol,
                status='success',
                records_fetched=len(dates)
            )
            
            # Try to fetch and save company info (for stocks, not ETFs)
            if not symbol.startswith('^') and not symbol in ['SPY', 'QQQ', 'DIA', 'IWM', 'VXX']:
                company_info = self.alpha_vantage.get_stock_overview(symbol)
                if company_info and 'Name' in company_info:
                    company_saved = self.db_manager.save_company_info(symbol, company_info)
                    result['company_info_saved'] = company_saved
                    
                    if company_saved:
                        self.sns_publisher.publish_company_info_updated(
                            symbol, company_info.get('Name')
                        )
            
            # Send success event (legacy SNS)
            self.sns_publisher.publish_stock_data_loaded(
                symbol=symbol,
                records_count=records_saved,
                latest_date=result['latest_date']
            )
            
            # Send Event System notification
            try:
                # Get latest price for event
                latest_price = 0.0
                if time_series and dates:
                    latest_data = time_series[dates[0]]
                    latest_price = float(latest_data.get('4. close', 0))
                
                # Publish stock data loaded event
                publish_stock_data_loaded(symbol, records_saved, result['latest_date'], latest_price)
                logger.info(f"📡 Published stock data loaded event for {symbol}")
            except Exception as e:
                logger.error(f"❌ Error publishing event for {symbol}: {e}")
            
            result['success'] = True
            logger.info(f"✅ Successfully processed {symbol}: {records_saved} records")
            
        except Exception as e:
            error_msg = f"Error processing {symbol}: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
            
            # Log error and send error event
            self.db_manager.log_fetch_operation(
                symbol=symbol,
                status='error',
                error_message=error_msg
            )
            self.sns_publisher.publish_error(symbol, error_msg, "data_processing")
        
        return result
    
    def fetch_and_store_batch(self, symbols: List[str], outputsize: str = 'compact') -> List[Dict]:
        """
        Fetch and store data for multiple symbols
        
        Args:
            symbols: List of stock symbols
            outputsize: 'compact' or 'full'
            
        Returns:
            List of results for each symbol
        """
        results = []
        total_records = 0
        successful_symbols = []
        
        logger.info(f"🚀 Starting batch processing for {len(symbols)} symbols...")
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Processing {i}/{len(symbols)}: {symbol}")
            
            result = self.fetch_and_store_symbol(symbol, outputsize)
            results.append(result)
            
            if result['success']:
                successful_symbols.append(symbol)
                total_records += result['records_saved']
            
            # Rate limiting between symbols (premium API: 1200 calls per minute)
            if i < len(symbols):
                time.sleep(0.1)  # Premium rate limit: 0.1 seconds between calls
        
        # Send batch completion event (legacy SNS)
        if successful_symbols:
            self.sns_publisher.publish_batch_complete(successful_symbols, total_records)
        
        # Send Event System batch completion event
        try:
            publish_batch_completed(len(symbols), len(successful_symbols), total_records, successful_symbols)
            logger.info(f"📡 Published batch completed event: {len(successful_symbols)}/{len(symbols)} symbols")
        except Exception as e:
            logger.error(f"❌ Error publishing batch event: {e}")
        
        # Log summary
        successful_count = len(successful_symbols)
        logger.info(f"📊 Batch complete: {successful_count}/{len(symbols)} symbols successful")
        logger.info(f"📊 Total records processed: {total_records}")
        
        return results
    
    def fetch_all_configured_symbols(self, outputsize: str = 'compact') -> List[Dict]:
        """
        Fetch data for all symbols configured in config
        
        Args:
            outputsize: 'compact' or 'full'
            
        Returns:
            List of results for all symbols
        """
        # Use dynamic symbol loading
        if config.DYNAMIC_SYMBOL_LOADING:
            if config.SYMBOL_SOURCE == 'sectors':
                all_symbols = self.alpha_vantage.get_market_sectors()
            elif config.SYMBOL_SOURCE == 'top_gainers':
                all_symbols = self.alpha_vantage.get_top_stocks(config.TARGET_SYMBOL_COUNT)
            else:
                all_symbols = config.ALL_SYMBOLS
        else:
            all_symbols = config.ALL_SYMBOLS
        
        # Limit to target count
        target_count = config.STOCK_THRESHOLD
        all_symbols = all_symbols[:target_count]
        
        logger.info(f"🔄 Fetching data for {len(all_symbols)} symbols...")
        
        return self.fetch_and_store_batch(all_symbols, outputsize)
    
    def get_symbol_status(self, symbol: str) -> Dict:
        """
        Get status of a symbol in the database
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with symbol status
        """
        try:
            # Get stock data and filter out records with 0.0 prices
            stock_data = self.db_manager.get_stock_data(symbol, limit=10)
            valid_data = [record for record in stock_data if record.get('close_price', 0) > 0]
            
            # Get company info
            company_info = self.db_manager.get_company_info(symbol)
            
            status = {
                'symbol': symbol,
                'has_data': len(valid_data) > 0,
                'latest_date': valid_data[0]['date'].isoformat() if valid_data and 'date' in valid_data[0] else None,
                'latest_price': valid_data[0]['close_price'] if valid_data and 'close_price' in valid_data[0] else None,
                'has_company_info': company_info is not None,
                'company_name': company_info['company_name'] if company_info and 'company_name' in company_info else None,
                'total_records': len(self.db_manager.get_stock_data(symbol, limit=10000))
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting status for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e)
            }
    
    def get_system_status(self) -> Dict:
        """
        Get overall system status
        
        Returns:
            Dictionary with system status
        """
        try:
            # Test Alpha Vantage connection
            alpha_vantage_status = self.alpha_vantage.test_api_connection()
            
            # Test SNS connection
            sns_ok = self.sns_publisher.test_connection()
            
            # Get database stats with better error handling
            try:
                db_stats = self.db_manager.get_database_stats()
                logger.info(f"📊 Database stats retrieved: {db_stats}")
                
                if not db_stats:
                    logger.warning("⚠️ Database stats returned empty, checking individual collections...")
                    # Try to get individual collection counts as fallback
                    total_records = 0
                    unique_symbols = 0
                    try:
                        # Direct collection access as fallback
                        stock_prices_collection = self.db_manager.get_collection('stock_prices')
                        companies_collection = self.db_manager.get_collection('companies')
                        total_records = stock_prices_collection.count_documents({})
                        unique_symbols = companies_collection.count_documents({})
                        logger.info(f"🔧 Fallback counts - Total records: {total_records}, Unique symbols: {unique_symbols}")
                    except Exception as fallback_error:
                        logger.error(f"❌ Fallback collection count failed: {fallback_error}")
                        total_records = 0
                        unique_symbols = 0
                else:
                    total_records = db_stats.get('stock_prices', 0)
                    unique_symbols = db_stats.get('companies', 0)
                    
            except Exception as db_error:
                logger.error(f"❌ Database stats error: {db_error}")
                total_records = 0
                unique_symbols = 0
            
            # Get current symbol count
            current_symbols = config.ALL_SYMBOLS
            
            status = {
                'alpha_vantage_connection': alpha_vantage_status,
                'sns_connection': sns_ok,
                'database_records': total_records,
                'unique_symbols': unique_symbols,
                'configured_symbols': len(current_symbols),
                'symbol_source': 'default',
                'target_symbol_count': config.STOCK_THRESHOLD,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"✅ System status generated: {status}")
            return status
            
        except Exception as e:
            logger.error(f"❌ Error getting system status: {e}")
            return {
                'alpha_vantage_connection': False,
                'sns_connection': False,
                'database_records': 0,
                'unique_symbols': 0,
                'configured_symbols': len(config.ALL_SYMBOLS),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

def main():
    """Test the data service"""
    service = DataService()
    
    # Test system status
    print("🔍 Checking system status...")
    status = service.get_system_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test fetching a single symbol
    print("\n🧪 Testing single symbol fetch...")
    result = service.fetch_and_store_symbol('AAPL', outputsize='compact')
    print(f"Result: {result}")
    
    # Test getting symbol status
    print("\n📊 Getting symbol status...")
    symbol_status = service.get_symbol_status('AAPL')
    print(f"AAPL Status: {symbol_status}")

if __name__ == "__main__":
    main() 