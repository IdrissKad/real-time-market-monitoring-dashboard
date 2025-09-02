from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging

from app.services.market_data_service import MarketDataService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get market data service
def get_market_data_service() -> MarketDataService:
    return MarketDataService()

@router.get("/quote/{symbol}")
async def get_quote(
    symbol: str,
    service: MarketDataService = Depends(get_market_data_service)
):
    """Get real-time quote for a single symbol"""
    try:
        data = await service.get_real_time_data([symbol.upper()])
        if symbol.upper() in data:
            return data[symbol.upper()]
        else:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quotes")
async def get_quotes(
    symbols: List[str] = Query(..., description="List of symbols to fetch"),
    service: MarketDataService = Depends(get_market_data_service)
):
    """Get real-time quotes for multiple symbols"""
    try:
        if len(symbols) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols allowed")
            
        symbols_upper = [s.upper() for s in symbols]
        data = await service.get_real_time_data(symbols_upper)
        return {
            "quotes": data,
            "count": len(data),
            "requested": symbols_upper
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    period: str = Query("1y", description="Period (1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max)"),
    interval: str = Query("1d", description="Interval (1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo)"),
    service: MarketDataService = Depends(get_market_data_service)
):
    """Get historical data for a symbol"""
    try:
        data = await service.get_historical_data(symbol.upper(), period, interval)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indicators/{symbol}")
async def get_technical_indicators(
    symbol: str,
    period: str = Query("6mo", description="Period for indicator calculation"),
    service: MarketDataService = Depends(get_market_data_service)
):
    """Get technical indicators for a symbol"""
    try:
        data = await service.get_technical_indicators(symbol.upper(), period)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overview")
async def get_market_overview(
    service: MarketDataService = Depends(get_market_data_service)
):
    """Get market overview with major indices"""
    try:
        data = await service.get_market_overview()
        return data
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company/{symbol}")
async def get_company_info(
    symbol: str,
    service: MarketDataService = Depends(get_market_data_service)
):
    """Get detailed company information"""
    try:
        data = await service.get_company_info(symbol.upper())
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_symbols(
    query: str = Query(..., min_length=1, description="Search query for symbols/companies"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """Search for symbols and companies"""
    try:
        # This is a simplified search - in production you'd want a proper search service
        # For now, return popular symbols that match the query
        popular_symbols = {
            "AAPL": "Apple Inc.",
            "GOOGL": "Alphabet Inc.",
            "MSFT": "Microsoft Corporation", 
            "TSLA": "Tesla Inc.",
            "AMZN": "Amazon.com Inc.",
            "META": "Meta Platforms Inc.",
            "NVDA": "NVIDIA Corporation",
            "SPY": "SPDR S&P 500 ETF Trust",
            "QQQ": "Invesco QQQ Trust",
            "IWM": "iShares Russell 2000 ETF",
            "BRK.B": "Berkshire Hathaway Inc.",
            "V": "Visa Inc.",
            "JNJ": "Johnson & Johnson",
            "WMT": "Walmart Inc.",
            "PG": "Procter & Gamble Co.",
            "JPM": "JPMorgan Chase & Co.",
            "UNH": "UnitedHealth Group Inc.",
            "MA": "Mastercard Inc.",
            "HD": "Home Depot Inc.",
            "DIS": "Walt Disney Co."
        }
        
        query_lower = query.lower()
        results = []
        
        for symbol, name in popular_symbols.items():
            if (query_lower in symbol.lower() or 
                query_lower in name.lower()):
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "type": "equity"
                })
                
        return {
            "query": query,
            "results": results[:limit],
            "count": len(results[:limit])
        }
        
    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watchlist")
async def get_default_watchlist(
    service: MarketDataService = Depends(get_market_data_service)
):
    """Get default watchlist with real-time data"""
    try:
        data = await service.get_real_time_data(settings.DEFAULT_SYMBOLS)
        return {
            "watchlist": data,
            "symbols": settings.DEFAULT_SYMBOLS,
            "count": len(data)
        }
    except Exception as e:
        logger.error(f"Error fetching watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))