#!/usr/bin/env python3
"""
EC2 Driver - Times Square Streaming Simulator
===========================================

This is the Times Square ticker simulator that:
- Listens for SNS events when stock data is ready
- Reads stock data from MongoDB database
- Simulates real-time streaming (1 tick per second)
- Sends ticks to the stream receiver for processing
- Provides health monitoring and status endpoints

Think of this as the "ticker display" that shows stock prices like Times Square.
"""

import asyncio
import json
import logging
import sys
import os
import aiohttp
sys.path.append('/app')
from datetime import datetime
from typing import Dict, List, Set
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mongodb_database_reader import MongoDBStockDataReader
from events.sns_event_listener import SNSEventListener
from events.event_definitions import EventType

# Create FastAPI app for health checks
app = FastAPI(title="EC2 Driver - Stream Simulator")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return JSONResponse({
        "status": "healthy",
        "service": "ec2-driver",
        "streaming": simulator.is_streaming if 'simulator' in globals() else False,
        "symbols_ready": len(simulator.ready_symbols) if 'simulator' in globals() else 0,
        "required_symbols": simulator.required_symbols if 'simulator' in globals() else 30,
        "timestamp": datetime.now().isoformat()
    })

class StreamSimulator:
    """Simulates real-time stock streaming like Times Square"""
    
    def __init__(self):
        self.db_reader = MongoDBStockDataReader()
        self.ready_symbols: Set[str] = set()
        self.required_symbols = int(os.getenv('STOCK_THRESHOLD', '30'))  # Set to 30 for production
        self.is_streaming = False
        self.tick_interval = 0.1  # 100ms between ticks
        self.sns_listener = SNSEventListener()
        self.data_quality_url = os.getenv('DATA_QUALITY_URL', 'http://localhost:8003')
    
    async def validate_stream_tick(self, tick_data: Dict) -> Dict:
        """Validate stream tick data using data quality service"""
        try:
            async with aiohttp.ClientSession() as session:
                validation_request = {
                    "data": tick_data,
                    "data_type": "stream_tick",
                    "validate_and_clean": True
                }
                
                async with session.post(
                    f"{self.data_quality_url}/api/v1/validate",
                    json=validation_request,
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "is_valid": result.get("is_acceptable", True),
                            "quality_score": result.get("quality_score", 1.0),
                            "errors": [r for r in result.get("validation_results", []) if not r.get("passed", True)]
                        }
                    else:
                        logger.warning(f"Data quality service returned {response.status}")
                        return {"is_valid": True, "quality_score": 1.0, "errors": []}
        except Exception as e:
            logger.debug(f"Data quality validation failed: {e}")
            return {"is_valid": True, "quality_score": 1.0, "errors": []}
        
    async def handle_sns_event(self, event: Dict):
        """Handle incoming SNS events"""
        try:
            event_type = event.get('type')
            
            if event_type == 'TICKER_UPDATED':
                symbol = event['symbol']
                self.ready_symbols.add(symbol)
                logger.info(f"📈 Added {symbol} to ready symbols ({len(self.ready_symbols)}/{self.required_symbols})")
                
                # Check if we have enough symbols
                if len(self.ready_symbols) >= self.required_symbols and not self.is_streaming:
                    await self.start_streaming()
                    
            elif event_type == 'DATA_THRESHOLD_REACHED':
                symbols = event['data']['symbols']
                self.ready_symbols.update(symbols)
                logger.info(f"🎯 Threshold reached with {len(symbols)} symbols")
                
                if not self.is_streaming:
                    await self.start_streaming()
                    
        except Exception as e:
            logger.error(f"❌ Error handling SNS event: {e}")
    
    async def start_streaming(self):
        """Start the streaming simulation"""
        try:
            self.is_streaming = True
            logger.info("🚀 Starting stream simulation")
            
            # Get all ticker data from MongoDB
            all_tickers = await self.db_reader.get_all_tickers()
            
            if not all_tickers:
                logger.error("❌ No ticker data found in MongoDB")
                return
            
            # Start continuous streaming
            while self.is_streaming:
                for ticker in all_tickers:
                    if not self.is_streaming:
                        break
                        
                    # Create simulated tick
                    tick = self._create_tick(ticker)
                    
                    # Send to Stream Processor (EC2 #3)
                    await self._send_to_processor(tick)
                    
                    # Wait for next tick
                    await asyncio.sleep(self.tick_interval)
                    
        except Exception as e:
            logger.error(f"❌ Error in streaming: {e}")
            self.is_streaming = False
    
    def _create_tick(self, ticker: Dict) -> Dict:
        """Create a ticker update"""
        import random
        
        # Get base price
        base_price = float(ticker['close_price'])
        
        # Simulate small price movement (-0.5% to +0.5%)
        change_percent = random.uniform(-0.005, 0.005)
        price_change = base_price * change_percent
        
        return {
            'symbol': ticker['symbol'],
            'price': base_price + price_change,
            'change': price_change,
            'volume': ticker['volume'],
            'timestamp': datetime.now().isoformat(),
            'tick_type': 'simulated'
        }
    
    async def _send_to_processor(self, tick: Dict):
        """Send tick to Stream Processor"""
        try:
            # Send to Stream Receiver via HTTP POST
            logger.info(f"📤 Sending tick: {tick['symbol']} - ${tick['price']:.2f}")
            
            # Use connection manager to send to stream receiver
            from shared.connection_manager import connection_manager
            
            # Initialize connection manager if not done
            await connection_manager.initialize()
            
            # Send tick data to stream receiver
            response = await connection_manager.send_to_instance(
                'stream_receiver', 
                'ticks', 
                tick
            )
            
            if response.get('error'):
                logger.error(f"❌ Failed to send tick to stream receiver: {response['error']}")
            else:
                logger.debug(f"✅ Tick sent successfully: {tick['symbol']}")
            
        except Exception as e:
            logger.error(f"❌ Error sending tick: {e}")
    
    def stop_streaming(self):
        """Stop the streaming simulation"""
        self.is_streaming = False
        logger.info("🛑 Streaming stopped")
    
    def get_status(self) -> Dict:
        """Get current simulator status"""
        return {
            'is_streaming': self.is_streaming,
            'ready_symbols': len(self.ready_symbols),
            'required_symbols': self.required_symbols,
            'tick_interval': self.tick_interval,
            'symbols': list(self.ready_symbols)
        }
    
    async def start_sns_listener(self):
        """Start listening to SNS events"""
        try:
            # Check if SNS is disabled for local development
            if os.getenv('DISABLE_SNS', 'false').lower() == 'true':
                logger.info("🚫 SNS disabled for local development")
                return True
            
            logger.info("🎧 Starting SNS event listener...")
            
            # Register handler for stock_data_loaded events
            self.sns_listener.register_custom_handler(EventType.STOCK_DATA_LOADED, self.handle_sns_event)
            
            # Start listening
            self.sns_listener.start_listening()
            
        except Exception as e:
            logger.error(f"❌ Error starting SNS listener: {e}")
    
    async def run(self):
        """Main run method"""
        try:
            # Start SNS listener
            await self.start_sns_listener()
            
            # Main loop - check database periodically
            while True:
                try:
                    # Check if we have enough symbols to start streaming
                    if not self.is_streaming:
                        await self.check_symbols_threshold()
                    
                    await asyncio.sleep(10)  # Check every 10 seconds
                    
                except Exception as loop_error:
                    logger.error(f"❌ Error in main loop: {loop_error}")
                    await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down...")
        except Exception as e:
            logger.error(f"❌ Error in main run loop: {e}")
    
    async def check_symbols_threshold(self):
        """Check if we have enough symbols to start streaming"""
        try:
            # Get current symbol count from database
            symbol_count = await self.db_reader.get_symbol_count()
            
            logger.info(f"🔍 Checking symbols threshold: {symbol_count}/{self.required_symbols}")
            
            if symbol_count >= self.required_symbols and not self.is_streaming:
                logger.info(f"🎯 Threshold reached! {symbol_count} symbols ready, starting streaming...")
                
                # Populate ready_symbols set with all available symbols for status display
                if not self.ready_symbols:
                    all_symbols = await self.db_reader.get_all_symbols()
                    self.ready_symbols.update(all_symbols)
                    logger.info(f"📈 Populated ready_symbols with {len(self.ready_symbols)} symbols")
                
                await self.start_streaming()
                
        except Exception as e:
            logger.error(f"❌ Error checking symbols threshold: {e}")

# Global simulator instance for health check
simulator = None

# Main execution
if __name__ == "__main__":
    import uvicorn
    
    async def main():
        global simulator
        simulator = StreamSimulator()
        
        # Start the simulator in the background
        simulator_task = asyncio.create_task(simulator.run())
        
        # Start the FastAPI server
        config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    
    asyncio.run(main())