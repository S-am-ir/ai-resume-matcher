# Vercel Serverless Entry Point for FastAPI
import os
import sys

# Add backend to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Set environment before any imports
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Import the original app from main.py
from main import app as original_app

# Create new app that catches all routes
app = FastAPI()

# Mount the original app at /api
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def api_catch_all(request: Request, path: str):
    # Forward request to original app
    return await original_app(request.scope, request.receive, request._send)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catch_all(request: Request, path: str):
    # Forward to original app
    return await original_app(request.scope, request.receive, request._send)
