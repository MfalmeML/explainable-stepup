#!/bin/bash

set -e

echo "========================================="
echo "Explainable Step-Up Decisioning System"
echo "Complete Production Deployment"
echo "========================================="

# 1. Environment setup
echo "[1/8] Setting up environment..."
mkdir -p /var/lib/explainable
mkdir -p /etc/explainable/models
mkdir -p /etc/explainable/config/templates
mkdir -p /var/log/explainable
mkdir -p /var/run/explainable

# 2. Copy configuration
echo "[2/8] Copying configuration..."
cp config/templates/graph_reason_templates.yaml /etc/explainable/config/templates/
cp config/production_config.json /etc/explainable/config/

# 3. Generate models
echo "[3/8] Generating models..."
python scripts/generate_models.py --output-dir /etc/explainable/models

# 4. Initialize data store
echo "[4/8] Initializing data store..."
echo '{"_system_initialized": true, "_initialized_at": "'$(date -Iseconds)'"}' > /var/lib/explainable/outcome_store.json

# 5. Build Docker images
echo "[5/8] Building Docker images..."
docker build -t explainable-api:latest .
docker build -t explainable-consumer:latest -f Dockerfile.consumer .

# 6. Run database migrations (if any)
echo "[6/8] Running migrations..."
python scripts/migrate_store.py --store /var/lib/explainable/outcome_store.json

# 7. Start services
echo "[7/8] Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# 8. Verify deployment
echo "[8/8] Verifying deployment..."
sleep 10
python scripts/verify_complete.py

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "API: http://localhost:5000"
echo "Health: http://localhost:5000/health"
echo "Logs: /var/log/explainable/"
echo "========================================="