# -*- coding: utf-8 -*-
"""
FastAPI Backend for Computer Control AI
Converted from Node.js/TypeScript to Python

⚠️ UWAGA! KRYTYCZNY KOMUNIKAT DOTYCZĄCY HARDCODOWANYCH API! ⚠️
NIE WOLNO CI USUWAĆ HARDCODE API NIE ŻYCZĘ SOBIE KURWA TEGO.
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import AsyncIterator, Dict, Any, List, Optional
import re
from datetime import datetime
import base64

from openai import AsyncOpenAI
from onkernel import Kernel

# ⚠️ HARDCODED API KEYS - DO NOT MODIFY! ⚠️
NVIDIA_API_KEY = "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"
NVIDIA_MODEL = "meta/llama-4-scout-17b-16e-instruct"
ONKERNEL_API_KEY = "sk_85dd38ea-b33f-45b5-bc33-0eed2357683a.t2lQgq3Lb6DamEGhcLiUgPa1jlx+1zD4BwAdchRHYgA"

# Resolution settings for desktop sandbox (4:3 aspect ratio)
RESOLUTION = {"x": 1024, "y": 768}

# Initialize clients
kernel_client = Kernel(api_key=ONKERNEL_API_KEY)
nvidia_client = AsyncOpenAI(
    api_key=NVIDIA_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1"
)

app = FastAPI()

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
