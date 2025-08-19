#!/usr/bin/env python3
"""
Alpha Vantage API Client - Stock Data Fetcher
============================================

This file connects to Alpha Vantage API to get real-time stock data.
It handles:
- Fetching stock prices and company info
- Rate limiting (5 calls per minute)
- Error handling and retries
- Data validation and formatting

Think of this as the "data source" that gets stock prices from the internet.
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config.config_manager import config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """Client for Alpha Vantage API with rate limiting"""
    
    def __init__(self):
        self.api_key = config.ALPHA_VANTAGE_API_KEY
        self.base_url = config.ALPHA_VANTAGE_BASE_URL
        # Premium API: 1200 calls per minute = 0.05 seconds between calls
        # Using 0.05 seconds for faster response
        self.request_delay = 0.05  # Premium rate limit: 1200 calls per minute
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make API request with error handling and rate limiting"""
        self._rate_limit()
        
        try:
            logger.info(f"Making API request with params: {params}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Debug logging
            logger.info(f"API Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API Error: {data['Error Message']}")
                return None
                
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API Note: {data['Note']}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
    
    def get_stock_daily(self, symbol: str, outputsize: str = 'full') -> Optional[Dict]:
        """
        Get daily stock data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', '^GSPC')
            outputsize: 'compact' (latest 100 data points) or 'full' (up to 20 years)
        """
        # For indexes, use different function
        if symbol.startswith('^'):
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
        else:
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
        
        return self._make_request(params)
    
    def get_stock_intraday(self, symbol: str, interval: str = '1min') -> Optional[Dict]:
        """
        Get intraday stock data for a symbol
        
        Args:
            symbol: Stock symbol
            interval: '1min', '5min', '15min', '30min', '60min'
        """
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': 'full',
            'apikey': self.api_key
        }
        
        return self._make_request(params)
    
    def get_stock_overview(self, symbol: str) -> Optional[Dict]:
        """
        Get company overview for a symbol
        
        Args:
            symbol: Stock symbol
        """
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        return self._make_request(params)
    
    def get_market_status(self) -> Optional[Dict]:
        """Get current market status"""
        params = {
            'function': 'MARKET_STATUS',
            'apikey': self.api_key
        }
        
        return self._make_request(params)
    
    def get_global_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time quote with price changes
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dictionary with real-time quote data including price changes
        """
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        return self._make_request(params)
    
    def get_batch_global_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get real-time quotes for multiple symbols with optimized batching
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary with symbol as key and quote data as value
        """
        results = {}
        
        # Limit to first 20 symbols to avoid rate limiting and improve performance
        symbols_to_fetch = symbols[:20] if len(symbols) > 20 else symbols
        
        for symbol in symbols_to_fetch:
            try:
                quote_data = self.get_global_quote(symbol)
                if quote_data and 'Global Quote' in quote_data:
                    results[symbol] = quote_data['Global Quote']
                else:
                    logger.warning(f"No quote data received for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching quote for {symbol}: {e}")
            
            # Reduced rate limiting for faster response
            time.sleep(self.request_delay * 0.5)  # Half the delay for faster updates
        
        return results
    
    def test_api_connection(self) -> bool:
        """Test if API key is valid and working"""
        logger.info("Testing Alpha Vantage API connection...")
        
        try:
            test_symbol = 'AAPL'  # Use a reliable stock for testing
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': test_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for different response types
            if 'Global Quote' in data:
                quote_data = data['Global Quote']
                if quote_data and len(quote_data) > 1:  # Has actual data
                    logger.info("✅ Alpha Vantage API connection successful - Data received!")
                    return True
                else:
                    logger.warning("⚠️ Alpha Vantage API: No current data available")
                    return False  # No data means API might not be working properly
            elif 'Note' in data:
                logger.warning("⚠️ Alpha Vantage API: Rate limited")
                return False  # Rate limited means API is not fully operational
            elif 'Error Message' in data:
                logger.error(f"❌ Alpha Vantage API Error: {data['Error Message']}")
                return False
            else:
                logger.warning("⚠️ Alpha Vantage API: Unexpected response format")
                return False  # Unexpected response means API might not be working
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Alpha Vantage API connection failed - request error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Alpha Vantage API connection failed - unexpected error: {e}")
            return False

    def get_top_stocks(self, limit=30):
        """Get top gainers/losers to dynamically populate stock list"""
        try:
            params = {
                'function': 'TOP_GAINERS_LOSERS',
                'apikey': self.api_key
            }
            
            response = self._make_request(params)
            
            if response and 'top_gainers' in response:
                # Extract symbols from top gainers
                gainers = [item['ticker'] for item in response['top_gainers'][:limit//2]]
                losers = [item['ticker'] for item in response['top_losers'][:limit//2]]
                
                # Combine and remove duplicates
                all_symbols = list(set(gainers + losers))
                return all_symbols[:limit]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to get top stocks: {e}")
            return []

    def get_market_sectors(self):
        """Get stocks from different market sectors"""
        try:
            # S&P 500 sectors - major companies from each sector
            sector_stocks = {
                'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC'],
                'Finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'MA', 'V', 'BLK'],
                'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN'],
                'Consumer': ['PG', 'HD', 'KO', 'PEP', 'WMT', 'COST', 'TGT', 'SBUX', 'NKE', 'MCD'],
                'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'OXY', 'HAL']
            }
            
            # Flatten the list
            all_stocks = []
            for sector, stocks in sector_stocks.items():
                all_stocks.extend(stocks)
            
            return all_stocks
            
        except Exception as e:
            logger.error(f"❌ Failed to get sector stocks: {e}")
            return []

def main():
    """Test the Alpha Vantage client"""
    client = AlphaVantageClient()
    
    # Test API connection
    if not client.test_api_connection():
        return
    
    # Test getting data for a few symbols
    test_symbols = ['AAPL', 'SPY', 'QQQ']
    
    for symbol in test_symbols:
        logger.info(f"\nTesting data fetch for {symbol}...")
        
        # Get daily data
        daily_data = client.get_stock_daily(symbol, outputsize='compact')
        
        if daily_data and 'Time Series (Daily)' in daily_data:
            dates = list(daily_data['Time Series (Daily)'].keys())
            logger.info(f" Got {len(dates)} days of data for {symbol}")
            logger.info(f"   Latest date: {dates[0]}")
            logger.info(f"   Earliest date: {dates[-1]}")
        else:
            logger.error(f" Failed to get data for {symbol}")
        
        # Get company overview (for stocks, not indexes)
        if not symbol.startswith('^'):
            overview = client.get_stock_overview(symbol)
            if overview and 'Name' in overview:
                logger.info(f" Got company info for {symbol}: {overview['Name']}")
            else:
                logger.warning(f"⚠️  No company info for {symbol}")

if __name__ == "__main__":
    main() 