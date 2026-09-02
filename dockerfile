FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories for data
RUN mkdir -p /var/lib/explainable
RUN mkdir -p /etc/explainable/models
RUN mkdir -p /etc/explainable/config/templates

# Expose ports
EXPOSE 5000

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "src.api.server:app"]