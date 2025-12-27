# 🕌 ShariahFolio

**AI-Powered Shariah-Compliant Portfolio Optimizer for EGX 33**

ShariahFolio is a conversational AI application that helps users build optimized investment portfolios from Shariah-compliant Egyptian stocks on the EGX 33 Index.

![ShariahFolio](https://img.shields.io/badge/ShariahFolio-v1.0.0-green)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red)

## ✨ Features

- 🤖 **AI-Powered Conversations**: Chat naturally about your investment goals
- 📈 **LSTM Predictions**: Deep learning model predicts future stock returns
- ⚖️ **Portfolio Optimization**: Mean-Variance Optimization maximizes Sharpe ratio
- 🕌 **Shariah-Compliant**: All 34 EGX 33 Shariah Index stocks supported
- 🎨 **Modern UI**: ChatGPT-style interface with dark/light modes
- ⚡ **Real-time**: WebSocket-based communication

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    FastAPI      │────▶│   LangGraph     │
│   (HTML/JS)     │◀────│   WebSocket     │◀────│     Agent       │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                              ┌─────────────────────┐
                                              │   LSTM Model +      │
                                              │   Portfolio Opt.    │
                                              └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenRouter API key ([Get one here](https://openrouter.ai/))

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd islam-invest
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   # Copy the example env file
   copy .env.example .env
   
   # Edit .env and add your OpenRouter API key
   ```

5. **Run the application:**
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Open in browser:**
   ```
   http://localhost:8000
   ```

## 💬 Usage

1. **Start a conversation** with ShariahFolio
2. **Tell it your investment amount** (e.g., "I want to invest 100,000 EGP")
3. **Specify your preference:**
   - Specific stocks: "I'm interested in ETEL.CA and EFIH.CA"
   - Risk profile: "I'm a conservative investor"
4. **Receive your optimized portfolio** with allocation percentages

### Example Conversation

> **You**: I have 50,000 EGP to invest and I'm looking for moderate risk.
>
> **ShariahFolio**: I'll create a moderate-risk portfolio for you...
>
> | Stock | Weight | Amount |
> |-------|--------|--------|
> | ETEL.CA | 30% | 15,000 |
> | EFIH.CA | 25% | 12,500 |
> | ...

## 📁 Project Structure

```
islam-invest/
├── backend/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── agent.py          # LangGraph conversational agent
│   ├── portfolio_model.py # LSTM + optimization
│   ├── data_loader.py    # Data preprocessing
│   └── config.py         # Configuration
├── frontend/
│   ├── index.html        # Chat interface
│   ├── styles.css        # Modern styling
│   └── app.js            # WebSocket client
├── data/
│   └── egx33_shariah_advanced_features.csv
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Configuration

Edit `.env` to configure:

```env
OPENROUTER_API_KEY=your_key_here
```

## 📊 Supported Stocks

All 34 EGX 33 Shariah Index tickers:

| | | | |
|---|---|---|---|
| ADIB.CA | SAUD.CA | AMOC.CA | ACGC.CA |
| ARCC.CA | CLHO.CA | SUGR.CA | EFID.CA |
| EFIH.CA | EGAL.CA | EGTS.CA | ETRS.CA |
| EMFD.CA | FAIT.CA | FAITA.CA | ISPH.CA |
| ICFC.CA | JUFO.CA | LCSW.CA | MASR.CA |
| MCQE.CA | ATQA.CA | MTIE.CA | EGAS.CA |
| OLFI.CA | ORAS.CA | ORHD.CA | ORWE.CA |
| PHDC.CA | SKPC.CA | OCDI.CA | TMGH.CA |
| ETEL.CA | RMDA.CA | | |

## ⚠️ Disclaimer

ShariahFolio provides AI-generated investment suggestions based on historical data and machine learning predictions. This is **not financial advice**. Always consult with a qualified financial advisor before making investment decisions.

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with ❤️ for Halal investing
