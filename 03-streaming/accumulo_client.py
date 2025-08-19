#!/usr/bin/env python3
"""
Simulated Accumulo Client - In-Memory Data Buffer
================================================

This file simulates Accumulo database operations for streaming data.
It handles:
- Storing real-time stock ticks in memory
- Data indexing and retrieval
- Stream processing operations
- Data persistence and cleanup

Think of this as a "moving buffer" that holds streaming data temporarily.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulatedAccumuloClient:
    """Simulated Accumulo client that doesn't crash the instance"""
    
    def __init__(self):
        self.data = {}
        self.is_connected = True
        self.table_name = "stock_ticks"
        logger.info("✅ Connected to Simulated Accumulo")
    
    def connect(self) -> bool:
        """Simulate connection (always succeeds)"""
        self.is_connected = True
        logger.info("✅ Connected to Simulated Accumulo")
        return True
    
    def disconnect(self):
        """Simulate disconnection"""
        self.is_connected = False
        logger.info("🔌 Disconnected from Simulated Accumulo")
    
    def write_stock_tick(self, tick_data: Dict) -> bool:
        """Write stock tick to simulated storage"""
        if not self.is_connected:
            logger.error("❌ Not connected to Accumulo")
            return False
            
        try:
            timestamp = tick_data.get('timestamp', datetime.now().isoformat())
            symbol = tick_data.get('symbol', 'UNKNOWN')
            tick_number = tick_data.get('tick_number', 0)
            
            # Create row key: timestamp_symbol_ticknumber
            row_key = f"{timestamp}_{symbol}_{tick_number:06d}"
            
            # Store in simulated data
            self.data[row_key] = {
                'symbol': symbol,
                'price': tick_data.get('price', 0.0),
                'volume': tick_data.get('volume', 0),
                'timestamp': timestamp,
                'tick_number': tick_number,
                'price_change': tick_data.get('price_change', 0.0),
                'current_price': tick_data.get('current_price', 0.0),
                'stream_type': tick_data.get('stream_type', 'times_square_simulation')
            }
            
            logger.info(f"📝 Written tick: {symbol} at {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to write tick: {e}")
            return False
    
    def read_stock_ticks(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """Read stock ticks from simulated storage"""
        if not self.is_connected:
            logger.error("❌ Not connected to Accumulo")
            return []
            
        try:
            if symbol:
                # Filter by symbol
                filtered_data = [v for v in self.data.values() if v.get('symbol') == symbol]
                return filtered_data[-limit:] if limit else filtered_data
            else:
                # Return all data
                return list(self.data.values())[-limit:] if limit else list(self.data.values())
        except Exception as e:
            logger.error(f"❌ Failed to read ticks: {e}")
            return []
    
    def get_status(self) -> Dict:
        """Get simulated system status"""
        return {
            "status": "running",
            "instance": "simulated-stockdata",
            "table": self.table_name,
            "records": len(self.data),
            "connected": self.is_connected
        }
    
    def create_table(self, table_name: str) -> bool:
        """Simulate table creation"""
        logger.info(f"📋 Created table: {table_name}")
        return True
    
    def table_exists(self, table_name: str) -> bool:
        """Simulate table existence check"""
        return True
    
    def get_active_symbols(self) -> List[str]:
        """Get list of active symbols that have tick data"""
        try:
            symbols = set()
            for tick in self.data.values():
                symbols.add(tick.get('symbol', 'UNKNOWN'))
            return list(symbols)
        except Exception as e:
            logger.error(f"❌ Failed to get active symbols: {e}")
            return []
    
    def get_recent_ticks(self, limit: int = 10) -> List[Dict]:
        """Get the most recent ticks across all symbols"""
        try:
            # Sort by timestamp (newest first)
            sorted_ticks = sorted(
                self.data.values(),
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )
            return sorted_ticks[:limit]
        except Exception as e:
            logger.error(f"❌ Failed to get recent ticks: {e}")
            return []

# Test the client
if __name__ == "__main__":
    client = SimulatedAccumuloClient()
    
    # Test with sample data
    test_tick = {
        "symbol": "AAPL",
        "price": 150.25,
        "volume": 1000,
        "timestamp": datetime.now().isoformat(),
        "tick_number": 1,
        "price_change": 0.50,
        "current_price": 150.75,
        "stream_type": "times_square_simulation"
    }
    
    # Test write
    success = client.write_stock_tick(test_tick)
    print(f"Write test: {'✅ Success' if success else '❌ Failed'}")
    
    # Test read
    ticks = client.read_stock_ticks()
    print(f"Read test: Found {len(ticks)} ticks")
    
    # Test status
    status = client.get_status()
    print(f"Status: {status}")
    
    print("🎯 Simulated Accumulo Client is ready for Phase 3!") 