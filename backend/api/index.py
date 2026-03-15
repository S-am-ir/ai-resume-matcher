# Vercel Serverless Entry Point for FastAPI
import os
import sys

# Add backend to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Set environment before any imports
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Import the FastAPI app from main.py
from main import app

# Export the app for Vercel to use
# Vercel's Python runtime auto-detects FastAPI apps
module = sys.modules[__name__]
setattr(module, "__version__", app.version)
