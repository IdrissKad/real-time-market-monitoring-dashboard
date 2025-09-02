from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
from datetime import datetime
from typing import List

from app.api.endpoints import market_data, analytics, portfolio
from app.websocket.connection_manager import ConnectionManager
from app.services.market_data_service import MarketDataService
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Market Monitor API",
    description="Real-time market data and analytics platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize connection manager and market data service
manager = ConnectionManager()
market_service = MarketDataService()

# Include API routers
app.include_router(market_data.router, prefix="/api/v1/market", tags=["market"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Market Monitor API")
    await market_service.initialize()
    # Start background task for real-time data streaming
    asyncio.create_task(stream_market_data())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Market Monitor API")
    await market_service.cleanup()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Market Monitor API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.websocket("/ws/market-data")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time market data"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe":
                symbols = message.get("symbols", [])
                await manager.subscribe_symbols(websocket, symbols)
                logger.info(f"Client subscribed to symbols: {symbols}")
            elif message.get("type") == "unsubscribe":
                symbols = message.get("symbols", [])
                await manager.unsubscribe_symbols(websocket, symbols)
                logger.info(f"Client unsubscribed from symbols: {symbols}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")

async def stream_market_data():
    """Background task to stream real-time market data"""
    logger.info("Starting market data streaming task")
    
    while True:
        try:
            # Get active symbols from all connected clients
            active_symbols = manager.get_active_symbols()
            
            if active_symbols:
                # Fetch real-time data for active symbols
                market_data = await market_service.get_real_time_data(active_symbols)
                
                # Broadcast to all subscribed clients
                for symbol, data in market_data.items():
                    await manager.broadcast_to_symbol_subscribers(symbol, {
                        "type": "market_data",
                        "symbol": symbol,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Wait before next update (1 second for real-time feel)
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in market data streaming: {e}")
            await asyncio.sleep(5)  # Wait longer on error

@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    return {
        "status": "healthy",
        "services": {
            "market_data": await market_service.health_check(),
            "websocket_connections": manager.get_connection_count(),
            "active_symbols": len(manager.get_active_symbols())
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )