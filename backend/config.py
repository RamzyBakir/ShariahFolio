"""
ShariahFolio Configuration Module
Contains API configuration, model parameters, and EGX 33 ticker list.

Features:
- Environment variable loading with validation
- Centralized configuration for all modules
- EGX 33 Shariah Index ticker definitions
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure module logger
logger = logging.getLogger(__name__)

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Project paths
BACKEND_DIR = Path(__file__).parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
PROMPTS_DIR = BACKEND_DIR / "prompts"

# Data file path
DATA_PATH = str(DATA_DIR / "egx33_shariah_advanced_features.csv")

# =============================================================================
# API CONFIGURATION
# =============================================================================

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "xiaomi/mimo-v2-flash:free")

def validate_api_config() -> bool:
    """
    Validate API configuration on startup.
    Returns True if valid, False otherwise.
    """
    if not OPENROUTER_API_KEY:
        logger.warning(
            "OPENROUTER_API_KEY not set. The application will not be able to "
            "generate AI responses. Please set this in your .env file."
        )
        return False

    if len(OPENROUTER_API_KEY) < 10:
        logger.warning("OPENROUTER_API_KEY appears to be invalid (too short).")
        return False

    logger.info(f"API configured with model: {OPENROUTER_MODEL}")
    return True

# =============================================================================
# MODEL PARAMETERS
# =============================================================================

# LSTM Model Configuration
LSTM_HIDDEN_SIZE = 32  # Reduced for speed
LSTM_NUM_LAYERS = 1    # Single layer for speed
LSTM_DROPOUT = 0.1
LSTM_LEARNING_RATE = 0.01

# Training Configuration
SEQUENCE_LENGTH = 30   # Days of history for prediction (reduced for speed)
PREDICTION_HORIZON = 30  # Days to predict
TRAINING_EPOCHS = 5    # Fast training
BATCH_SIZE = 64

# Portfolio Optimization
MAX_WEIGHT_PER_STOCK = 0.5  # Maximum 50% allocation per stock
RISK_FREE_RATE = 0.02       # 2% risk-free rate for Sharpe calculation

# =============================================================================
# EGX 33 SHARIAH INDEX TICKERS
# =============================================================================

EGX33_TICKERS = [
    "ADIB.CA", "SAUD.CA", "AMOC.CA", "ACGC.CA", "ARCC.CA", "CLHO.CA",
    "SUGR.CA", "EFID.CA", "EFIH.CA", "EGAL.CA", "EGTS.CA", "ETRS.CA",
    "EMFD.CA", "FAIT.CA", "FAITA.CA", "ISPH.CA", "ICFC.CA", "JUFO.CA",
    "LCSW.CA", "MASR.CA", "MCQE.CA", "ATQA.CA", "MTIE.CA", "EGAS.CA",
    "OLFI.CA", "ORAS.CA", "ORHD.CA", "ORWE.CA", "PHDC.CA", "SKPC.CA",
    "OCDI.CA", "TMGH.CA", "ETEL.CA", "RMDA.CA"
]

# Ticker to Company Name mapping
TICKER_NAMES = {
    "ADIB.CA": "Abu Dhabi Islamic Bank",
    "SAUD.CA": "Al Baraka Bank Egypt",
    "AMOC.CA": "Alexandria Mineral Oils",
    "ACGC.CA": "Arab Cotton Ginning",
    "ARCC.CA": "Arabian Cement",
    "CLHO.CA": "Cleopatra Hospital",
    "SUGR.CA": "Delta Sugar",
    "EFID.CA": "Edita Food Industries",
    "EFIH.CA": "E-Finance",
    "EGAL.CA": "Egypt Aluminum",
    "EGTS.CA": "Egyptian Tourism Resorts",
    "ETRS.CA": "Egyptian Transport (EGYTRANS)",
    "EMFD.CA": "Emaar Misr",
    "FAIT.CA": "Faisal Islamic Bank (EGP)",
    "FAITA.CA": "Faisal Islamic Bank (USD)",
    "ISPH.CA": "Ibnsina Pharma",
    "ICFC.CA": "International Co. For Fertilizers",
    "JUFO.CA": "Juhayna Food Industries",
    "LCSW.CA": "Lecico Egypt",
    "MASR.CA": "Madinet Masr (MNHD)",
    "MCQE.CA": "Misr Cement Qena",
    "ATQA.CA": "Misr National Steel (Ataqa)",
    "MTIE.CA": "MM Group",
    "EGAS.CA": "Natural Gas & Mining (Egypt Gas)",
    "OLFI.CA": "Obour Land",
    "ORAS.CA": "Orascom Construction",
    "ORHD.CA": "Orascom Development",
    "ORWE.CA": "Oriental Weavers",
    "PHDC.CA": "Palm Hills",
    "SKPC.CA": "Sidi Kerir Petrochemicals",
    "OCDI.CA": "SODIC",
    "TMGH.CA": "TMG Holding",
    "ETEL.CA": "Telecom Egypt",
    "RMDA.CA": "Rameda"
}

# Ticker sectors for additional context
TICKER_SECTORS = {
    "ADIB.CA": "Banking",
    "SAUD.CA": "Banking",
    "FAIT.CA": "Banking",
    "FAITA.CA": "Banking",
    "AMOC.CA": "Energy",
    "SKPC.CA": "Energy",
    "EGAS.CA": "Energy",
    "ACGC.CA": "Textiles",
    "ORWE.CA": "Textiles",
    "ARCC.CA": "Construction Materials",
    "MCQE.CA": "Construction Materials",
    "CLHO.CA": "Healthcare",
    "ISPH.CA": "Healthcare",
    "RMDA.CA": "Healthcare",
    "SUGR.CA": "Food & Beverage",
    "EFID.CA": "Food & Beverage",
    "JUFO.CA": "Food & Beverage",
    "OLFI.CA": "Food & Beverage",
    "EFIH.CA": "Financial Services",
    "EGAL.CA": "Industrial",
    "ATQA.CA": "Industrial",
    "ICFC.CA": "Industrial",
    "LCSW.CA": "Industrial",
    "EGTS.CA": "Tourism",
    "ETRS.CA": "Transportation",
    "EMFD.CA": "Real Estate",
    "MASR.CA": "Real Estate",
    "ORHD.CA": "Real Estate",
    "PHDC.CA": "Real Estate",
    "OCDI.CA": "Real Estate",
    "TMGH.CA": "Real Estate",
    "MTIE.CA": "Technology",
    "ORAS.CA": "Construction",
    "ETEL.CA": "Telecommunications"
}

# =============================================================================
# RISK PROFILES
# =============================================================================

RISK_PROFILES = {
    "conservative": {
        "max_volatility": 0.02,
        "description": "Low-risk, stable stocks with consistent performance",
        "target_stocks": 8  # Number of stocks to select
    },
    "moderate": {
        "max_volatility": 0.05,
        "description": "Balanced mix of stability and growth potential",
        "target_stocks": 6
    },
    "aggressive": {
        "max_volatility": 1.0,
        "description": "Higher risk stocks with greater growth potential",
        "target_stocks": 5
    }
}

# =============================================================================
# FEATURE CONFIGURATION
# =============================================================================

# Feature columns for the LSTM model
FEATURE_COLUMNS = [
    "Open", "High", "Low", "Close", "Volume",
    "Daily_Return", "Volatility_30d", "SMA_50", "SMA_200"
]

# Minimal features for fast training
FAST_FEATURE_COLUMNS = ["Close", "Daily_Return", "Volatility_30d"]

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger.info(f"Logging configured at {LOG_LEVEL} level")

# =============================================================================
# VALIDATION
# =============================================================================

def validate_data_path() -> bool:
    """Check if the data file exists."""
    data_path = Path(DATA_PATH)
    if not data_path.exists():
        logger.error(f"Data file not found: {DATA_PATH}")
        return False
    logger.info(f"Data file found: {DATA_PATH}")
    return True

def validate_config() -> dict:
    """
    Validate all configuration on startup.
    Returns a dict with validation results.
    """
    results = {
        "api_valid": validate_api_config(),
        "data_valid": validate_data_path(),
        "prompts_dir_exists": PROMPTS_DIR.exists()
    }

    if not results["prompts_dir_exists"]:
        logger.warning(f"Prompts directory not found: {PROMPTS_DIR}")

    results["all_valid"] = all(results.values())
    return results
