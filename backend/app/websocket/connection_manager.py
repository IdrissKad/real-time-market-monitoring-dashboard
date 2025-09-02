from fastapi import WebSocket
from typing import Dict, List, Set
import json
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and symbol subscriptions"""
    
    def __init__(self):
        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Symbol subscriptions: symbol -> set of websockets
        self.symbol_subscriptions: Dict[str, Set[WebSocket]] = {}
        
        # Client subscriptions: websocket -> set of symbols  
        self.client_subscriptions: Dict[WebSocket, Set[str]] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_subscriptions[websocket] = set()
        self.connection_metadata[websocket] = {
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow(),
            "message_count": 0
        }
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection and cleanup subscriptions"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        # Remove from all symbol subscriptions
        if websocket in self.client_subscriptions:
            symbols = self.client_subscriptions[websocket].copy()
            for symbol in symbols:
                self._unsubscribe_symbol(websocket, symbol)
            del self.client_subscriptions[websocket]
            
        # Cleanup metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
            
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def subscribe_symbols(self, websocket: WebSocket, symbols: List[str]):
        """Subscribe websocket to list of symbols"""
        for symbol in symbols:
            symbol = symbol.upper()
            self._subscribe_symbol(websocket, symbol)
        
        await self.send_personal_message(websocket, {
            "type": "subscription_confirmed",
            "symbols": symbols,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def unsubscribe_symbols(self, websocket: WebSocket, symbols: List[str]):
        """Unsubscribe websocket from list of symbols"""
        for symbol in symbols:
            symbol = symbol.upper()
            self._unsubscribe_symbol(websocket, symbol)
            
        await self.send_personal_message(websocket, {
            "type": "unsubscription_confirmed", 
            "symbols": symbols,
            "timestamp": datetime.utcnow().isoformat()
        })

    def _subscribe_symbol(self, websocket: WebSocket, symbol: str):
        """Internal method to subscribe websocket to symbol"""
        if symbol not in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol] = set()
        
        self.symbol_subscriptions[symbol].add(websocket)
        self.client_subscriptions[websocket].add(symbol)

    def _unsubscribe_symbol(self, websocket: WebSocket, symbol: str):
        """Internal method to unsubscribe websocket from symbol"""
        if symbol in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol].discard(websocket)
            # Remove empty symbol subscription
            if not self.symbol_subscriptions[symbol]:
                del self.symbol_subscriptions[symbol]
                
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket].discard(symbol)

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to specific websocket"""
        try:
            if websocket in self.active_connections:
                await websocket.send_text(json.dumps(message))
                self._update_connection_stats(websocket)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected websockets"""
        if self.active_connections:
            message_str = json.dumps(message)
            disconnected = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                    self._update_connection_stats(connection)
                except Exception as e:
                    logger.error(f"Error broadcasting to connection: {e}")
                    disconnected.append(connection)
            
            # Cleanup disconnected connections
            for connection in disconnected:
                self.disconnect(connection)

    async def broadcast_to_symbol_subscribers(self, symbol: str, message: dict):
        """Broadcast message to all websockets subscribed to specific symbol"""
        symbol = symbol.upper()
        if symbol in self.symbol_subscriptions:
            subscribers = list(self.symbol_subscriptions[symbol])
            message_str = json.dumps(message)
            disconnected = []
            
            for websocket in subscribers:
                try:
                    await websocket.send_text(message_str)
                    self._update_connection_stats(websocket)
                except Exception as e:
                    logger.error(f"Error sending to symbol subscriber: {e}")
                    disconnected.append(websocket)
            
            # Cleanup disconnected connections
            for websocket in disconnected:
                self.disconnect(websocket)

    def get_active_symbols(self) -> List[str]:
        """Get list of all symbols that have active subscriptions"""
        return list(self.symbol_subscriptions.keys())

    def get_symbol_subscriber_count(self, symbol: str) -> int:
        """Get number of subscribers for a specific symbol"""
        symbol = symbol.upper()
        return len(self.symbol_subscriptions.get(symbol, set()))

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)

    def get_client_subscriptions(self, websocket: WebSocket) -> List[str]:
        """Get list of symbols client is subscribed to"""
        return list(self.client_subscriptions.get(websocket, set()))

    def get_stats(self) -> dict:
        """Get comprehensive connection and subscription statistics"""
        return {
            "total_connections": len(self.active_connections),
            "active_symbols": len(self.symbol_subscriptions),
            "symbol_details": {
                symbol: len(subscribers) 
                for symbol, subscribers in self.symbol_subscriptions.items()
            },
            "connection_details": [
                {
                    "subscribed_symbols": len(symbols),
                    "connected_duration": (datetime.utcnow() - self.connection_metadata[ws]["connected_at"]).total_seconds(),
                    "message_count": self.connection_metadata[ws]["message_count"]
                }
                for ws, symbols in self.client_subscriptions.items()
                if ws in self.connection_metadata
            ]
        }

    def _update_connection_stats(self, websocket: WebSocket):
        """Update connection statistics"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["last_ping"] = datetime.utcnow()
            self.connection_metadata[websocket]["message_count"] += 1

    async def heartbeat(self):
        """Send heartbeat to all connections to keep them alive"""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat(),
            "server_status": "online"
        }
        await self.broadcast(heartbeat_message)