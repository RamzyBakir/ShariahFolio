"""
ShariahFolio FastAPI Application
Main entry point with WebSocket chat endpoint and static file serving.
"""

import asyncio
from pathlib import Path
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .agent import PortfolioAgent
from .data_loader import get_data_loader
from .config import EGX33_TICKERS


# Store active connections and their agents
active_connections: Dict[str, tuple[WebSocket, PortfolioAgent]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - preload data on startup."""
    print("[START] Starting ShariahFolio...")
    
    # Preload data
    try:
        data_loader = get_data_loader()
        print(f"[OK] Loaded data for {len(data_loader.ticker_data)} tickers")
    except Exception as e:
        print(f"[WARN] Could not preload data: {e}")
    
    yield
    
    # Cleanup on shutdown
    print("[STOP] Shutting down ShariahFolio...")


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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ShariahFolio"}


# API info endpoint
@app.get("/api/info")
async def get_info():
    """Get API information and available tickers."""
    data_loader = get_data_loader()
    valid_tickers = data_loader.get_valid_tickers()
    
    return {
        "name": "ShariahFolio",
        "version": "1.0.0",
        "description": "AI-Powered Shariah-Compliant Portfolio Optimizer",
        "available_tickers": valid_tickers,
        "total_tickers": len(EGX33_TICKERS),
        "valid_tickers": len(valid_tickers)
    }


async def send_progress(websocket: WebSocket, message: str):
    """Send a progress update to the client."""
    try:
        await websocket.send_json({
            "type": "progress",
            "content": message
        })
    except:
        pass  # Ignore send errors


# WebSocket chat endpoint
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    
    # Create agent for this connection
    agent = PortfolioAgent()
    connection_id = str(id(websocket))
    active_connections[connection_id] = (websocket, agent)
    
    print(f"[CONNECT] New connection: {connection_id}")
    
    # Send welcome message
    welcome_message = """# Welcome to ShariahFolio

I'm your AI-powered investment advisor specializing in **Shariah-compliant Egyptian stocks** from the EGX 33 Index.

I can help you:
- Build an optimized investment portfolio
- Select stocks based on your risk tolerance
- Allocate your investment across multiple stocks

**To get started, tell me:**
1. How much would you like to invest?
2. Do you have specific stocks in mind, or would you prefer a risk-based recommendation?

Let's build your Halal portfolio together!"""
    
    await websocket.send_json({
        "type": "message",
        "content": welcome_message,
        "sender": "assistant"
    })
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                user_message = data.get("content", "")
                
                if not user_message.strip():
                    continue
                
                # Send typing indicator
                await websocket.send_json({
                    "type": "typing",
                    "status": True
                })
                
                try:
                    # Process with agent in thread pool
                    def run_agent():
                        return asyncio.run(agent.chat(user_message))
                    
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(None, run_agent)
                    
                    # Send response
                    await websocket.send_json({
                        "type": "message",
                        "content": response,
                        "sender": "assistant"
                    })
                    
                except Exception as e:
                    print(f"Error processing message: {e}")
                    import traceback
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "error",
                        "content": f"An error occurred: {str(e)}"
                    })
                
                finally:
                    # Stop typing indicator
                    await websocket.send_json({
                        "type": "typing",
                        "status": False
                    })
            
            elif data.get("type") == "reset":
                # Reset conversation
                agent.reset()
                await websocket.send_json({
                    "type": "system",
                    "content": "Conversation reset. How can I help you today?"
                })
    
    except WebSocketDisconnect:
        print(f"[DISCONNECT] Connection closed: {connection_id}")
    
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]


# Serve frontend static files
@app.get("/")
async def serve_index():
    """Serve the main HTML page."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(
        {"error": "Frontend not found. Please create frontend/index.html"},
        status_code=404
    )


# Mount static files for CSS and JS
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# Serve other frontend files directly
@app.get("/{filename:path}")
async def serve_static(filename: str):
    """Serve static frontend files."""
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
