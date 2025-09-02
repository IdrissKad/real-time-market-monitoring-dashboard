import React, { useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab
} from '@mui/material';
import {
  AccountBalanceWallet,
  Add,
  Delete,
  Analytics,
  PieChart,
  TrendingUp,
  Assessment
} from '@mui/icons-material';

import { PieChart as RechartsPieChart, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import axios from 'axios';

interface Position {
  symbol: string;
  shares: number;
  avg_cost: number;
}

interface Portfolio {
  name: string;
  positions: Position[];
  cash: number;
}

interface PortfolioAnalysis {
  portfolio_name: string;
  summary: {
    total_value: number;
    total_cost: number;
    cash: number;
    total_unrealized_pnl: number;
    total_unrealized_pnl_pct: number;
    daily_pnl: number;
    daily_pnl_pct: number;
  };
  positions: Array<{
    symbol: string;
    shares: number;
    current_price: number;
    market_value: number;
    cost_basis: number;
    unrealized_pnl: number;
    unrealized_pnl_pct: number;
    weight: number;
    day_change: number;
    day_change_pct: number;
  }>;
  sector_allocation: Record<string, number>;
}

const Portfolio: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [portfolio, setPortfolio] = useState<Portfolio>({
    name: 'My Portfolio',
    positions: [
      { symbol: 'AAPL', shares: 50, avg_cost: 150.00 },
      { symbol: 'GOOGL', shares: 10, avg_cost: 2500.00 },
      { symbol: 'MSFT', shares: 25, avg_cost: 280.00 },
    ],
    cash: 10000
  });
  
  const [analysis, setAnalysis] = useState<PortfolioAnalysis | null>(null);
  const [addPositionOpen, setAddPositionOpen] = useState(false);
  const [newPosition, setNewPosition] = useState<Position>({ symbol: '', shares: 0, avg_cost: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const analyzePortfolio = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/v1/portfolio/analyze', portfolio);
      setAnalysis(response.data);
    } catch (err) {
      setError('Failed to analyze portfolio');
      console.error('Error analyzing portfolio:', err);
    } finally {
      setLoading(false);
    }
  };

  const addPosition = () => {
    if (newPosition.symbol && newPosition.shares > 0 && newPosition.avg_cost > 0) {
      setPortfolio(prev => ({
        ...prev,
        positions: [...prev.positions, { ...newPosition, symbol: newPosition.symbol.toUpperCase() }]
      }));
      setNewPosition({ symbol: '', shares: 0, avg_cost: 0 });
      setAddPositionOpen(false);
    }
  };

  const removePosition = (index: number) => {
    setPortfolio(prev => ({
      ...prev,
      positions: prev.positions.filter((_, i) => i !== index)
    }));
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercent = (percent: number) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const getColorForValue = (value: number) => {
    return value >= 0 ? 'success.main' : 'error.main';
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  const pieChartData = analysis?.positions.map((pos, index) => ({
    name: pos.symbol,
    value: pos.weight,
    color: COLORS[index % COLORS.length]
  })) || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <AccountBalanceWallet />
          <Typography variant="h4">Portfolio Manager</Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Add />}
            onClick={() => setAddPositionOpen(true)}
          >
            Add Position
          </Button>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={16} /> : <Analytics />}
            onClick={analyzePortfolio}
            disabled={loading || portfolio.positions.length === 0}
          >
            Analyze Portfolio
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Tabs value={selectedTab} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Holdings" icon={<AccountBalanceWallet />} />
        <Tab label="Analysis" icon={<Assessment />} disabled={!analysis} />
        <Tab label="Allocation" icon={<PieChart />} disabled={!analysis} />
      </Tabs>

      {/* Holdings Tab */}
      {selectedTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Current Holdings
              </Typography>
              
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell align="right">Shares</TableCell>
                      <TableCell align="right">Avg Cost</TableCell>
                      <TableCell align="right">Total Cost</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {portfolio.positions.map((position, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography variant="body1" fontWeight="bold">
                            {position.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">{position.shares}</TableCell>
                        <TableCell align="right">{formatCurrency(position.avg_cost)}</TableCell>
                        <TableCell align="right">
                          {formatCurrency(position.shares * position.avg_cost)}
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={() => removePosition(index)}
                            color="error"
                          >
                            <Delete />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow>
                      <TableCell><strong>Cash</strong></TableCell>
                      <TableCell align="right">-</TableCell>
                      <TableCell align="right">-</TableCell>
                      <TableCell align="right">
                        <strong>{formatCurrency(portfolio.cash)}</strong>
                      </TableCell>
                      <TableCell align="center">-</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Analysis Tab */}
      {selectedTab === 1 && analysis && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary">
                      Total Value
                    </Typography>
                    <Typography variant="h5">
                      {formatCurrency(analysis.summary.total_value)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary">
                      Total Return
                    </Typography>
                    <Typography variant="h5" color={getColorForValue(analysis.summary.total_unrealized_pnl)}>
                      {formatCurrency(analysis.summary.total_unrealized_pnl)}
                    </Typography>
                    <Typography variant="body2" color={getColorForValue(analysis.summary.total_unrealized_pnl_pct)}>
                      {formatPercent(analysis.summary.total_unrealized_pnl_pct)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary">
                      Daily P&L
                    </Typography>
                    <Typography variant="h5" color={getColorForValue(analysis.summary.daily_pnl)}>
                      {formatCurrency(analysis.summary.daily_pnl)}
                    </Typography>
                    <Typography variant="body2" color={getColorForValue(analysis.summary.daily_pnl_pct)}>
                      {formatPercent(analysis.summary.daily_pnl_pct)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary">
                      Cash
                    </Typography>
                    <Typography variant="h5">
                      {formatCurrency(analysis.summary.cash)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Position Details
              </Typography>
              
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell align="right">Current Price</TableCell>
                      <TableCell align="right">Market Value</TableCell>
                      <TableCell align="right">Unrealized P&L</TableCell>
                      <TableCell align="right">Weight</TableCell>
                      <TableCell align="right">Day Change</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analysis.positions.map((position) => (
                      <TableRow key={position.symbol}>
                        <TableCell>
                          <Typography variant="body1" fontWeight="bold">
                            {position.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatCurrency(position.current_price)}
                        </TableCell>
                        <TableCell align="right">
                          {formatCurrency(position.market_value)}
                        </TableCell>
                        <TableCell align="right">
                          <Box>
                            <Typography variant="body2" color={getColorForValue(position.unrealized_pnl)}>
                              {formatCurrency(position.unrealized_pnl)}
                            </Typography>
                            <Typography variant="caption" color={getColorForValue(position.unrealized_pnl_pct)}>
                              {formatPercent(position.unrealized_pnl_pct)}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          {position.weight.toFixed(1)}%
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={formatPercent(position.day_change_pct)}
                            color={position.day_change >= 0 ? "success" : "error"}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Allocation Tab */}
      {selectedTab === 2 && analysis && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Portfolio Allocation
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <RechartsPieChart>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </RechartsPieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Sector Allocation
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={Object.entries(analysis.sector_allocation).map(([sector, percentage]) => ({
                    sector: sector.replace(' ', '\n'),
                    percentage: percentage
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="sector" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, 'Allocation']} />
                  <Bar dataKey="percentage" fill="#00C49F" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Allocation Summary
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(analysis.sector_allocation).map(([sector, percentage]) => (
                    <Grid item xs={6} md={4} key={sector}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2">{sector}:</Typography>
                        <Chip label={`${percentage.toFixed(1)}%`} size="small" />
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Add Position Dialog */}
      <Dialog open={addPositionOpen} onClose={() => setAddPositionOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Position</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Symbol"
              value={newPosition.symbol}
              onChange={(e) => setNewPosition(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
              fullWidth
            />
            <TextField
              label="Shares"
              type="number"
              value={newPosition.shares || ''}
              onChange={(e) => setNewPosition(prev => ({ ...prev, shares: Number(e.target.value) }))}
              fullWidth
            />
            <TextField
              label="Average Cost"
              type="number"
              value={newPosition.avg_cost || ''}
              onChange={(e) => setNewPosition(prev => ({ ...prev, avg_cost: Number(e.target.value) }))}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddPositionOpen(false)}>Cancel</Button>
          <Button onClick={addPosition} variant="contained">Add Position</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Portfolio;