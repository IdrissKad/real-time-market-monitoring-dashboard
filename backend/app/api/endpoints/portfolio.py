from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from app.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

router = APIRouter()

class Position(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    shares: float = Field(..., description="Number of shares")
    avg_cost: float = Field(..., description="Average cost basis per share")

class Portfolio(BaseModel):
    name: str = Field(..., description="Portfolio name")
    positions: List[Position] = Field(..., description="List of positions")
    cash: float = Field(default=0.0, description="Cash position")

def get_market_data_service() -> MarketDataService:
    return MarketDataService()

@router.post("/analyze")
async def analyze_portfolio(
    portfolio: Portfolio,
    benchmark: str = "SPY",
    service: MarketDataService = Depends(get_market_data_service)
):
    """Comprehensive portfolio analysis"""
    try:
        if not portfolio.positions:
            raise HTTPException(status_code=400, detail="Portfolio must have at least one position")
        
        symbols = [pos.symbol.upper() for pos in portfolio.positions]
        
        # Get current market data
        market_data = await service.get_real_time_data(symbols)
        
        # Calculate portfolio metrics
        total_value = portfolio.cash
        total_cost = portfolio.cash
        positions_data = []
        
        for position in portfolio.positions:
            symbol = position.symbol.upper()
            if symbol in market_data and "error" not in market_data[symbol]:
                current_price = market_data[symbol]["price"]
                market_value = position.shares * current_price
                cost_basis = position.shares * position.avg_cost
                
                total_value += market_value
                total_cost += cost_basis
                
                unrealized_pnl = market_value - cost_basis
                unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                
                positions_data.append({
                    "symbol": symbol,
                    "shares": position.shares,
                    "avg_cost": position.avg_cost,
                    "current_price": current_price,
                    "market_value": market_value,
                    "cost_basis": cost_basis,
                    "unrealized_pnl": unrealized_pnl,
                    "unrealized_pnl_pct": unrealized_pnl_pct,
                    "weight": (market_value / total_value) * 100 if total_value > 0 else 0,
                    "day_change": market_data[symbol].get("change", 0),
                    "day_change_pct": market_data[symbol].get("change_percent", 0)
                })
        
        # Portfolio level metrics
        total_unrealized_pnl = sum(pos["unrealized_pnl"] for pos in positions_data)
        total_unrealized_pnl_pct = (total_unrealized_pnl / (total_cost - portfolio.cash)) * 100 if (total_cost - portfolio.cash) > 0 else 0
        
        # Daily P&L
        daily_pnl = sum(pos["shares"] * pos["day_change"] for pos in positions_data)
        daily_pnl_pct = (daily_pnl / total_value) * 100 if total_value > 0 else 0
        
        # Sector allocation (simplified)
        sector_allocation = await _calculate_sector_allocation(symbols, service)
        
        return {
            "portfolio_name": portfolio.name,
            "summary": {
                "total_value": total_value,
                "total_cost": total_cost,
                "cash": portfolio.cash,
                "total_unrealized_pnl": total_unrealized_pnl,
                "total_unrealized_pnl_pct": total_unrealized_pnl_pct,
                "daily_pnl": daily_pnl,
                "daily_pnl_pct": daily_pnl_pct,
                "number_of_positions": len(positions_data)
            },
            "positions": positions_data,
            "sector_allocation": sector_allocation,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/risk-analysis")
async def portfolio_risk_analysis(
    portfolio: Portfolio,
    period: str = "1y",
    service: MarketDataService = Depends(get_market_data_service)
):
    """Calculate portfolio risk metrics"""
    try:
        if not portfolio.positions:
            raise HTTPException(status_code=400, detail="Portfolio must have at least one position")
            
        symbols = [pos.symbol.upper() for pos in portfolio.positions]
        weights = []
        
        # Get current prices to calculate weights
        market_data = await service.get_real_time_data(symbols)
        total_value = portfolio.cash
        
        for position in portfolio.positions:
            symbol = position.symbol.upper()
            if symbol in market_data and "error" not in market_data[symbol]:
                market_value = position.shares * market_data[symbol]["price"]
                total_value += market_value
        
        # Calculate position weights
        for position in portfolio.positions:
            symbol = position.symbol.upper()
            if symbol in market_data and "error" not in market_data[symbol]:
                market_value = position.shares * market_data[symbol]["price"]
                weight = market_value / total_value if total_value > 0 else 0
                weights.append(weight)
            else:
                weights.append(0)
        
        # Get historical data for risk calculations
        returns_data = {}
        for symbol in symbols:
            hist_data = await service.get_historical_data(symbol, period, "1d")
            if "error" not in hist_data and "data" in hist_data:
                prices = [item["close"] for item in hist_data["data"]]
                dates = [item["date"] for item in hist_data["data"]]
                price_series = pd.Series(prices, index=pd.to_datetime(dates))
                returns_data[symbol] = price_series.pct_change().dropna()
        
        if not returns_data:
            raise HTTPException(status_code=404, detail="Insufficient historical data")
            
        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_data)
        
        # Calculate portfolio returns
        weights_array = np.array(weights[:len(returns_df.columns)])
        portfolio_returns = returns_df.dot(weights_array)
        
        # Risk metrics
        portfolio_volatility = portfolio_returns.std() * np.sqrt(252)
        portfolio_var_95 = portfolio_returns.quantile(0.05)
        portfolio_var_99 = portfolio_returns.quantile(0.01)
        
        # Expected shortfall (Conditional VaR)
        es_95 = portfolio_returns[portfolio_returns <= portfolio_var_95].mean()
        es_99 = portfolio_returns[portfolio_returns <= portfolio_var_99].mean()
        
        # Maximum drawdown
        cumulative_returns = (1 + portfolio_returns).cumprod()
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min()
        
        # Correlation matrix
        correlation_matrix = returns_df.corr()
        
        # Diversification ratio
        weighted_avg_vol = sum(returns_df[symbol].std() * weight for symbol, weight in zip(symbols, weights))
        diversification_ratio = weighted_avg_vol / portfolio_volatility if portfolio_volatility > 0 else 0
        
        return {
            "portfolio_name": portfolio.name,
            "period": period,
            "risk_metrics": {
                "portfolio_volatility_annual": float(portfolio_volatility),
                "var_95_daily": float(portfolio_var_95),
                "var_99_daily": float(portfolio_var_99),
                "expected_shortfall_95": float(es_95),
                "expected_shortfall_99": float(es_99),
                "max_drawdown": float(max_drawdown),
                "diversification_ratio": float(diversification_ratio)
            },
            "position_weights": dict(zip(symbols, weights)),
            "correlation_matrix": correlation_matrix.to_dict(),
            "total_positions": len(symbols),
            "analysis_period_days": len(portfolio_returns),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in portfolio risk analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimization")
async def portfolio_optimization(
    symbols: List[str],
    period: str = "1y",
    target_return: Optional[float] = None,
    risk_free_rate: float = 0.02,
    service: MarketDataService = Depends(get_market_data_service)
):
    """Modern Portfolio Theory optimization (simplified)"""
    try:
        if len(symbols) < 2:
            raise HTTPException(status_code=400, detail="At least 2 symbols required for optimization")
            
        symbols = [s.upper() for s in symbols]
        
        # Get historical data
        returns_data = {}
        for symbol in symbols:
            hist_data = await service.get_historical_data(symbol, period, "1d")
            if "error" not in hist_data and "data" in hist_data:
                prices = [item["close"] for item in hist_data["data"]]
                dates = [item["date"] for item in hist_data["data"]]
                price_series = pd.Series(prices, index=pd.to_datetime(dates))
                returns_data[symbol] = price_series.pct_change().dropna()
        
        if len(returns_data) < 2:
            raise HTTPException(status_code=404, detail="Insufficient data for optimization")
            
        returns_df = pd.DataFrame(returns_data)
        
        # Calculate expected returns and covariance matrix
        expected_returns = returns_df.mean() * 252  # Annualized
        cov_matrix = returns_df.cov() * 252  # Annualized
        
        # Simple equal weight allocation (in production, use cvxpy for proper optimization)
        num_assets = len(symbols)
        equal_weights = np.array([1/num_assets] * num_assets)
        
        # Calculate portfolio metrics for equal weight
        portfolio_return = np.dot(equal_weights, expected_returns)
        portfolio_volatility = np.sqrt(np.dot(equal_weights.T, np.dot(cov_matrix, equal_weights)))
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
        
        # Risk contribution
        marginal_contrib = np.dot(cov_matrix, equal_weights)
        risk_contrib = equal_weights * marginal_contrib / (portfolio_volatility ** 2)
        
        return {
            "optimization_type": "Equal Weight (Simplified)",
            "symbols": symbols,
            "period": period,
            "optimal_weights": dict(zip(symbols, equal_weights.tolist())),
            "expected_return": float(portfolio_return),
            "expected_volatility": float(portfolio_volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "risk_contribution": dict(zip(symbols, risk_contrib.tolist())),
            "individual_returns": expected_returns.to_dict(),
            "note": "This is a simplified equal-weight allocation. Full optimization requires advanced libraries.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in portfolio optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _calculate_sector_allocation(symbols: List[str], service: MarketDataService) -> Dict:
    """Calculate sector allocation for portfolio"""
    sector_mapping = {
        # Technology
        "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", 
        "NVDA": "Technology", "META": "Technology", "ADBE": "Technology",
        
        # Financial
        "JPM": "Financial", "BAC": "Financial", "WFC": "Financial",
        "C": "Financial", "GS": "Financial",
        
        # Healthcare
        "JNJ": "Healthcare", "PFE": "Healthcare", "UNH": "Healthcare",
        "ABBV": "Healthcare", "MRK": "Healthcare",
        
        # Consumer
        "AMZN": "Consumer Discretionary", "TSLA": "Consumer Discretionary",
        "HD": "Consumer Discretionary", "MCD": "Consumer Discretionary",
        "PG": "Consumer Staples", "KO": "Consumer Staples",
        
        # Industrial
        "BA": "Industrial", "CAT": "Industrial", "GE": "Industrial",
        
        # Energy
        "XOM": "Energy", "CVX": "Energy",
        
        # ETFs
        "SPY": "ETF", "QQQ": "ETF", "IWM": "ETF"
    }
    
    sector_counts = {}
    for symbol in symbols:
        sector = sector_mapping.get(symbol, "Other")
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
    
    total = len(symbols)
    return {
        sector: (count / total) * 100 
        for sector, count in sector_counts.items()
    }