from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Market Monitor"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Real-time market data and analytics platform"
    
    # CORS
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    # Database
    DATABASE_URL: str = "sqlite:///./market_monitor.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # 5 minutes
    
    # Market Data APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    IEX_CLOUD_API_KEY: Optional[str] = None
    POLYGON_API_KEY: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    MAX_CONNECTIONS_PER_IP: int = 10
    
    # Data Settings
    DEFAULT_SYMBOLS: List[str] = [
        "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", 
        "META", "NVDA", "SPY", "QQQ", "IWM"
    ]
    
    # Technical Indicators Settings
    DEFAULT_SMA_PERIODS: List[int] = [20, 50, 200]
    DEFAULT_EMA_PERIODS: List[int] = [12, 26]
    RSI_PERIOD: int = 14
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD: float = 2.0
    
    # Risk Management
    MAX_POSITION_SIZE: float = 0.1  # 10% of portfolio
    STOP_LOSS_PERCENTAGE: float = 0.02  # 2%
    TAKE_PROFIT_PERCENTAGE: float = 0.05  # 5%
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Development
    DEBUG: bool = True
    RELOAD: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Market hours configuration
MARKET_HOURS = {
    "US": {
        "open": "09:30",
        "close": "16:00",
        "timezone": "America/New_York"
    },
    "EU": {
        "open": "08:00", 
        "close": "16:30",
        "timezone": "Europe/London"
    },
    "ASIA": {
        "open": "09:00",
        "close": "15:00", 
        "timezone": "Asia/Tokyo"
    }
}

# Supported exchanges
SUPPORTED_EXCHANGES = [
    "NYSE", "NASDAQ", "LSE", "TSE", "HKSE", 
    "Euronext", "TSX", "ASX", "BSE", "SSE"
]

# Asset classes
ASSET_CLASSES = {
    "EQUITY": "Stocks",
    "ETF": "Exchange Traded Funds",
    "INDEX": "Market Indices", 
    "FOREX": "Foreign Exchange",
    "CRYPTO": "Cryptocurrency",
    "COMMODITY": "Commodities",
    "BOND": "Fixed Income"
}

# Market data refresh intervals (seconds)
REFRESH_INTERVALS = {
    "REAL_TIME": 1,
    "FAST": 5,
    "NORMAL": 15,
    "SLOW": 60,
    "HOURLY": 3600,
    "DAILY": 86400
}