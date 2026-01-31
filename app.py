"""FastAPI web server for NYC Subway Agent."""
import os
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.agent import chat, clear_history

# API key for basic auth
API_KEY = os.environ.get("API_KEY", "brian2026subway")

app = FastAPI(title="MTAGPT - NYC Subway Assistant")

# Templates
templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


def verify_key(key: str = Query(None)):
    """Verify API key."""
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, key: str = Query(None)):
    """Serve the main chat interface."""
    verify_key(key)
    return templates.TemplateResponse("index.html", {"request": request, "key": key})


@app.post("/chat")
async def chat_endpoint(req: ChatRequest, key: str = Query(None)):
    """Handle chat messages."""
    verify_key(key)
    try:
        response = await chat(req.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
async def clear_endpoint(key: str = Query(None)):
    """Clear conversation history."""
    verify_key(key)
    clear_history()
    return {"status": "cleared"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
