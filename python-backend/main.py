# -*- coding: utf-8 -*-
"""
FastAPI Backend for Computer Control AI
Converted from Node.js/TypeScript to Python

⚠️ UWAGA! KRYTYCZNY KOMUNIKAT DOTYCZĄCY HARDCODOWANYCH API! ⚠️
NIE WOLNO CI USUWAĆ HARDCODE API NIE ŻYCZĘ SOBIE KURWA TEGO.
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json

from openai import AsyncOpenAI
from onkernel import Kernel

# Import our modules
from utils import DesktopManager
from chat_handler import handle_chat_stream

# ⚠️ HARDCODED API KEYS - DO NOT MODIFY! ⚠️
NVIDIA_API_KEY = "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"
NVIDIA_MODEL = "meta/llama-4-scout-17b-16e-instruct"
ONKERNEL_API_KEY = "sk_85dd38ea-b33f-45b5-bc33-0eed2357683a.t2lQgq3Lb6DamEGhcLiUgPa1jlx+1zD4BwAdchRHYgA"

# Initialize clients
kernel_client = Kernel(api_key=ONKERNEL_API_KEY)
nvidia_client = AsyncOpenAI(
    api_key=NVIDIA_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1"
)

# Initialize desktop manager
desktop_manager = DesktopManager(kernel_client)

# Create FastAPI app
app = FastAPI(
    title="Computer Control AI Backend",
    description="Python backend for AI-powered computer control",
    version="1.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "online",
        "service": "Computer Control AI Backend",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "kill_desktop": "/api/kill-desktop",
            "docs": "/docs"
        }
    }


@app.post("/api/chat")
async def handle_chat(request: Request):
    """
    Main chat endpoint - handles streaming AI responses with computer control
    
    CRITICAL: This endpoint maintains the EXACT LOOP LOGIC from the original TypeScript version
    """
    try:
        body = await request.json()
        messages = body.get("messages", [])
        sandbox_id = body.get("sandboxId")
        
        # Get or create desktop
        desktop = await desktop_manager.get_desktop(sandbox_id)
        
        # Create streaming response
        return StreamingResponse(
            handle_chat_stream(
                messages=messages,
                sandbox_id=desktop.session_id,
                desktop=desktop,
                kernel_client=kernel_client,
                nvidia_client=nvidia_client
            ),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Accel-Buffering": "no",
                "Transfer-Encoding": "chunked",
                "Connection": "keep-alive"
            }
        )
    except Exception as error:
        print(f"Error in chat endpoint: {error}")
        return JSONResponse(
            status_code=500,
            content={"error": str(error)}
        )


@app.post("/api/kill-desktop")
async def handle_kill_desktop(request: Request):
    """Kill desktop endpoint"""
    try:
        # Try to get sandboxId from query params first, then from body
        sandbox_id = request.query_params.get("sandboxId")
        
        if not sandbox_id:
            body = await request.json()
            sandbox_id = body.get("sandboxId")
        
        if not sandbox_id:
            return JSONResponse(
                status_code=400,
                content={"error": "No sandboxId provided"}
            )
        
        await desktop_manager.kill_desktop(sandbox_id)
        return {"message": "Desktop killed successfully"}
    
    except Exception as error:
        print(f"Failed to kill desktop: {error}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to kill desktop"}
        )


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("Computer Control AI - Python Backend")
    print("=" * 50)
    print("Starting server on http://0.0.0.0:5000")
    print("API Documentation: http://0.0.0.0:5000/docs")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
