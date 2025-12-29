"""
ShariahFolio Data Loader Module
Handles loading, preprocessing, and feature engineering for EGX 33 stock data.

Features:
- CSV data loading with error handling
- Missing value imputation
- Per-ticker data organization
- Sequence creation for LSTM training
- Volatility and returns calculations
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict
from pathlib import Path

from .config import DATA_PATH, EGX33_TICKERS, FEATURE_COLUMNS, SEQUENCE_LENGTH

# Configure logger
logger = logging.getLogger(__name__)


class DataLoader:
    """Load and preprocess EGX 33 Shariah stock data."""

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the DataLoader.

        Args:
            data_path: Optional custom path to the data CSV file
        """
        self.data_path = data_path if data_path is not None else DATA_PATH
        self.data: Optional[pd.DataFrame] = None
        self.ticker_data: Dict[str, pd.DataFrame] = {}
        self._loaded = False

    def load_data(self) -> pd.DataFrame:
        """
        Load the CSV data and perform initial preprocessing.

        Returns:
            The preprocessed DataFrame

        Raises:
            FileNotFoundError: If the data file doesn't exist
            ValueError: If the data file is empty or invalid
        """
        data_path = Path(self.data_path)

        if not data_path.exists():
            logger.error(f"Data file not found: {self.data_path}")
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        logger.info(f"Loading data from {self.data_path}...")

        try:
            # Load CSV
            self.data = pd.read_csv(self.data_path, parse_dates=["Date"])
        except Exception as e:
            logger.exception(f"Failed to load CSV: {e}")
            raise ValueError(f"Failed to load data file: {e}")

        if self.data is None or len(self.data) == 0:
            logger.error("Data file is empty")
            raise ValueError("Data file is empty")

        # Basic info
        num_tickers = self.data['Ticker'].nunique()
        logger.info(f"Loaded {len(self.data)} rows with {num_tickers} tickers")

        # Sort by date and ticker
        self.data = self.data.sort_values(["Ticker", "Date"]).reset_index(drop=True)

        # Fill missing values
        self._handle_missing_values()

        # Calculate RSI if not present
        if "RSI" not in self.data.columns:
            self._calculate_rsi()

        # Pre-process per ticker
        self._preprocess_tickers()

        self._loaded = True
        logger.info(f"Data preprocessing complete. {len(self.ticker_data)} tickers available.")

        return self.data

    def _handle_missing_values(self) -> None:
        """Handle missing values in the dataset."""
        logger.debug("Handling missing values...")

        # Group by ticker and forward fill
        numeric_cols = [
            "Open", "High", "Low", "Close", "Volume",
            "Daily_Return", "Volatility_30d", "SMA_50", "SMA_200"
        ]

        for col in numeric_cols:
            if col in self.data.columns:
                # Forward fill within each ticker group
                self.data[col] = self.data.groupby("Ticker")[col].transform(
                    lambda x: x.ffill().bfill()
                )

        # Replace any remaining NaN with 0 for returns, or column mean for others
        if "Daily_Return" in self.data.columns:
            self.data["Daily_Return"] = self.data["Daily_Return"].fillna(0)

        if "Volatility_30d" in self.data.columns:
            vol_mean = self.data["Volatility_30d"].mean()
            self.data["Volatility_30d"] = self.data["Volatility_30d"].fillna(vol_mean)

    def _calculate_rsi(self, period: int = 14) -> None:
        """
        Calculate RSI (Relative Strength Index) for each ticker.

        Args:
            period: The lookback period for RSI calculation
        """
        logger.debug(f"Calculating RSI with period={period}...")

        def compute_rsi(group: pd.DataFrame) -> pd.Series:
            delta = group["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        self.data["RSI"] = self.data.groupby("Ticker").apply(
            compute_rsi
        ).reset_index(level=0, drop=True)

        # Neutral RSI for missing values
        self.data["RSI"] = self.data["RSI"].fillna(50)

    def _preprocess_tickers(self) -> None:
        """Create per-ticker dataframes for quick access."""
        logger.debug("Creating per-ticker dataframes...")

        for ticker in self.data["Ticker"].unique():
            ticker_df = self.data[self.data["Ticker"] == ticker].copy()
            ticker_df = ticker_df.sort_values("Date").reset_index(drop=True)
            self.ticker_data[ticker] = ticker_df

    def get_ticker_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Get data for a specific ticker.

        Args:
            ticker: The ticker symbol (e.g., "ETEL.CA")

        Returns:
            DataFrame with the ticker's data, or None if not found
        """
        if not self._loaded:
            self.load_data()
        return self.ticker_data.get(ticker)

    def get_valid_tickers(self) -> List[str]:
        """
        Return list of valid EGX 33 tickers that have sufficient data.

        A ticker is considered valid if it has at least SEQUENCE_LENGTH + 30
        days of data with non-null close prices.

        Returns:
            List of valid ticker symbols
        """
        if not self._loaded:
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

        logger.debug(f"Found {len(valid)} valid tickers out of {len(EGX33_TICKERS)}")
        return valid

    def get_ticker_volatility(self) -> Dict[str, float]:
        """
        Get the latest volatility for each ticker (for risk profiling).

        Returns:
            Dictionary mapping ticker symbols to their latest 30-day volatility
        """
        if not self._loaded:
            self.load_data()

        volatilities = {}
        for ticker, df in self.ticker_data.items():
            if "Volatility_30d" in df.columns and len(df) > 0:
                vol = df["Volatility_30d"].dropna()
                if len(vol) > 0:
                    volatilities[ticker] = float(vol.iloc[-1])  # Latest volatility

        return volatilities

    def create_sequences(
        self,
        ticker: str,
        seq_length: int = SEQUENCE_LENGTH,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training.

        Args:
            ticker: The ticker symbol
            seq_length: Length of each sequence
            feature_cols: List of feature column names to use

        Returns:
            Tuple of (X, y) where:
                X: Shape (num_samples, seq_length, num_features)
                y: Shape (num_samples,) - next day's return
        """
        if feature_cols is None:
            feature_cols = ["Close", "Volume", "Daily_Return", "Volatility_30d", "SMA_50"]

        df = self.get_ticker_data(ticker)
        if df is None or len(df) < seq_length + 1:
            logger.warning(f"Insufficient data for {ticker}: need {seq_length + 1}, have {len(df) if df is not None else 0}")
            return np.array([]), np.array([])

        # Get feature matrix
        available_cols = [c for c in feature_cols if c in df.columns]
        if not available_cols:
            logger.warning(f"No valid feature columns found for {ticker}")
            return np.array([]), np.array([])

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
        """
        Normalize features using min-max scaling.

        Args:
            features: 2D array of shape (num_samples, num_features)

        Returns:
            Normalized features array
        """
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
        features = np.nan_to_num(features, nan=0.0)

        return features

    def get_returns_matrix(self, tickers: List[str]) -> pd.DataFrame:
        """
        Get a matrix of daily returns for multiple tickers.
        Used for covariance calculation in portfolio optimization.

        Args:
            tickers: List of ticker symbols

        Returns:
            DataFrame with dates as index and tickers as columns
        """
        if not self._loaded:
            self.load_data()

        returns_dict = {}
        for ticker in tickers:
            if ticker in self.ticker_data:
                df = self.ticker_data[ticker]
                returns_dict[ticker] = df.set_index("Date")["Daily_Return"]

        if not returns_dict:
            logger.warning("No valid tickers found for returns matrix")
            return pd.DataFrame()

        # Combine into DataFrame, align by date
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()

        logger.debug(f"Returns matrix: {len(returns_df)} rows, {len(returns_df.columns)} tickers")

        return returns_df

    def get_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """
        Get the latest closing prices for given tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping ticker symbols to their latest prices
        """
        if not self._loaded:
            self.load_data()

        prices = {}
        for ticker in tickers:
            if ticker in self.ticker_data:
                df = self.ticker_data[ticker]
                if len(df) > 0 and "Close" in df.columns:
                    close_price = df["Close"].iloc[-1]
                    if pd.notna(close_price):
                        prices[ticker] = float(close_price)

        return prices

    def get_ticker_info(self, ticker: str) -> Optional[Dict]:
        """
        Get summary information about a ticker.

        Args:
            ticker: The ticker symbol

        Returns:
            Dictionary with ticker info, or None if not found
        """
        df = self.get_ticker_data(ticker)
        if df is None or len(df) == 0:
            return None

        return {
            "ticker": ticker,
            "data_points": len(df),
            "date_range": {
                "start": df["Date"].min().isoformat() if pd.notna(df["Date"].min()) else None,
                "end": df["Date"].max().isoformat() if pd.notna(df["Date"].max()) else None
            },
            "latest_price": float(df["Close"].iloc[-1]) if pd.notna(df["Close"].iloc[-1]) else None,
            "volatility_30d": float(df["Volatility_30d"].iloc[-1]) if "Volatility_30d" in df.columns and pd.notna(df["Volatility_30d"].iloc[-1]) else None
        }

    def is_loaded(self) -> bool:
        """Check if data has been loaded."""
        return self._loaded


# Singleton instance for easy access
_data_loader: Optional[DataLoader] = None


def get_data_loader() -> DataLoader:
    """
    Get or create the singleton DataLoader instance.

    Returns:
        The global DataLoader instance with data loaded
    """
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
        _data_loader.load_data()
    return _data_loader


def reset_data_loader() -> None:
    """Reset the singleton DataLoader instance. Useful for testing."""
    global _data_loader
    _data_loader = None
