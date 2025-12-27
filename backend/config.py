"""
ShariahFolio Configuration Module
Contains API configuration, model parameters, and EGX 33 ticker list.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "xiaomi/mimo-v2-flash:free"  # Free model

# Model Parameters
LSTM_HIDDEN_SIZE = 64
LSTM_NUM_LAYERS = 2
SEQUENCE_LENGTH = 60  # Days of history for prediction
PREDICTION_HORIZON = 30  # Days to predict

# EGX 33 Shariah Index Tickers
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

# Risk Profile Mapping (volatility thresholds)
RISK_PROFILES = {
    "conservative": {"max_volatility": 0.02, "description": "Low-risk, stable stocks"},
    "moderate": {"max_volatility": 0.05, "description": "Balanced risk-return"},
    "aggressive": {"max_volatility": 1.0, "description": "Higher risk, higher potential returns"}
}

# Feature columns for the model
FEATURE_COLUMNS = ["Open", "High", "Low", "Close", "Volume", "Daily_Return", "Volatility_30d", "SMA_50", "SMA_200"]

# Data path
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "egx33_shariah_advanced_features.csv")
