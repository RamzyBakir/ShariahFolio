"""
ShariahFolio Data Loader Module
Handles loading, preprocessing, and feature engineering for EGX 33 stock data.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict
from pathlib import Path

from .config import DATA_PATH, EGX33_TICKERS, FEATURE_COLUMNS, SEQUENCE_LENGTH


class DataLoader:
    """Load and preprocess EGX 33 Shariah stock data."""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or DATA_PATH
        self.data: Optional[pd.DataFrame] = None
        self.ticker_data: Dict[str, pd.DataFrame] = {}
        
    def load_data(self) -> pd.DataFrame:
        """Load the CSV data and perform initial preprocessing."""
        print(f"Loading data from {self.data_path}...")
        
        # Load CSV
        self.data = pd.read_csv(self.data_path, parse_dates=["Date"])
        
        # Basic info
        print(f"Loaded {len(self.data)} rows with {self.data['Ticker'].nunique()} tickers")
        
        # Sort by date and ticker
        self.data = self.data.sort_values(["Ticker", "Date"]).reset_index(drop=True)
        
        # Fill missing values
        self._handle_missing_values()
        
        # Calculate RSI if not present
        if "RSI" not in self.data.columns:
            self._calculate_rsi()
        
        # Pre-process per ticker
        self._preprocess_tickers()
        
        return self.data
    
    def _handle_missing_values(self):
        """Handle missing values in the dataset."""
        # Group by ticker and forward fill
        numeric_cols = ["Open", "High", "Low", "Close", "Volume", "Daily_Return", 
                       "Volatility_30d", "SMA_50", "SMA_200"]
        
        for col in numeric_cols:
            if col in self.data.columns:
                # Forward fill within each ticker group
                self.data[col] = self.data.groupby("Ticker")[col].transform(
                    lambda x: x.ffill().bfill()
                )
        
        # Replace any remaining NaN with 0 for returns, or column mean for others
        self.data["Daily_Return"] = self.data["Daily_Return"].fillna(0)
        self.data["Volatility_30d"] = self.data["Volatility_30d"].fillna(
            self.data["Volatility_30d"].mean()
        )
        
    def _calculate_rsi(self, period: int = 14):
        """Calculate RSI for each ticker."""
        def compute_rsi(group):
            delta = group["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        self.data["RSI"] = self.data.groupby("Ticker").apply(
            compute_rsi
        ).reset_index(level=0, drop=True)
        
        self.data["RSI"] = self.data["RSI"].fillna(50)  # Neutral RSI for missing
        
    def _preprocess_tickers(self):
        """Create per-ticker dataframes for quick access."""
        for ticker in self.data["Ticker"].unique():
            ticker_df = self.data[self.data["Ticker"] == ticker].copy()
            ticker_df = ticker_df.sort_values("Date").reset_index(drop=True)
            self.ticker_data[ticker] = ticker_df
            
    def get_ticker_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get data for a specific ticker."""
        if not self.ticker_data:
            self.load_data()
        return self.ticker_data.get(ticker)
    
    def get_valid_tickers(self) -> List[str]:
        """Return list of valid EGX 33 tickers that have sufficient data."""
        if not self.ticker_data:
            self.load_data()
            
        valid = []
        for ticker in EGX33_TICKERS:
            if ticker in self.ticker_data:
                df = self.ticker_data[ticker]
                # Need at least SEQUENCE_LENGTH + 30 days of data
                if len(df) >= SEQUENCE_LENGTH + 30:
                    # Check for sufficient non-null close prices
                    if df["Close"].notna().sum() >= SEQUENCE_LENGTH:
                        valid.append(ticker)
        return valid
    
    def get_ticker_volatility(self) -> Dict[str, float]:
        """Get volatility for each ticker (for risk profiling)."""
        if not self.ticker_data:
            self.load_data()
            
        volatilities = {}
        for ticker, df in self.ticker_data.items():
            if "Volatility_30d" in df.columns and len(df) > 0:
                vol = df["Volatility_30d"].dropna()
                if len(vol) > 0:
                    volatilities[ticker] = vol.iloc[-1]  # Latest volatility
        return volatilities
    
    def create_sequences(
        self, 
        ticker: str, 
        seq_length: int = SEQUENCE_LENGTH,
        feature_cols: List[str] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training.
        
        Returns:
            X: Shape (num_samples, seq_length, num_features)
            y: Shape (num_samples,) - next day's return
        """
        if feature_cols is None:
            feature_cols = ["Close", "Volume", "Daily_Return", "Volatility_30d", "SMA_50"]
        
        df = self.get_ticker_data(ticker)
        if df is None or len(df) < seq_length + 1:
            return np.array([]), np.array([])
        
        # Get feature matrix
        available_cols = [c for c in feature_cols if c in df.columns]
        features = df[available_cols].values
        
        # Normalize features
        features = self._normalize(features)
        
        # Create target (next day's return)
        returns = df["Daily_Return"].values
        
        X, y = [], []
        for i in range(len(features) - seq_length):
            X.append(features[i:i + seq_length])
            y.append(returns[i + seq_length])
        
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)
    
    def _normalize(self, features: np.ndarray) -> np.ndarray:
        """Normalize features using min-max scaling."""
        # Handle edge cases
        if len(features) == 0:
            return features
            
        # Replace inf with nan, then fill
        features = np.where(np.isinf(features), np.nan, features)
        
        # Column-wise normalization
        for i in range(features.shape[1]):
            col = features[:, i]
            col_min = np.nanmin(col)
            col_max = np.nanmax(col)
            if col_max - col_min > 0:
                features[:, i] = (col - col_min) / (col_max - col_min)
            else:
                features[:, i] = 0
                
        # Fill remaining NaN
        features = np.nan_to_num(features, 0)
        
        return features
    
    def get_returns_matrix(self, tickers: List[str]) -> pd.DataFrame:
        """
        Get a matrix of daily returns for multiple tickers.
        Used for covariance calculation in portfolio optimization.
        """
        if not self.ticker_data:
            self.load_data()
            
        returns_dict = {}
        for ticker in tickers:
            if ticker in self.ticker_data:
                df = self.ticker_data[ticker]
                returns_dict[ticker] = df.set_index("Date")["Daily_Return"]
        
        # Combine into DataFrame, align by date
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()
        
        return returns_df
    
    def get_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get the latest closing prices for given tickers."""
        if not self.ticker_data:
            self.load_data()
            
        prices = {}
        for ticker in tickers:
            if ticker in self.ticker_data:
                df = self.ticker_data[ticker]
                if len(df) > 0:
                    prices[ticker] = df["Close"].iloc[-1]
        return prices


# Singleton instance for easy access
_data_loader: Optional[DataLoader] = None


def get_data_loader() -> DataLoader:
    """Get or create the singleton DataLoader instance."""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
        _data_loader.load_data()
    return _data_loader
