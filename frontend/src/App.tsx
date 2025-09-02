import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Paper,
  Box,
  Tab,
  Tabs,
  IconButton
} from '@mui/material';
import {
  TrendingUp,
  Dashboard,
  Analytics,
  AccountBalanceWallet,
  Brightness4,
  Brightness7
} from '@mui/icons-material';

import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Portfolio from './pages/Portfolio';
import { useWebSocket } from './hooks/useWebSocket';
import { MarketDataProvider } from './contexts/MarketDataContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`nav-tabpanel-${index}`}
      aria-labelledby={`nav-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : true;
  });
  
  const [currentTab, setCurrentTab] = useState(0);

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: darkMode ? '#00e676' : '#1976d2',
      },
      secondary: {
        main: darkMode ? '#ff4081' : '#dc004e',
      },
      background: {
        default: darkMode ? '#0a0e1a' : '#f5f5f5',
        paper: darkMode ? '#1a1d29' : '#ffffff',
      },
      success: {
        main: '#00e676',
      },
      error: {
        main: '#f44336',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h4: {
        fontWeight: 600,
      },
      h6: {
        fontWeight: 500,
      },
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            border: darkMode ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid rgba(0, 0, 0, 0.12)',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: darkMode ? '#1a1d29' : '#1976d2',
            borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.12)' : 'none',
          },
        },
      },
    },
  });

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <MarketDataProvider>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <AppBar position="static" elevation={0}>
            <Toolbar>
              <TrendingUp sx={{ mr: 2 }} />
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Market Monitor Pro
              </Typography>
              <IconButton color="inherit" onClick={toggleDarkMode}>
                {darkMode ? <Brightness7 /> : <Brightness4 />}
              </IconButton>
            </Toolbar>
            <Tabs
              value={currentTab}
              onChange={handleTabChange}
              centered
              sx={{
                borderBottom: 1,
                borderColor: 'divider',
                '& .MuiTab-root': {
                  color: 'rgba(255, 255, 255, 0.7)',
                  '&.Mui-selected': {
                    color: 'white',
                  },
                },
              }}
            >
              <Tab
                icon={<Dashboard />}
                label="Dashboard"
                sx={{ textTransform: 'none', fontSize: '1rem' }}
              />
              <Tab
                icon={<Analytics />}
                label="Analytics"
                sx={{ textTransform: 'none', fontSize: '1rem' }}
              />
              <Tab
                icon={<AccountBalanceWallet />}
                label="Portfolio"
                sx={{ textTransform: 'none', fontSize: '1rem' }}
              />
            </Tabs>
          </AppBar>

          <Container maxWidth="xl" sx={{ flexGrow: 1, py: 2 }}>
            <TabPanel value={currentTab} index={0}>
              <Dashboard />
            </TabPanel>
            <TabPanel value={currentTab} index={1}>
              <Analytics />
            </TabPanel>
            <TabPanel value={currentTab} index={2}>
              <Portfolio />
            </TabPanel>
          </Container>

          <Box
            component="footer"
            sx={{
              py: 2,
              px: 3,
              mt: 'auto',
              backgroundColor: theme.palette.background.paper,
              borderTop: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography variant="body2" color="text.secondary" align="center">
              © 2024 Market Monitor Pro - Real-time Financial Analytics Platform
            </Typography>
          </Box>
        </Box>
      </MarketDataProvider>
    </ThemeProvider>
  );
}

export default App;