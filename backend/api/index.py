# Vercel Serverless Entry Point
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import asyncpg
import base64
import uuid
import asyncio
from typing import Optional, List, Dict, Any
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db
from config import settings
from agent.graph import build_graph

# Allow HTTP traffic for local dev
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Create temp directory for resume uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes from main.py
from main import router
app.include_router(router)

def handler(request):
    return app
