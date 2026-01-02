FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install PyTorch CPU version explicitly (to avoid 2GB download)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for models and data
RUN mkdir -p /app/models/best_models /app/data/raw

# Expose port
EXPOSE 8000

# Command will be specified in docker-compose.yml for flexibility
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
