#!/bin/bash

set -e

echo "=== Explainable Step-Up Decisioning System - Production Launch ==="

# Create directories
mkdir -p /var/lib/explainable
mkdir -p /etc/explainable/models
mkdir -p /etc/explainable/config/templates
mkdir -p /var/log/explainable

# Copy configuration
cp config/templates/graph_reason_templates.yaml /etc/explainable/config/templates/
cp config/production_config.json /etc/explainable/config/

# Generate models if they don't exist
if [ ! -f /etc/explainable/models/tabular_model.pkl ]; then
    echo "Generating models..."
    python scripts/generate_models.py --output-dir /etc/explainable/models
fi

# Initialize data store
if [ ! -f /var/lib/explainable/outcome_store.json ]; then
    echo "{}" > /var/lib/explainable/outcome_store.json
fi

# Initialize with sample data (optional)
if [ "$1" == "--seed" ]; then
    echo "Seeding with sample data..."
    python init_data.py
fi

# Start services
echo "Starting services..."
docker-compose up -d

echo "=== Production System Running ==="
echo "API: http://localhost:5000"
echo "Health: http://localhost:5000/health"

# Wait for API to be ready
sleep 5

# Generate sample decisions (if in dev mode)
if [ "$1" == "--seed" ]; then
    echo "Generating sample decisions..."
    python scripts/produce_decisions.py
fi

echo "=== Launch Complete ==="