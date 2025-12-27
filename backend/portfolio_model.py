"""
ShariahFolio Portfolio Model Module
Contains LSTM model for return prediction and Mean-Variance Portfolio Optimization.
OPTIMIZED FOR SPEED - Training should complete in under 2 minutes.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader as TorchDataLoader, TensorDataset
from typing import Dict, List, Tuple, Optional, Callable
from scipy.optimize import minimize
import warnings
import time

from .config import (
    LSTM_HIDDEN_SIZE, LSTM_NUM_LAYERS, SEQUENCE_LENGTH, 
    PREDICTION_HORIZON, EGX33_TICKERS
)
from .data_loader import get_data_loader

warnings.filterwarnings('ignore')

# SPEED OPTIMIZATION: Reduced parameters
FAST_EPOCHS = 5  # Reduced from 30-50
FAST_BATCH_SIZE = 64  # Increased for faster processing
FAST_SEQUENCE_LENGTH = 30  # Reduced from 60


class LSTMPredictor(nn.Module):
    """LSTM Network for stock return prediction - Lightweight version."""
    
    def __init__(
        self, 
        input_size: int, 
        hidden_size: int = 32,  # Reduced from 64
        num_layers: int = 1,    # Reduced from 2
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Simpler FC layer
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)
        last_out = lstm_out[:, -1, :]
        prediction = self.fc(last_out)
        return prediction.squeeze(-1)


class PortfolioOptimizer:
    """
    Portfolio optimization using LSTM predictions and Mean-Variance Optimization.
    OPTIMIZED FOR SPEED.
    """
    
    def __init__(self, device: str = None, progress_callback: Callable = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.models: Dict[str, LSTMPredictor] = {}
        self.trained = False
        self.data_loader = get_data_loader()
        self.progress_callback = progress_callback
        print(f"[INIT] PortfolioOptimizer initialized (device: {self.device})")
        
    def _log(self, message: str):
        """Log to console and callback if available."""
        print(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def train_model(
        self, 
        tickers: List[str] = None,
        epochs: int = FAST_EPOCHS,
        learning_rate: float = 0.01,  # Increased for faster convergence
        batch_size: int = FAST_BATCH_SIZE
    ) -> Dict[str, float]:
        """
        Train LSTM models for each ticker - FAST VERSION.
        Target: Complete in under 2 minutes for 10 tickers.
        """
        if tickers is None:
            tickers = self.data_loader.get_valid_tickers()
        
        start_time = time.time()
        self._log(f"[TRAIN] Starting FAST training for {len(tickers)} tickers...")
        self._log(f"   Config: {epochs} epochs, batch_size={batch_size}, seq_len={FAST_SEQUENCE_LENGTH}")
        
        losses = {}
        
        for i, ticker in enumerate(tickers, 1):
            ticker_start = time.time()
            self._log(f"  [{i}/{len(tickers)}] Training {ticker}...")
            
            # Get sequences with shorter length
            X, y = self._create_fast_sequences(ticker)
            
            if len(X) < batch_size:
                self._log(f"  [SKIP] {ticker} - insufficient data ({len(X)} samples)")
                continue
            
            # Subsample if too much data (speed up)
            if len(X) > 1000:
                indices = np.random.choice(len(X), 1000, replace=False)
                X, y = X[indices], y[indices]
            
            # Convert to tensors
            X_tensor = torch.FloatTensor(X).to(self.device)
            y_tensor = torch.FloatTensor(y).to(self.device)
            
            # Create data loader
            dataset = TensorDataset(X_tensor, y_tensor)
            train_loader = TorchDataLoader(dataset, batch_size=batch_size, shuffle=True)
            
            # Create lightweight model
            input_size = X.shape[2]
            model = LSTMPredictor(input_size).to(self.device)
            
            # Training with higher learning rate
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
            
            model.train()
            final_loss = 0
            
            for epoch in range(epochs):
                epoch_loss = 0
                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    predictions = model(batch_X)
                    loss = criterion(predictions, batch_y)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item()
                final_loss = epoch_loss / len(train_loader)
            
            self.models[ticker] = model
            losses[ticker] = final_loss
            
            elapsed = time.time() - ticker_start
            self._log(f"  [DONE] {ticker} in {elapsed:.1f}s (loss: {final_loss:.6f})")
        
        self.trained = True
        total_time = time.time() - start_time
        self._log(f"[COMPLETE] Training done! {len(self.models)} models in {total_time:.1f}s")
        
        return losses
    
    def _create_fast_sequences(self, ticker: str) -> Tuple[np.ndarray, np.ndarray]:
        """Create shorter sequences for faster training."""
        feature_cols = ["Close", "Daily_Return", "Volatility_30d"]  # Fewer features
        
        df = self.data_loader.get_ticker_data(ticker)
        if df is None or len(df) < FAST_SEQUENCE_LENGTH + 1:
            return np.array([]), np.array([])
        
        # Get feature matrix
        available_cols = [c for c in feature_cols if c in df.columns]
        features = df[available_cols].values
        
        # Quick normalization
        features = self._normalize(features)
        
        # Create target
        returns = df["Daily_Return"].values
        
        X, y = [], []
        # Step by 5 to reduce samples
        for i in range(0, len(features) - FAST_SEQUENCE_LENGTH, 5):
            X.append(features[i:i + FAST_SEQUENCE_LENGTH])
            y.append(returns[i + FAST_SEQUENCE_LENGTH])
        
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)
    
    def _normalize(self, features: np.ndarray) -> np.ndarray:
        """Fast normalization."""
        if len(features) == 0:
            return features
        features = np.where(np.isinf(features), np.nan, features)
        for i in range(features.shape[1]):
            col = features[:, i]
            col_min, col_max = np.nanmin(col), np.nanmax(col)
            if col_max - col_min > 0:
                features[:, i] = (col - col_min) / (col_max - col_min)
            else:
                features[:, i] = 0
        return np.nan_to_num(features, 0)
    
    def predict_returns(
        self, 
        tickers: List[str],
        horizon: int = PREDICTION_HORIZON
    ) -> Dict[str, float]:
        """Predict expected returns for given tickers."""
        
        # Train only missing models
        missing_tickers = [t for t in tickers if t not in self.models]
        if missing_tickers:
            self._log(f"[TRAIN] Training models for {len(missing_tickers)} new tickers...")
            self.train_model(missing_tickers)
        
        predictions = {}
        
        for ticker in tickers:
            if ticker in self.models:
                model = self.models[ticker]
                model.eval()
                
                X, _ = self._create_fast_sequences(ticker)
                if len(X) > 0:
                    with torch.no_grad():
                        latest_seq = torch.FloatTensor(X[-1:]).to(self.device)
                        pred = model(latest_seq).cpu().numpy()[0]
                        expected_return = pred * horizon
                        predictions[ticker] = float(expected_return)
            else:
                # Use historical average as fallback
                df = self.data_loader.get_ticker_data(ticker)
                if df is not None and len(df) > 0:
                    avg_return = df["Daily_Return"].mean() * horizon
                    predictions[ticker] = float(avg_return) if not np.isnan(avg_return) else 0.05
                        
        return predictions
    
    def optimize_portfolio(
        self, 
        tickers: List[str],
        investment_amount: float,
        risk_free_rate: float = 0.02
    ) -> Dict[str, Dict]:
        """Optimize portfolio using Mean-Variance Optimization."""
        
        start_time = time.time()
        self._log(f"[OPTIMIZE] Optimizing portfolio for {len(tickers)} stocks...")
        
        # Filter to valid tickers
        valid_tickers = [t for t in tickers if t in self.data_loader.ticker_data]
        
        if len(valid_tickers) == 0:
            return {"error": "No valid tickers provided"}
        
        if len(valid_tickers) == 1:
            ticker = valid_tickers[0]
            return {
                "weights": {ticker: 1.0},
                "allocation": {ticker: investment_amount},
                "expected_return": 0.0,
                "expected_volatility": 0.0,
                "sharpe_ratio": 0.0
            }
        
        # Get expected returns from LSTM predictions
        self._log("[PREDICT] Getting LSTM predictions...")
        expected_returns = self.predict_returns(valid_tickers)
        
        # Get historical returns for covariance
        self._log("[CALC] Calculating covariance matrix...")
        returns_df = self.data_loader.get_returns_matrix(valid_tickers)
        
        if len(returns_df) < 30:
            return {"error": "Insufficient historical data for optimization"}
        
        # Calculate covariance matrix (annualized)
        cov_matrix = returns_df.cov() * 252
        
        # Ensure we have expected returns for all tickers
        mu = np.array([expected_returns.get(t, 0.05) for t in valid_tickers])
        
        # Mean-Variance Optimization
        n_assets = len(valid_tickers)
        
        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix.values, weights)))
        
        def negative_sharpe(weights):
            ret = np.dot(weights, mu)
            vol = portfolio_volatility(weights)
            if vol == 0:
                return 0
            return -(ret - risk_free_rate) / vol
        
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        bounds = tuple((0.0, 0.5) for _ in range(n_assets))
        initial_weights = np.array([1/n_assets] * n_assets)
        
        self._log("[OPT] Running optimization...")
        result = minimize(
            negative_sharpe,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints
        )
        
        if not result.success:
            optimal_weights = initial_weights
        else:
            optimal_weights = result.x
        
        # Round small weights to 0
        optimal_weights = np.where(optimal_weights < 0.01, 0, optimal_weights)
        if optimal_weights.sum() > 0:
            optimal_weights = optimal_weights / optimal_weights.sum()
        
        # Calculate metrics
        expected_portfolio_return = np.dot(optimal_weights, mu)
        expected_volatility = portfolio_volatility(optimal_weights)
        sharpe = (expected_portfolio_return - risk_free_rate) / expected_volatility if expected_volatility > 0 else 0
        
        # Build result
        weights_dict = {t: float(w) for t, w in zip(valid_tickers, optimal_weights) if w > 0}
        allocation_dict = {t: float(w * investment_amount) for t, w in zip(valid_tickers, optimal_weights) if w > 0}
        
        total_time = time.time() - start_time
        self._log(f"[DONE] Optimization complete in {total_time:.1f}s")
        
        return {
            "weights": weights_dict,
            "allocation": allocation_dict,
            "expected_return": float(expected_portfolio_return),
            "expected_volatility": float(expected_volatility),
            "sharpe_ratio": float(sharpe),
            "investment_amount": investment_amount
        }
    
    def get_stocks_by_risk_profile(self, risk_profile: str) -> List[str]:
        """Get recommended stocks based on risk profile."""
        volatilities = self.data_loader.get_ticker_volatility()
        
        if not volatilities:
            return self.data_loader.get_valid_tickers()[:5]
        
        sorted_tickers = sorted(volatilities.items(), key=lambda x: x[1])
        
        if risk_profile == "conservative":
            cutoff = len(sorted_tickers) // 3
            return [t for t, v in sorted_tickers[:max(cutoff, 5)]]
        elif risk_profile == "moderate":
            low = len(sorted_tickers) // 3
            high = 2 * len(sorted_tickers) // 3
            return [t for t, v in sorted_tickers[low:high]]
        else:  # aggressive
            cutoff = 2 * len(sorted_tickers) // 3
            return [t for t, v in sorted_tickers[cutoff:]]


# Singleton instance
_optimizer: Optional[PortfolioOptimizer] = None


def get_optimizer() -> PortfolioOptimizer:
    """Get or create the singleton PortfolioOptimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = PortfolioOptimizer()
    return _optimizer
