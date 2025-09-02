import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
import ta
from app.core.config import settings

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for fetching and processing market data from multiple sources"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.last_update: Dict[str, datetime] = {}
        
    async def initialize(self):
        """Initialize the service"""
        self.session = aiohttp.ClientSession()
        logger.info("Market Data Service initialized")
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            
    async def health_check(self) -> dict:
        """Check service health"""
        try:
            # Test with a simple Yahoo Finance call
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            return {
                "status": "healthy",
                "last_check": datetime.utcnow().isoformat(),
                "test_symbol": "AAPL",
                "test_result": "success" if info else "failed"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }

    async def get_real_time_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time market data for symbols"""
        result = {}
        
        for symbol in symbols:
            try:
                # Use yfinance for real-time data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d", interval="1m")
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    info = ticker.info
                    
                    result[symbol] = {
                        "symbol": symbol,
                        "price": float(latest["Close"]),
                        "open": float(latest["Open"]),
                        "high": float(latest["High"]),
                        "low": float(latest["Low"]),
                        "volume": int(latest["Volume"]),
                        "change": float(latest["Close"] - latest["Open"]),
                        "change_percent": float(((latest["Close"] - latest["Open"]) / latest["Open"]) * 100),
                        "timestamp": datetime.utcnow().isoformat(),
                        "market_cap": info.get("marketCap"),
                        "pe_ratio": info.get("trailingPE"),
                        "52_week_high": info.get("fiftyTwoWeekHigh"),
                        "52_week_low": info.get("fiftyTwoWeekLow"),
                        "avg_volume": info.get("averageVolume")
                    }
                    
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                result[symbol] = {
                    "symbol": symbol,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        return result

    async def get_historical_data(
        self, 
        symbol: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> Dict:
        """Get historical data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return {"error": f"No data found for {symbol}"}
                
            # Convert to list of dictionaries for JSON serialization
            data = []
            for index, row in hist.iterrows():
                data.append({
                    "date": index.isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]), 
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })
                
            return {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": data,
                "count": len(data)
            }
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return {"error": str(e)}

    async def get_technical_indicators(
        self, 
        symbol: str, 
        period: str = "6mo"
    ) -> Dict:
        """Calculate technical indicators for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {"error": f"No data found for {symbol}"}
                
            # Calculate various technical indicators
            indicators = {}
            
            # Simple Moving Averages
            for period_days in settings.DEFAULT_SMA_PERIODS:
                indicators[f"SMA_{period_days}"] = ta.trend.sma_indicator(
                    hist["Close"], window=period_days
                ).iloc[-1]
                
            # Exponential Moving Averages  
            for period_days in settings.DEFAULT_EMA_PERIODS:
                indicators[f"EMA_{period_days}"] = ta.trend.ema_indicator(
                    hist["Close"], window=period_days
                ).iloc[-1]
                
            # RSI
            indicators["RSI"] = ta.momentum.rsi(
                hist["Close"], window=settings.RSI_PERIOD
            ).iloc[-1]
            
            # MACD
            macd_line = ta.trend.macd(hist["Close"])
            macd_signal = ta.trend.macd_signal(hist["Close"])
            macd_histogram = ta.trend.macd_diff(hist["Close"])
            
            indicators["MACD"] = macd_line.iloc[-1]
            indicators["MACD_Signal"] = macd_signal.iloc[-1]
            indicators["MACD_Histogram"] = macd_histogram.iloc[-1]
            
            # Bollinger Bands
            bb_upper = ta.volatility.bollinger_hband(
                hist["Close"], 
                window=settings.BOLLINGER_PERIOD, 
                window_dev=settings.BOLLINGER_STD
            )
            bb_lower = ta.volatility.bollinger_lband(
                hist["Close"], 
                window=settings.BOLLINGER_PERIOD,
                window_dev=settings.BOLLINGER_STD
            )
            bb_middle = ta.volatility.bollinger_mavg(
                hist["Close"], window=settings.BOLLINGER_PERIOD
            )
            
            indicators["BB_Upper"] = bb_upper.iloc[-1]
            indicators["BB_Lower"] = bb_lower.iloc[-1]
            indicators["BB_Middle"] = bb_middle.iloc[-1]
            
            # Volume indicators
            indicators["Volume_SMA_20"] = hist["Volume"].rolling(window=20).mean().iloc[-1]
            indicators["Volume_Ratio"] = hist["Volume"].iloc[-1] / indicators["Volume_SMA_20"]
            
            # Volatility
            indicators["Volatility_20D"] = hist["Close"].pct_change().rolling(window=20).std().iloc[-1] * np.sqrt(252)
            
            # Support and Resistance levels
            high_20 = hist["High"].rolling(window=20).max().iloc[-1]
            low_20 = hist["Low"].rolling(window=20).min().iloc[-1]
            indicators["Resistance_20D"] = high_20
            indicators["Support_20D"] = low_20
            
            return {
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat(),
                "current_price": float(hist["Close"].iloc[-1]),
                "indicators": {k: float(v) if pd.notna(v) else None for k, v in indicators.items()}
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return {"error": str(e)}

    async def get_market_overview(self) -> Dict:
        """Get market overview with major indices and market sentiment"""
        indices = ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"]
        overview = {}
        
        for index in indices:
            try:
                ticker = yf.Ticker(index)
                hist = ticker.history(period="2d")
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    previous = hist.iloc[-2] if len(hist) > 1 else latest
                    
                    overview[index] = {
                        "name": self._get_index_name(index),
                        "value": float(latest["Close"]),
                        "change": float(latest["Close"] - previous["Close"]),
                        "change_percent": float(((latest["Close"] - previous["Close"]) / previous["Close"]) * 100),
                        "volume": int(latest["Volume"]) if not pd.isna(latest["Volume"]) else 0
                    }
            except Exception as e:
                logger.error(f"Error fetching data for {index}: {e}")
                
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "indices": overview,
            "market_status": await self._get_market_status()
        }

    def _get_index_name(self, symbol: str) -> str:
        """Get human readable name for index symbol"""
        names = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "NASDAQ",
            "^RUT": "Russell 2000", 
            "^VIX": "VIX"
        }
        return names.get(symbol, symbol)

    async def _get_market_status(self) -> str:
        """Determine if market is open or closed"""
        from datetime import datetime, time
        import pytz
        
        # US market hours (9:30 AM - 4:00 PM ET)
        et = pytz.timezone('US/Eastern')
        now = datetime.now(et)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return "closed"
            
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now.time()
        
        if market_open <= current_time <= market_close:
            return "open"
        else:
            return "closed"

    async def get_company_info(self, symbol: str) -> Dict:
        """Get detailed company information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "description": info.get("longBusinessSummary", "N/A"),
                "website": info.get("website", "N/A"),
                "employees": info.get("fullTimeEmployees", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "enterprise_value": info.get("enterpriseValue", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "peg_ratio": info.get("pegRatio", "N/A"),
                "price_to_book": info.get("priceToBook", "N/A"),
                "debt_to_equity": info.get("debtToEquity", "N/A"),
                "roe": info.get("returnOnEquity", "N/A"),
                "roa": info.get("returnOnAssets", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "beta": info.get("beta", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52_week_low": info.get("fiftyTwoWeekLow", "N/A")
            }
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {e}")
            return {"error": str(e)}