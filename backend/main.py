"""
ShariahFolio FastAPI Application
Main entry point with WebSocket chat endpoint and static file serving.

Features:
- WebSocket-based real-time chat
- Static file serving for frontend
- Health check and API info endpoints
- Proper logging and error handling
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .agent import PortfolioAgent
from .data_loader import get_data_loader
from .config import (
    EGX33_TICKERS,
    setup_logging,
    validate_config,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Store active connections and their agents
active_connections: Dict[str, tuple[WebSocket, PortfolioAgent]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - initialize on startup, cleanup on shutdown."""
    logger.info("=" * 60)
    logger.info("Starting ShariahFolio...")
    logger.info("=" * 60)

    # Validate configuration
    config_status = validate_config()

    if not config_status["api_valid"]:
        logger.warning(
            "API key not configured. Chat functionality will be limited. "
            "Please set OPENROUTER_API_KEY in your .env file."
        )
    else:
        logger.info(f"Using LLM model: {OPENROUTER_MODEL}")

    if not config_status["data_valid"]:
        logger.error("Data file not found. The application may not function correctly.")

    # Preload data
    try:
        data_loader = get_data_loader()
        valid_tickers = data_loader.get_valid_tickers()
        logger.info(f"Loaded data for {len(data_loader.ticker_data)} tickers")
        logger.info(f"Valid tickers for optimization: {len(valid_tickers)}")
    except Exception as e:
        logger.exception(f"Failed to preload data: {e}")

    logger.info("=" * 60)
    logger.info("ShariahFolio is ready!")
    logger.info("=" * 60)

    yield

    # Cleanup on shutdown
    logger.info("Shutting down ShariahFolio...")

    # Close all active connections
    for conn_id, (ws, agent) in list(active_connections.items()):
        try:
            await ws.close()
        except Exception:
            pass

    active_connections.clear()
    logger.info("Cleanup complete. Goodbye!")


# Create FastAPI app
app = FastAPI(
    title="ShariahFolio",
    description="AI-Powered Shariah-Compliant Portfolio Optimizer for EGX 33",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Get paths
BACKEND_DIR = Path(__file__).parent
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    data_loader = get_data_loader()
    valid_tickers = data_loader.get_valid_tickers()

    return {
        "status": "healthy",
        "service": "ShariahFolio",
        "version": "1.0.0",
        "api_configured": bool(OPENROUTER_API_KEY),
        "data_loaded": len(data_loader.ticker_data) > 0,
        "valid_tickers_count": len(valid_tickers),
        "active_connections": len(active_connections)
    }


@app.get("/api/info")
async def get_info():
    """Get API information and available tickers."""
    data_loader = get_data_loader()
    valid_tickers = data_loader.get_valid_tickers()

    return {
        "name": "ShariahFolio",
        "version": "1.0.0",
        "description": "AI-Powered Shariah-Compliant Portfolio Optimizer",
        "model": OPENROUTER_MODEL,
        "available_tickers": valid_tickers,
        "total_tickers": len(EGX33_TICKERS),
        "valid_tickers": len(valid_tickers),
        "features": [
            "LSTM-based return prediction",
            "Mean-Variance Portfolio Optimization",
            "Risk profile-based stock selection",
            "Conversational AI interface"
        ]
    }


@app.get("/api/tickers")
async def get_tickers():
    """Get list of available tickers with details."""
    from .config import TICKER_NAMES, TICKER_SECTORS

    data_loader = get_data_loader()
    valid_tickers = data_loader.get_valid_tickers()
    volatilities = data_loader.get_ticker_volatility()
    latest_prices = data_loader.get_latest_prices(valid_tickers)

    tickers_info = []
    for ticker in valid_tickers:
        tickers_info.append({
            "ticker": ticker,
            "name": TICKER_NAMES.get(ticker, ticker),
            "sector": TICKER_SECTORS.get(ticker, "Unknown"),
            "volatility": volatilities.get(ticker),
            "latest_price": latest_prices.get(ticker)
        })

    return {
        "count": len(tickers_info),
        "tickers": tickers_info
    }


async def send_message(websocket: WebSocket, msg_type: str, content: str, **kwargs):
    """Send a message to the WebSocket client with error handling."""
    try:
        message = {"type": msg_type, "content": content, **kwargs}
        await websocket.send_json(message)
    except Exception as e:
        logger.warning(f"Failed to send message: {e}")


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()

    # Create agent for this connection
    agent = PortfolioAgent()
    connection_id = str(id(websocket))
    active_connections[connection_id] = (websocket, agent)

    logger.info(f"New WebSocket connection: {connection_id}")

    # Send welcome message
    welcome_message = """# Welcome to ShariahFolio! 🕌📈

I'm your AI-powered investment advisor specializing in **Shariah-compliant Egyptian stocks** from the EGX 33 Index.

I can help you:
- 📊 Build an optimized investment portfolio
- 🎯 Select stocks based on your risk tolerance
- 💰 Allocate your investment across multiple stocks

**To get started, tell me:**
1. How much would you like to invest? (in EGP)
2. Do you have specific stocks in mind, or would you prefer a risk-based recommendation?

Let's build your Halal portfolio together! ✨"""

    await send_message(websocket, "message", welcome_message, sender="assistant")

    try:
        while True:
            # Receive message from client
            try:
                data = await websocket.receive_json()
            except Exception as e:
                logger.warning(f"Failed to receive JSON: {e}")
                break

            msg_type = data.get("type")

            if msg_type == "message":
                user_message = data.get("content", "").strip()

                if not user_message:
                    continue

                logger.info(f"[{connection_id}] User: {user_message[:100]}...")

                # Send typing indicator
                await send_message(websocket, "typing", "", status=True)

                try:
                    # Process with agent in thread pool to avoid blocking
                    def run_agent():
                        return asyncio.run(agent.chat(user_message))

                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(None, run_agent)

                    logger.info(f"[{connection_id}] Assistant: {response[:100]}...")

                    # Send response
                    await send_message(websocket, "message", response, sender="assistant")

                except Exception as e:
                    logger.exception(f"Error processing message: {e}")
                    error_msg = (
                        "I encountered an error while processing your request. "
                        "This might be due to a temporary issue. Please try again."
                    )
                    await send_message(websocket, "error", error_msg)

                finally:
                    # Stop typing indicator
                    await send_message(websocket, "typing", "", status=False)

            elif msg_type == "reset":
                # Reset conversation
                agent.reset()
                logger.info(f"[{connection_id}] Conversation reset")
                await send_message(
                    websocket,
                    "system",
                    "Conversation reset. How can I help you build a new portfolio?"
                )

            elif msg_type == "ping":
                # Keepalive ping
                await send_message(websocket, "pong", "")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.exception(f"WebSocket error: {e}")

    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]
        logger.info(f"Connection cleanup complete: {connection_id}")


# Serve frontend static files
@app.get("/")
async def serve_index():
    """Serve the main HTML page."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    logger.warning("Frontend index.html not found")
    return JSONResponse(
        {
            "error": "Frontend not found",
            "message": "Please ensure frontend/index.html exists"
        },
        status_code=404
    )


# Mount static files for CSS and JS
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
else:
    logger.warning(f"Frontend directory not found: {FRONTEND_DIR}")


# Serve other frontend files directly
@app.get("/{filename:path}")
async def serve_static(filename: str):
    """Serve static frontend files."""
    # Prevent directory traversal
    if ".." in filename:
        return JSONResponse({"error": "Invalid path"}, status_code=400)

    file_path = FRONTEND_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)

    # Default to index for SPA routing
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return JSONResponse({"error": "Not found"}, status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
