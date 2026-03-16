"""
Render.com entry point - starts only the FastAPI app.
"""
import os
import uvicorn

# Get port from Render environment
port = int(os.environ.get("PORT", "10000"))

if __name__ == "__main__":
    print(f"Starting Anti-Berojgar API on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
