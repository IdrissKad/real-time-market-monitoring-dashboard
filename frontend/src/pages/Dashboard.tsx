import React, { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Alert,
  Skeleton
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh,
  Add,
  Remove,
  Timeline
} from '@mui/icons-material';

import { useMarketData } from '../contexts/MarketDataContext';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import axios from 'axios';

interface MarketOverview {
  indices: Record<string, {
    name: string;
    value: number;
    change: number;
    change_percent: number;
    volume: number;
  }>;
  market_status: string;
  timestamp: string;
}

const Dashboard: React.FC = () => {
  const { marketData, watchlist, connectionStatus, isConnected, addToWatchlist, removeFromWatchlist } = useMarketData();
  const [marketOverview, setMarketOverview] = useState<MarketOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMarketOverview();
    const interval = setInterval(fetchMarketOverview, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMarketOverview = async () => {
    try {
      const response = await axios.get('/api/v1/market/overview');
      setMarketOverview(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch market overview');
      console.error('Error fetching market overview:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatChange = (change: number, changePercent: number) => {
    const isPositive = change >= 0;
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        {isPositive ? <TrendingUp sx={{ fontSize: 16 }} color="success" /> : <TrendingDown sx={{ fontSize: 16 }} color="error" />}
        <Typography variant="body2" color={isPositive ? 'success.main' : 'error.main'}>
          {isPositive ? '+' : ''}{change.toFixed(2)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
        </Typography>
      </Box>
    );
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'success';
      case 'connecting': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box>
        <Skeleton variant="rectangular" width="100%" height={200} sx={{ mb: 2 }} />
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={12} md={3} key={i}>
              <Skeleton variant="rectangular" width="100%" height={150} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box>
      {/* Connection Status & Market Status */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Chip
            label={`WebSocket: ${connectionStatus}`}
            color={getConnectionStatusColor()}
            size="small"
            icon={<Timeline />}
          />
          {marketOverview && (
            <Chip
              label={`Market: ${marketOverview.market_status.toUpperCase()}`}
              color={marketOverview.market_status === 'open' ? 'success' : 'default'}
              size="small"
            />
          )}
        </Box>
        <IconButton onClick={fetchMarketOverview} size="small">
          <Refresh />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Major Indices */}
      {marketOverview && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {Object.entries(marketOverview.indices).map(([symbol, data]) => (
            <Grid item xs={12} sm={6} md={2.4} key={symbol}>
              <Card>
                <CardContent sx={{ pb: 2 }}>
                  <Typography variant="h6" component="div" gutterBottom>
                    {data.name}
                  </Typography>
                  <Typography variant="h4" color="text.primary" gutterBottom>
                    {data.value.toLocaleString()}
                  </Typography>
                  {formatChange(data.change, data.change_percent)}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Watchlist */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TrendingUp />
          Watchlist
          <Chip label={watchlist.length} size="small" />
        </Typography>
        
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell align="right">Price</TableCell>
                <TableCell align="right">Change</TableCell>
                <TableCell align="right">Change %</TableCell>
                <TableCell align="right">Volume</TableCell>
                <TableCell align="right">High</TableCell>
                <TableCell align="right">Low</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {watchlist.map((symbol) => {
                const data = marketData[symbol];
                if (!data) {
                  return (
                    <TableRow key={symbol}>
                      <TableCell>{symbol}</TableCell>
                      <TableCell colSpan={7} align="center">
                        <LinearProgress size="small" />
                      </TableCell>
                    </TableRow>
                  );
                }

                const isPositive = data.change >= 0;

                return (
                  <TableRow key={symbol} hover>
                    <TableCell>
                      <Typography variant="body1" fontWeight="bold">
                        {symbol}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body1" fontWeight="bold">
                        {formatPrice(data.price)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        color={isPositive ? 'success.main' : 'error.main'}
                      >
                        {isPositive ? '+' : ''}{data.change.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${data.change_percent >= 0 ? '+' : ''}${data.change_percent.toFixed(2)}%`}
                        color={isPositive ? 'success' : 'error'}
                        size="small"
                        icon={isPositive ? <TrendingUp /> : <TrendingDown />}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {data.volume.toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="success.main">
                        {formatPrice(data.high)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="error.main">
                        {formatPrice(data.low)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => removeFromWatchlist([symbol])}
                        color="error"
                      >
                        <Remove />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>

        {watchlist.length === 0 && (
          <Box textAlign="center" py={4}>
            <Typography variant="body1" color="text.secondary">
              No symbols in watchlist. Add symbols to monitor real-time data.
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Market Activity Summary */}
      {Object.keys(marketData).length > 0 && (
        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom color="success.main">
                  Gainers
                </Typography>
                {Object.entries(marketData)
                  .filter(([_, data]) => data.change_percent > 0)
                  .sort((a, b) => b[1].change_percent - a[1].change_percent)
                  .slice(0, 3)
                  .map(([symbol, data]) => (
                    <Box key={symbol} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                      <Typography variant="body2">{symbol}</Typography>
                      <Typography variant="body2" color="success.main">
                        +{data.change_percent.toFixed(2)}%
                      </Typography>
                    </Box>
                  ))}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom color="error.main">
                  Losers
                </Typography>
                {Object.entries(marketData)
                  .filter(([_, data]) => data.change_percent < 0)
                  .sort((a, b) => a[1].change_percent - b[1].change_percent)
                  .slice(0, 3)
                  .map(([symbol, data]) => (
                    <Box key={symbol} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                      <Typography variant="body2">{symbol}</Typography>
                      <Typography variant="body2" color="error.main">
                        {data.change_percent.toFixed(2)}%
                      </Typography>
                    </Box>
                  ))}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Volume Leaders
                </Typography>
                {Object.entries(marketData)
                  .sort((a, b) => b[1].volume - a[1].volume)
                  .slice(0, 3)
                  .map(([symbol, data]) => (
                    <Box key={symbol} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                      <Typography variant="body2">{symbol}</Typography>
                      <Typography variant="body2">
                        {(data.volume / 1000000).toFixed(1)}M
                      </Typography>
                    </Box>
                  ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Dashboard;