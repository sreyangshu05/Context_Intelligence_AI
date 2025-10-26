#!/bin/bash

set -e

echo "Running Contract Intelligence API Tests..."
echo "=========================================="

if [ ! -d "app" ]; then
    echo "Error: Must run from project root directory"
    exit 1
fi

echo ""
echo "1. Running unit tests..."
pytest tests/ -v

echo ""
echo "2. Checking API health..."
response=$(curl -s http://localhost:8000/healthz || echo '{"status":"not running"}')
status=$(echo $response | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$status" = "healthy" ]; then
    echo "✓ API is healthy"
else
    echo "⚠ API is not running. Start with: docker-compose up -d"
fi

echo ""
echo "3. Checking OpenAPI docs..."
if curl -s http://localhost:8000/openapi.json > /dev/null 2>&1; then
    echo "✓ OpenAPI documentation available at http://localhost:8000/docs"
else
    echo "⚠ API documentation not accessible"
fi

echo ""
echo "=========================================="
echo "Tests complete!"
