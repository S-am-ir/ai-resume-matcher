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

# Railway expects the app on port 8080
EXPOSE 8080

# Run the app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
