# Vercel Serverless Entry Point for FastAPI
import os
import sys

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment before any imports
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the main app from main.py
from main import app

# Add CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel requires this handler for ASGI apps
def handler(request):
    return app
