#!/usr/bin/env python3
"""
Connection Manager for EC2 Instances
Handles HTTP and WebSocket connections between instances
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
import websockets

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages connections between EC2 instances"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket_clients: List[websockets.WebSocketServerProtocol] = []
        self.instance_urls = {
            'api_server': 'http://localhost:8000',
            'driver': 'http://localhost:8001',
            'stream_receiver': 'http://localhost:8002'
        }
        
    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        logger.info("✅ Connection manager initialized")
    
    async def close(self):
        """Close all connections"""
        if self.session:
            await self.session.close()
        logger.info("🔌 Connection manager closed")
    
    async def send_to_instance(self, instance: str, endpoint: str, data: Dict) -> Dict:
        """Send HTTP request to an instance"""
        if not self.session:
            await self.initialize()
            
        url = f"{self.instance_urls[instance]}/{endpoint}"
        try:
            async with self.session.post(url, json=data) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"❌ Error sending to {instance}: {e}")
            return {'error': str(e)}
    
    async def register_websocket(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new WebSocket client"""
        self.websocket_clients.append(websocket)
        logger.info(f"📡 New WebSocket client registered (Total: {len(self.websocket_clients)})")
    
    async def unregister_websocket(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a WebSocket client"""
        if websocket in self.websocket_clients:
            self.websocket_clients.remove(websocket)
            logger.info(f"🔌 WebSocket client unregistered (Total: {len(self.websocket_clients)})")
    
    async def broadcast_to_websockets(self, data: Dict):
        """Broadcast data to all WebSocket clients"""
        if not self.websocket_clients:
            return
            
        message = json.dumps(data)
        disconnected = []
        
        for websocket in self.websocket_clients:
            try:
                await websocket.send(message)
            except Exception as e:
                logger.error(f"❌ Error broadcasting to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            await self.unregister_websocket(websocket)
    
    async def check_instance_health(self, instance: str) -> bool:
        """Check if an instance is healthy"""
        if not self.session:
            await self.initialize()
            
        try:
            url = f"{self.instance_urls[instance]}/health"
            async with self.session.get(url) as response:
                data = await response.json()
                return data.get('status') == 'healthy'
        except Exception as e:
            logger.error(f"❌ Health check failed for {instance}: {e}")
            return False

# Global connection manager instance
connection_manager = ConnectionManager()

def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    return connection_manager