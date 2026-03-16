# Hugging Face Spaces Docker Deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for frontend build
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*
RUN playwright install chromium

# Copy backend code
COPY backend/ ./backend/

# Copy frontend code and build
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN npm install && npm run build

# Create uploads directory
RUN mkdir -p /app/backend/uploads
RUN mkdir -p /app/backend/output

# Set environment variables
ENV PORT=7860
ENV PYTHONPATH=/app/backend

# Start both backend and serve frontend
WORKDIR /app/backend
CMD bash -c "uvicorn main:app --host 0.0.0.0 --port $PORT"
