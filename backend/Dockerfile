FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml first for better caching
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy all backend code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Railway sets PORT env var - use it
ENV PORT=8080

# Run the app - use Railway's PORT env var
CMD bash -c "uvicorn main:app --host 0.0.0.0 --port $PORT"
