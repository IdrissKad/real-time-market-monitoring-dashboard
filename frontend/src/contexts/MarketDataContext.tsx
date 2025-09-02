import React, { createContext, useContext, useEffect, useState } from 'react';
import { useWebSocket, MarketData, WebSocketHook } from '../hooks/useWebSocket';

interface MarketDataContextType extends WebSocketHook {
  watchlist: string[];
  addToWatchlist: (symbols: string[]) => void;
  removeFromWatchlist: (symbols: string[]) => void;
  clearWatchlist: () => void;
}

const MarketDataContext = createContext<MarketDataContextType | undefined>(undefined);

export const useMarketData = () => {
  const context = useContext(MarketDataContext);
  if (!context) {
    throw new Error('useMarketData must be used within a MarketDataProvider');
  }
  return context;
};

interface MarketDataProviderProps {
  children: React.ReactNode;
}

export const MarketDataProvider: React.FC<MarketDataProviderProps> = ({ children }) => {
  const webSocket = useWebSocket();
  const [watchlist, setWatchlist] = useState<string[]>(() => {
    // Load watchlist from localStorage
    const saved = localStorage.getItem('market-watchlist');
    return saved ? JSON.parse(saved) : [
      'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 
      'META', 'NVDA', 'SPY', 'QQQ', 'IWM'
    ];
  });

  // Subscribe to watchlist symbols when WebSocket connects
  useEffect(() => {
    if (webSocket.isConnected && watchlist.length > 0) {
      webSocket.subscribe(watchlist);
    }
  }, [webSocket.isConnected, watchlist, webSocket]);

  // Save watchlist to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('market-watchlist', JSON.stringify(watchlist));
  }, [watchlist]);

  const addToWatchlist = (symbols: string[]) => {
    const upperSymbols = symbols.map(s => s.toUpperCase());
    const newSymbols = upperSymbols.filter(symbol => !watchlist.includes(symbol));
    
    if (newSymbols.length > 0) {
      setWatchlist(prev => [...prev, ...newSymbols]);
      if (webSocket.isConnected) {
        webSocket.subscribe(newSymbols);
      }
    }
  };

  const removeFromWatchlist = (symbols: string[]) => {
    const upperSymbols = symbols.map(s => s.toUpperCase());
    setWatchlist(prev => prev.filter(symbol => !upperSymbols.includes(symbol)));
    
    if (webSocket.isConnected) {
      webSocket.unsubscribe(upperSymbols);
    }
  };

  const clearWatchlist = () => {
    if (webSocket.isConnected) {
      webSocket.unsubscribe(watchlist);
    }
    setWatchlist([]);
  };

  const contextValue: MarketDataContextType = {
    ...webSocket,
    watchlist,
    addToWatchlist,
    removeFromWatchlist,
    clearWatchlist,
  };

  return (
    <MarketDataContext.Provider value={contextValue}>
      {children}
    </MarketDataContext.Provider>
  );
};