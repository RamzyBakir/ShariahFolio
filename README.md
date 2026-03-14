<h1 align="center">
  <br>
  🕌 ShariahFolio
  <br>
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Maintained%3F-no-red.svg" alt="Maintenance">
  <img src="https://img.shields.io/badge/Status-Deprecated-orange" alt="Status">
</p>

This project was developed for a Deep Learning Class. 
**Please note:** This project is archived and is not being updated or supported.

<h4 align="center">AI-Powered Shariah-Compliant Portfolio Optimizer for EGX 33</h4>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#demo">Demo</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#project-structure">Project Structure</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-green.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-teal.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/PyTorch-2.0+-red.svg" alt="PyTorch">
  <img src="https://img.shields.io/badge/LangGraph-0.1+-purple.svg" alt="LangGraph">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
</p>

---

## 📋 Overview

**ShariahFolio** is a conversational AI application that helps users build optimized investment portfolios from Shariah-compliant Egyptian stocks listed on the EGX 33 Index. It combines natural language processing with deep learning-based stock prediction and modern portfolio theory to deliver personalized investment recommendations.

### Why ShariahFolio?

- 🕌 **Halal Investing**: All 34 stocks in the EGX 33 Shariah Index are pre-screened for Islamic compliance
- 🤖 **AI-Powered**: LSTM neural networks predict future returns based on historical patterns
- 🔧 **Tool-Based Architecture**: ReAct-style agent ensures accurate, non-hallucinated portfolio results
- 💬 **Conversational**: Chat naturally about your investment goals - no complex forms
- ⚡ **Real-time**: WebSocket-based communication for instant responses
- 📊 **Optimized**: Mean-Variance Optimization maximizes risk-adjusted returns

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Tool-Based Agent** | LangGraph ReAct agent uses explicit tools to guarantee accurate portfolio data |
| **LSTM Predictions** | Deep learning model analyzes historical patterns to predict returns |
| **Portfolio Optimization** | Mean-Variance Optimization with Sharpe ratio maximization |
| **Risk Profiling** | Conservative, moderate, and aggressive portfolio strategies |
| **Flexible Stock Selection** | Combine risk profiles with specific stock preferences |
| **Modern UI** | ChatGPT-style interface with dark/light modes |
| **Real-time Chat** | WebSocket-based communication with typing indicators |

---

## 🎬 Demo

### Starting a Conversation
```
User: I want to invest 100,000 EGP, moderate risk, needs to include ETEL.CA

ShariahFolio: 📊 Your Optimized Shariah Portfolio

Investment Amount: 100,000.00 EGP
Risk Profile: Moderate
Additional Stocks Included: ETEL.CA

| Ticker   | Company              | Sector           | Weight | Amount (EGP) |
|----------|----------------------|------------------|--------|--------------|
| ETEL.CA  | Telecom Egypt        | Telecommunications | 50.0%  | 50,000.00    |
| JUFO.CA  | Juhayna Food         | Food & Beverage  | 28.5%  | 28,528.58    |
| ORWE.CA  | Oriental Weavers     | Textiles         | 21.5%  | 21,471.42    |

Expected Return: 26.68%
Expected Volatility: 28.16% (High Risk)
Sharpe Ratio: 0.88 (Good risk-adjusted return)
Projected Value (1 year): ~126,680 EGP
```

### Modifying Your Portfolio
```
User: Actually, let's just invest in ETEL.CA alone

ShariahFolio: 📊 Single Stock Portfolio

Total Investment: 100,000 EGP

| Ticker   | Company       | Allocation | Amount     |
|----------|---------------|------------|------------|
| ETEL.CA  | Telecom Egypt | 100%       | 100,000 EGP|

Note: While ETEL.CA is a solid telecommunications company, 
concentrating your entire investment in one stock carries 
company-specific risk. Consider diversifying to reduce risk.
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                │
│              (HTML/CSS/JS + WebSocket Client)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Server                             │
│                   (WebSocket Endpoint)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                  LangGraph ReAct Agent                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Agent Node (LLM)                      │  │
│  │         Decides when to call tools or respond            │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                            │                                   │
│                            ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Tool Executor                         │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                │  │
│  │  │optimize_portfolio│  │ get_stock_info │                │  │
│  │  └─────────────────┘  └─────────────────┘                │  │
│  │  ┌─────────────────┐  ┌─────────────────────────┐        │  │
│  │  │list_avail_stocks│  │get_stocks_by_risk_profile│       │  │
│  │  └─────────────────┘  └─────────────────────────┘        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬───────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────────────┐
│    LSTM Model        │      │   Mean-Variance Optimization     │
│  (Return Prediction) │      │     (Sharpe Maximization)        │
└──────────────────────┘      └──────────────────────────────────┘
```

### Tool-Based Architecture

ShariahFolio uses a **ReAct (Reasoning + Acting)** pattern where the LLM explicitly calls tools to perform actions, ensuring:

- ✅ **No Hallucinated Data**: Portfolio allocations always come from the actual optimizer
- ✅ **Reliable Results**: Tools validate inputs and return structured data
- ✅ **Traceable Actions**: Every tool call is logged for debugging

### Available Tools

| Tool | Description |
|------|-------------|
| `optimize_portfolio` | Creates optimized portfolio using LSTM + Mean-Variance Optimization |
| `get_stock_info` | Retrieves detailed information about a specific stock |
| `list_available_stocks` | Lists all 34 Shariah-compliant stocks with prices/volatility |
| `get_stocks_by_risk_profile` | Shows which stocks match a given risk level |

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- OpenRouter API key ([Get one free here](https://openrouter.ai/))

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/RamzyBakir/shariahfolio.git
   cd shariahfolio
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your OpenRouter API key
   # OPENROUTER_API_KEY=your_api_key_here
   ```

5. **Run the application**
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Open in browser**
   ```
   http://localhost:8000
   ```

---

## 💬 Usage

### Basic Conversation Flow

1. **State your investment amount**
   > "I want to invest 50,000 EGP"

2. **Choose your approach**
   - **Risk profile only**: "I'm a conservative investor"
   - **Specific stocks only**: "I want ETEL.CA and EFIH.CA"
   - **Combined**: "Moderate risk, but make sure to include ETEL.CA" ✨ **New!**

3. **Receive your portfolio** with allocations, metrics, and explanations

4. **Request modifications**
   > "Can you add JUFO.CA to this portfolio?"
   > "Make it more aggressive"
   > "What if I invest 100,000 instead?"

### Risk Profiles

| Profile | Description | Volatility Range |
|---------|-------------|------------------|
| **Conservative** | Stable, low-volatility stocks (banks, utilities) | < 2% daily |
| **Moderate** | Balanced risk-return trade-off | 2-5% daily |
| **Aggressive** | High growth potential, higher risk | > 5% daily |

### Combining Risk Profiles with Specific Stocks

You can now request a risk-based portfolio while ensuring specific stocks are included:

```
User: I want 100,000 EGP, moderate risk, but include ETEL.CA and ARCC.CA

ShariahFolio: [Analyzes moderate-risk stocks + ETEL.CA + ARCC.CA]
              [Returns optimized allocation across all selected stocks]
```

---

## 📁 Project Structure

```
shariahfolio/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & WebSocket
│   ├── agent.py             # LangGraph ReAct agent with tools
│   ├── tools.py             # LangChain tools for portfolio operations
│   ├── portfolio_model.py   # LSTM model & Mean-Variance optimization
│   ├── data_loader.py       # Data preprocessing & caching
│   ├── config.py            # Configuration & constants
│   ├── prompts/             # External prompt templates
│   │   ├── consultant_system.md
│   │   ├── consultant_post_portfolio.md
│   │   ├── consultant_error_context.md
│   │   └── summary_template.md
│   └── utils/
│       ├── __init__.py
│       └── prompt_loader.py # Prompt loading utilities
├── frontend/
│   ├── index.html           # Chat interface
│   ├── styles.css           # Modern styling
│   └── app.js               # WebSocket client
├── data/
│   └── egx33_shariah_advanced_features.csv
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📊 Supported Stocks

All **34 EGX 33 Shariah Index** tickers are supported:

<details>
<summary>Click to expand full ticker list</summary>

| Ticker | Company | Sector |
|--------|---------|--------|
| ADIB.CA | Abu Dhabi Islamic Bank | Banking |
| SAUD.CA | Al Baraka Bank Egypt | Banking |
| FAIT.CA | Faisal Islamic Bank (EGP) | Banking |
| FAITA.CA | Faisal Islamic Bank (USD) | Banking |
| ETEL.CA | Telecom Egypt | Telecommunications |
| EFIH.CA | E-Finance | Financial Services |
| AMOC.CA | Alexandria Mineral Oils | Energy |
| SKPC.CA | Sidi Kerir Petrochemicals | Energy |
| EGAS.CA | Natural Gas & Mining | Energy |
| CLHO.CA | Cleopatra Hospital | Healthcare |
| ISPH.CA | Ibnsina Pharma | Healthcare |
| RMDA.CA | Rameda | Healthcare |
| JUFO.CA | Juhayna Food Industries | Food & Beverage |
| EFID.CA | Edita Food Industries | Food & Beverage |
| OLFI.CA | Obour Land | Food & Beverage |
| SUGR.CA | Delta Sugar | Food & Beverage |
| EMFD.CA | Emaar Misr | Real Estate |
| PHDC.CA | Palm Hills | Real Estate |
| OCDI.CA | SODIC | Real Estate |
| TMGH.CA | TMG Holding | Real Estate |
| MASR.CA | Madinet Masr (MNHD) | Real Estate |
| ORHD.CA | Orascom Development | Real Estate |
| ARCC.CA | Arabian Cement | Construction Materials |
| MCQE.CA | Misr Cement Qena | Construction Materials |
| ORAS.CA | Orascom Construction | Construction |
| EGAL.CA | Egypt Aluminum | Industrial |
| ATQA.CA | Misr National Steel | Industrial |
| ICFC.CA | International Co. For Fertilizers | Industrial |
| LCSW.CA | Lecico Egypt | Industrial |
| ACGC.CA | Arab Cotton Ginning | Textiles |
| ORWE.CA | Oriental Weavers | Textiles |
| EGTS.CA | Egyptian Tourism Resorts | Tourism |
| ETRS.CA | Egyptian Transport | Transportation |
| MTIE.CA | MM Group | Technology |

</details>

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Required |
| `OPENROUTER_MODEL` | LLM model to use | `xiaomi/mimo-v2-flash:free` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Model Parameters (config.py)

```python
# LSTM Configuration
LSTM_HIDDEN_SIZE = 32      # LSTM hidden layer size
LSTM_NUM_LAYERS = 1        # Number of LSTM layers
SEQUENCE_LENGTH = 30       # Days of history for prediction
PREDICTION_HORIZON = 30    # Days to predict forward
TRAINING_EPOCHS = 5        # Training epochs per model

# Portfolio Constraints
MAX_WEIGHT_PER_STOCK = 0.5 # Maximum 50% allocation per stock
RISK_FREE_RATE = 0.02      # 2% risk-free rate for Sharpe calculation
```

### Agent Safety Limits

```python
MAX_TOOL_CALLS_PER_REQUEST = 3  # Prevents infinite tool calling loops
MAX_MESSAGE_HISTORY = 30        # Prevents token overflow
```

---

## 🧪 Technical Details

### LSTM Model
- **Architecture**: Single-layer LSTM (32 hidden units)
- **Input**: 30-day sequences of (Close, Daily_Return, Volatility_30d)
- **Output**: Predicted daily return
- **Training**: On-demand per ticker, 5 epochs, ~0.5-2s per ticker
- **Caching**: Trained models are cached for faster subsequent requests

### Portfolio Optimization
- **Method**: Mean-Variance Optimization (Markowitz)
- **Objective**: Maximize Sharpe Ratio
- **Constraints**: 
  - Weights sum to 1
  - Maximum 50% per stock
  - No short selling (weights ≥ 0)

### Tool-Based Agent
- **Framework**: LangGraph with LangChain tools
- **Pattern**: ReAct (Reasoning + Acting)
- **Safety**: Tool call limits, recursion limits, input validation
- **Logging**: Comprehensive logging of all tool calls and results

---

## 🔧 Recent Improvements (v2.0)

- ✅ **Tool-Based Architecture**: Switched from LLM-only responses to explicit tool calls
- ✅ **Combined Stock Selection**: Can now combine risk profiles with specific tickers
- ✅ **Input Normalization**: Handles various ticker formats (ETEL, etel.ca, "ETEL.CA")
- ✅ **JSON String Handling**: Robust parsing of LLM tool call arguments
- ✅ **Infinite Loop Prevention**: Tool call counter prevents runaway loops
- ✅ **Single-Stock Portfolios**: Properly handles portfolios with just one stock
- ✅ **Enhanced Error Messages**: Clear, actionable error messages for users
- ✅ **External Prompts**: System prompts stored in markdown files for easy editing

---

## ⚠️ Disclaimer

ShariahFolio provides **AI-generated investment suggestions** based on historical data and machine learning predictions. This is **NOT financial advice**.

- Past performance does not guarantee future results
- Always consult with a qualified financial advisor
- Do your own research before making investment decisions
- The developers are not responsible for any financial losses

---

<p align="center">
  Built with ❤️ for Halal investing
  <br>
  <sub>© 2024 ShariahFolio</sub>
</p>
