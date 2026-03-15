FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Make start script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Run the app using start script
CMD ["./start.sh"]
