#!/bin/bash

# Render.com startup script
# Use PORT env variable from Render, default to 8080
PORT=${PORT:-8080}

echo "Starting Anti-Berojgar API on port $PORT..."

# Start the FastAPI app
exec uvicorn main:app --host 0.0.0.0 --port $PORT
