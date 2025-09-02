from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

from app.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

router = APIRouter()

def get_market_data_service() -> MarketDataService:
    return MarketDataService()

@router.get("/correlation")
async def calculate_correlation(
    symbols: List[str] = Query(..., description="List of symbols for correlation analysis"),
    period: str = Query("1y", description="Time period for analysis"),
    service: MarketDataService = Depends(get_market_data_service)
):
    """Calculate correlation matrix between symbols"""
    try:
        if len(symbols) < 2:
            raise HTTPException(status_code=400, detail="At least 2 symbols required")
        if len(symbols) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 symbols allowed")
            
        # Fetch historical data for all symbols
        price_data = {}
        for symbol in symbols:
            data = await service.get_historical_data(symbol.upper(), period, "1d")
            if "error" not in data and "data" in data:
                prices = [item["close"] for item in data["data"]]
                dates = [item["date"] for item in data["data"]]
                price_data[symbol.upper()] = pd.Series(prices, index=pd.to_datetime(dates))
        
        if len(price_data) < 2:
            raise HTTPException(status_code=404, detail="Insufficient data for correlation analysis")
            
        # Create DataFrame and calculate returns
        df = pd.DataFrame(price_data)
        returns = df.pct_change().dropna()
        
        # Calculate correlation matrix
        correlation_matrix = returns.corr()
        
        # Convert to dictionary format
        correlation_dict = {}
        for i, symbol1 in enumerate(correlation_matrix.columns):
            correlation_dict[symbol1] = {}
            for j, symbol2 in enumerate(correlation_matrix.columns):
                correlation_dict[symbol1][symbol2] = float(correlation_matrix.iloc[i, j])
        
        return {
            "symbols": list(correlation_matrix.columns),
            "correlation_matrix": correlation_dict,
            "period": period,
            "data_points": len(returns),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/volatility/{symbol}")
async def calculate_volatility(
    symbol: str,
    period: str = Query("1y", description="Time period for analysis"),
    window: int = Query(30, description="Rolling window for volatility calculation"),
    service: MarketDataService = Depends(get_market_data_service)
):
    """Calculate historical and realized volatility"""
    try:
        data = await service.get_historical_data(symbol.upper(), period, "1d")
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
            
        prices = [item["close"] for item in data["data"]]
        dates = [item["date"] for item in data["data"]]
        
        price_series = pd.Series(prices, index=pd.to_datetime(dates))
        returns = price_series.pct_change().dropna()
        
        # Calculate various volatility measures
        daily_vol = returns.std()
        annual_vol = daily_vol * np.sqrt(252)  # Annualized volatility
        
        # Rolling volatility
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)
        
        # VaR calculations
        var_95 = returns.quantile(0.05)  # 95% VaR
        var_99 = returns.quantile(0.01)  # 99% VaR
        
        # Prepare rolling volatility data
        rolling_vol_data = []
        for date, vol in rolling_vol.dropna().items():
            rolling_vol_data.append({
                "date": date.isoformat(),
                "volatility": float(vol)
            })
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "daily_volatility": float(daily_vol),
            "annualized_volatility": float(annual_vol),
            "var_95": float(var_95),
            "var_99": float(var_99),
            "rolling_volatility": rolling_vol_data,
            "window_days": window,
            "data_points": len(returns),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating volatility for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/{symbol}")
async def calculate_performance_metrics(
    symbol: str,
    period: str = Query("1y", description="Time period for analysis"),
    benchmark: str = Query("SPY", description="Benchmark symbol for comparison"),
    service: MarketDataService = Depends(get_market_data_service)
):
    """Calculate comprehensive performance metrics"""
    try:
        # Fetch data for both symbol and benchmark
        symbol_data = await service.get_historical_data(symbol.upper(), period, "1d")
        benchmark_data = await service.get_historical_data(benchmark.upper(), period, "1d")
        
        if "error" in symbol_data or "error" in benchmark_data:
            raise HTTPException(status_code=404, detail="Error fetching data")
            
        # Convert to pandas series
        symbol_prices = pd.Series(
            [item["close"] for item in symbol_data["data"]],
            index=pd.to_datetime([item["date"] for item in symbol_data["data"]])
        )
        
        benchmark_prices = pd.Series(
            [item["close"] for item in benchmark_data["data"]],
            index=pd.to_datetime([item["date"] for item in benchmark_data["data"]])
        )
        
        # Align data
        aligned_data = pd.DataFrame({
            "symbol": symbol_prices,
            "benchmark": benchmark_prices
        }).dropna()
        
        # Calculate returns
        symbol_returns = aligned_data["symbol"].pct_change().dropna()
        benchmark_returns = aligned_data["benchmark"].pct_change().dropna()
        
        # Performance metrics
        total_return = (symbol_prices.iloc[-1] / symbol_prices.iloc[0] - 1) * 100
        benchmark_total_return = (benchmark_prices.iloc[-1] / benchmark_prices.iloc[0] - 1) * 100
        
        # Risk metrics
        volatility = symbol_returns.std() * np.sqrt(252)
        benchmark_volatility = benchmark_returns.std() * np.sqrt(252)
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        excess_returns = symbol_returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / volatility if volatility > 0 else 0
        
        # Beta calculation
        covariance = np.cov(symbol_returns, benchmark_returns)[0][1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        # Alpha calculation
        alpha = (symbol_returns.mean() * 252) - (risk_free_rate + beta * (benchmark_returns.mean() * 252 - risk_free_rate))
        
        # Maximum drawdown
        cumulative_returns = (1 + symbol_returns).cumprod()
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min()
        
        # Sortino ratio (downside deviation)
        downside_returns = symbol_returns[symbol_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = excess_returns / downside_deviation if downside_deviation > 0 else 0
        
        # Information ratio
        active_returns = symbol_returns - benchmark_returns
        tracking_error = active_returns.std() * np.sqrt(252)
        information_ratio = (active_returns.mean() * 252) / tracking_error if tracking_error > 0 else 0
        
        # Win rate
        win_rate = (symbol_returns > 0).sum() / len(symbol_returns) * 100
        
        return {
            "symbol": symbol.upper(),
            "benchmark": benchmark.upper(),
            "period": period,
            "returns": {
                "total_return_pct": float(total_return),
                "benchmark_return_pct": float(benchmark_total_return),
                "excess_return_pct": float(total_return - benchmark_total_return),
                "annualized_return_pct": float(symbol_returns.mean() * 252 * 100)
            },
            "risk_metrics": {
                "volatility_pct": float(volatility * 100),
                "benchmark_volatility_pct": float(benchmark_volatility * 100),
                "max_drawdown_pct": float(max_drawdown * 100),
                "downside_deviation_pct": float(downside_deviation * 100),
                "beta": float(beta),
                "tracking_error_pct": float(tracking_error * 100)
            },
            "risk_adjusted_metrics": {
                "sharpe_ratio": float(sharpe_ratio),
                "sortino_ratio": float(sortino_ratio),
                "information_ratio": float(information_ratio),
                "alpha_pct": float(alpha * 100)
            },
            "trading_metrics": {
                "win_rate_pct": float(win_rate),
                "total_trading_days": len(symbol_returns),
                "positive_days": int((symbol_returns > 0).sum()),
                "negative_days": int((symbol_returns < 0).sum())
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sector-analysis")
async def sector_analysis(
    service: MarketDataService = Depends(get_market_data_service)
):
    """Analyze performance by sector using sector ETFs"""
    try:
        # Major sector ETFs
        sector_etfs = {
            "XLK": "Technology",
            "XLF": "Financial", 
            "XLV": "Healthcare",
            "XLI": "Industrial",
            "XLE": "Energy",
            "XLRE": "Real Estate",
            "XLU": "Utilities",
            "XLB": "Materials",
            "XLP": "Consumer Staples",
            "XLY": "Consumer Discretionary",
            "XLC": "Communication Services"
        }
        
        sector_data = await service.get_real_time_data(list(sector_etfs.keys()))
        
        # Sort by performance
        performance_list = []
        for symbol, data in sector_data.items():
            if "error" not in data:
                performance_list.append({
                    "symbol": symbol,
                    "name": sector_etfs.get(symbol, symbol),
                    "price": data.get("price", 0),
                    "change_percent": data.get("change_percent", 0),
                    "volume": data.get("volume", 0)
                })
        
        # Sort by performance
        performance_list.sort(key=lambda x: x["change_percent"], reverse=True)
        
        return {
            "sectors": performance_list,
            "market_summary": {
                "advancing": len([s for s in performance_list if s["change_percent"] > 0]),
                "declining": len([s for s in performance_list if s["change_percent"] < 0]),
                "unchanged": len([s for s in performance_list if s["change_percent"] == 0])
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in sector analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/momentum-scan")
async def momentum_scan(
    min_volume: int = Query(1000000, description="Minimum daily volume"),
    min_price: float = Query(5.0, description="Minimum stock price"),
    service: MarketDataService = Depends(get_market_data_service)
):
    """Scan for stocks with strong momentum characteristics"""
    try:
        # Popular momentum stocks to scan
        momentum_candidates = [
            "AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN", 
            "NFLX", "CRM", "ADBE", "PYPL", "SQ", "ROKU", "ZM", "SHOP",
            "AMD", "INTC", "ORCL", "CSCO", "IBM", "MU", "QCOM", "TXN"
        ]
        
        real_time_data = await service.get_real_time_data(momentum_candidates)
        
        momentum_stocks = []
        for symbol, data in real_time_data.items():
            if "error" not in data:
                price = data.get("price", 0)
                volume = data.get("volume", 0)
                change_percent = data.get("change_percent", 0)
                
                # Apply filters
                if price >= min_price and volume >= min_volume:
                    # Get technical indicators
                    indicators = await service.get_technical_indicators(symbol, "3mo")
                    
                    if "error" not in indicators:
                        current_price = indicators.get("current_price", price)
                        indicators_data = indicators.get("indicators", {})
                        
                        # Momentum score calculation
                        momentum_score = 0
                        
                        # Price above moving averages
                        sma_20 = indicators_data.get("SMA_20")
                        sma_50 = indicators_data.get("SMA_50")
                        if sma_20 and current_price > sma_20:
                            momentum_score += 1
                        if sma_50 and current_price > sma_50:
                            momentum_score += 1
                            
                        # RSI in bullish range (50-80)
                        rsi = indicators_data.get("RSI")
                        if rsi and 50 <= rsi <= 80:
                            momentum_score += 1
                            
                        # Volume above average
                        volume_ratio = indicators_data.get("Volume_Ratio", 1)
                        if volume_ratio > 1.2:
                            momentum_score += 1
                            
                        # Strong daily performance
                        if change_percent > 1:
                            momentum_score += 1
                            
                        momentum_stocks.append({
                            "symbol": symbol,
                            "price": price,
                            "change_percent": change_percent,
                            "volume": volume,
                            "momentum_score": momentum_score,
                            "rsi": rsi,
                            "volume_ratio": volume_ratio,
                            "above_sma_20": current_price > sma_20 if sma_20 else False,
                            "above_sma_50": current_price > sma_50 if sma_50 else False
                        })
        
        # Sort by momentum score and performance
        momentum_stocks.sort(key=lambda x: (x["momentum_score"], x["change_percent"]), reverse=True)
        
        return {
            "momentum_stocks": momentum_stocks[:20],  # Top 20
            "scan_criteria": {
                "min_volume": min_volume,
                "min_price": min_price,
                "total_scanned": len(momentum_candidates),
                "passed_filter": len(momentum_stocks)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in momentum scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))