import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  CircularProgress,
  Tabs,
  Tab
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  TrendingUp,
  Assessment,
  ScatterPlot,
  Timeline
} from '@mui/icons-material';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar } from 'recharts';
import axios from 'axios';

interface TechnicalIndicators {
  symbol: string;
  current_price: number;
  indicators: Record<string, number>;
  timestamp: string;
}

interface PerformanceMetrics {
  symbol: string;
  benchmark: string;
  returns: {
    total_return_pct: number;
    benchmark_return_pct: number;
    excess_return_pct: number;
  };
  risk_metrics: {
    volatility_pct: number;
    max_drawdown_pct: number;
    beta: number;
  };
  risk_adjusted_metrics: {
    sharpe_ratio: number;
    sortino_ratio: number;
    alpha_pct: number;
  };
}

interface VolatilityData {
  symbol: string;
  annualized_volatility: number;
  var_95: number;
  var_99: number;
  rolling_volatility: Array<{
    date: string;
    volatility: number;
  }>;
}

const Analytics: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [indicators, setIndicators] = useState<TechnicalIndicators | null>(null);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [volatility, setVolatility] = useState<VolatilityData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const popularSymbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'SPY', 'QQQ'];

  useEffect(() => {
    if (selectedSymbol) {
      fetchAnalytics();
    }
  }, [selectedSymbol]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [indicatorsRes, performanceRes, volatilityRes] = await Promise.all([
        axios.get(`/api/v1/market/indicators/${selectedSymbol}`),
        axios.get(`/api/v1/analytics/performance/${selectedSymbol}?benchmark=SPY`),
        axios.get(`/api/v1/analytics/volatility/${selectedSymbol}`)
      ]);

      setIndicators(indicatorsRes.data);
      setPerformance(performanceRes.data);
      setVolatility(volatilityRes.data);
    } catch (err) {
      setError('Failed to fetch analytics data');
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getColorForValue = (value: number, threshold = 0) => {
    return value >= threshold ? 'success.main' : 'error.main';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <AnalyticsIcon />
        <Typography variant="h4">Analytics Dashboard</Typography>
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Symbol</InputLabel>
          <Select
            value={selectedSymbol}
            label="Symbol"
            onChange={(e) => setSelectedSymbol(e.target.value)}
          >
            {popularSymbols.map((symbol) => (
              <MenuItem key={symbol} value={symbol}>
                {symbol}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Button
          variant="contained"
          onClick={fetchAnalytics}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <Assessment />}
        >
          Analyze
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Tabs value={selectedTab} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Technical Indicators" icon={<Timeline />} />
        <Tab label="Performance Metrics" icon={<TrendingUp />} />
        <Tab label="Volatility Analysis" icon={<ScatterPlot />} />
      </Tabs>

      {/* Technical Indicators Tab */}
      {selectedTab === 0 && indicators && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Technical Indicators for {indicators.symbol}
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        Moving Averages
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {['SMA_20', 'SMA_50', 'SMA_200', 'EMA_12', 'EMA_26'].map((indicator) => {
                          const value = indicators.indicators[indicator];
                          if (value) {
                            const abovePrice = indicators.current_price > value;
                            return (
                              <Box key={indicator} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="body2">{indicator}:</Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="body2">${value.toFixed(2)}</Typography>
                                  <Chip
                                    label={abovePrice ? "Above" : "Below"}
                                    size="small"
                                    color={abovePrice ? "success" : "error"}
                                  />
                                </Box>
                              </Box>
                            );
                          }
                          return null;
                        })}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        Momentum Indicators
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">RSI:</Typography>
                          <Typography 
                            variant="body2" 
                            color={
                              indicators.indicators.RSI > 70 ? 'error.main' :
                              indicators.indicators.RSI < 30 ? 'success.main' : 'text.primary'
                            }
                          >
                            {indicators.indicators.RSI?.toFixed(2)}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">MACD:</Typography>
                          <Typography variant="body2">{indicators.indicators.MACD?.toFixed(4)}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">MACD Signal:</Typography>
                          <Typography variant="body2">{indicators.indicators.MACD_Signal?.toFixed(4)}</Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        Bollinger Bands & Support/Resistance
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6} md={3}>
                          <Typography variant="body2" color="error.main">
                            BB Upper: ${indicators.indicators.BB_Upper?.toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="body2">
                            BB Middle: ${indicators.indicators.BB_Middle?.toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="body2" color="success.main">
                            BB Lower: ${indicators.indicators.BB_Lower?.toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="body2">
                            Current: ${indicators.current_price?.toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="body2" color="error.main">
                            Resistance: ${indicators.indicators.Resistance_20D?.toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="body2" color="success.main">
                            Support: ${indicators.indicators.Support_20D?.toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="body2">
                            Volatility: {(indicators.indicators.Volatility_20D * 100)?.toFixed(1)}%
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="body2">
                            Volume Ratio: {indicators.indicators.Volume_Ratio?.toFixed(2)}x
                          </Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Trading Signals
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {/* RSI Signal */}
                  <Box>
                    <Typography variant="subtitle2">RSI Signal</Typography>
                    <Chip
                      label={
                        indicators.indicators.RSI > 70 ? "Overbought" :
                        indicators.indicators.RSI < 30 ? "Oversold" : "Neutral"
                      }
                      color={
                        indicators.indicators.RSI > 70 ? "error" :
                        indicators.indicators.RSI < 30 ? "success" : "default"
                      }
                    />
                  </Box>

                  {/* Moving Average Signal */}
                  <Box>
                    <Typography variant="subtitle2">MA Trend</Typography>
                    <Chip
                      label={
                        indicators.current_price > indicators.indicators.SMA_20 && 
                        indicators.current_price > indicators.indicators.SMA_50 ? "Bullish" : "Bearish"
                      }
                      color={
                        indicators.current_price > indicators.indicators.SMA_20 && 
                        indicators.current_price > indicators.indicators.SMA_50 ? "success" : "error"
                      }
                    />
                  </Box>

                  {/* Volume Signal */}
                  <Box>
                    <Typography variant="subtitle2">Volume</Typography>
                    <Chip
                      label={indicators.indicators.Volume_Ratio > 1.5 ? "High" : "Normal"}
                      color={indicators.indicators.Volume_Ratio > 1.5 ? "primary" : "default"}
                    />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Performance Metrics Tab */}
      {selectedTab === 1 && performance && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Returns Analysis
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Total Return:</Typography>
                    <Typography color={getColorForValue(performance.returns.total_return_pct)}>
                      {formatPercent(performance.returns.total_return_pct)}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Benchmark Return:</Typography>
                    <Typography color={getColorForValue(performance.returns.benchmark_return_pct)}>
                      {formatPercent(performance.returns.benchmark_return_pct)}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Excess Return:</Typography>
                    <Typography color={getColorForValue(performance.returns.excess_return_pct)}>
                      {formatPercent(performance.returns.excess_return_pct)}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Metrics
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Volatility:</Typography>
                    <Typography>{performance.risk_metrics.volatility_pct.toFixed(2)}%</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Max Drawdown:</Typography>
                    <Typography color="error.main">
                      {performance.risk_metrics.max_drawdown_pct.toFixed(2)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Beta:</Typography>
                    <Typography>{performance.risk_metrics.beta.toFixed(2)}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk-Adjusted Performance
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={4}>
                    <Box textAlign="center">
                      <Typography variant="h4" color={getColorForValue(performance.risk_adjusted_metrics.sharpe_ratio)}>
                        {performance.risk_adjusted_metrics.sharpe_ratio.toFixed(2)}
                      </Typography>
                      <Typography variant="subtitle2">Sharpe Ratio</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box textAlign="center">
                      <Typography variant="h4" color={getColorForValue(performance.risk_adjusted_metrics.sortino_ratio)}>
                        {performance.risk_adjusted_metrics.sortino_ratio.toFixed(2)}
                      </Typography>
                      <Typography variant="subtitle2">Sortino Ratio</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box textAlign="center">
                      <Typography variant="h4" color={getColorForValue(performance.risk_adjusted_metrics.alpha_pct)}>
                        {formatPercent(performance.risk_adjusted_metrics.alpha_pct)}
                      </Typography>
                      <Typography variant="subtitle2">Alpha</Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Volatility Analysis Tab */}
      {selectedTab === 2 && volatility && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Rolling Volatility Chart
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={volatility.rolling_volatility}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(date) => new Date(date).toLocaleDateString()}
                  />
                  <YAxis tickFormatter={(value) => `${(value * 100).toFixed(1)}%`} />
                  <Tooltip
                    labelFormatter={(date) => new Date(date).toLocaleDateString()}
                    formatter={(value) => [`${(value * 100).toFixed(2)}%`, 'Volatility']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="volatility" 
                    stroke="#ff4081" 
                    fill="#ff4081" 
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Volatility Metrics
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="subtitle2">Annualized Volatility</Typography>
                    <Typography variant="h5">
                      {(volatility.annualized_volatility * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2">Value at Risk (95%)</Typography>
                    <Typography variant="h6" color="error.main">
                      {(volatility.var_95 * 100).toFixed(2)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2">Value at Risk (99%)</Typography>
                    <Typography variant="h6" color="error.main">
                      {(volatility.var_99 * 100).toFixed(2)}%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Analytics;