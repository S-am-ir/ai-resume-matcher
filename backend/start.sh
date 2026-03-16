#!/bin/bash

# Render.com startup script
# Use PORT env variable from Render, default to 10000
PORT="${PORT:-10000}"

echo "Starting Anti-Berojgar API on port $PORT..."

# Start the FastAPI app directly
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
