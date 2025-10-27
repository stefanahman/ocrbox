#!/bin/bash
#
# OCRBox Local Mode Test Script
# Quick test of OCR functionality
#

set -e

echo "========================================="
echo "OCRBox Local Mode Test"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Run scripts/setup.sh first."
    exit 1
fi

# Check if GEMINI_API_KEY is set
if ! grep -q "GEMINI_API_KEY=your_gemini_api_key" .env; then
    echo "✓ GEMINI_API_KEY appears to be configured"
else
    echo "❌ Please set GEMINI_API_KEY in .env file"
    exit 1
fi

# Ensure MODE is set to local
if ! grep -q "^MODE=local" .env; then
    echo "Setting MODE=local in .env..."
    sed -i.bak 's/^MODE=.*/MODE=local/' .env
    rm .env.bak 2>/dev/null || true
fi

echo "✓ Configuration verified"
echo ""

# Start the service
echo "Starting OCRBox in local mode..."
docker-compose up -d
echo "✓ Service started"
echo ""

# Wait a bit for startup
echo "Waiting for service to initialize..."
sleep 3

# Show logs
echo ""
echo "========================================="
echo "Service Logs (last 20 lines)"
echo "========================================="
docker-compose logs --tail=20
echo ""

echo "========================================="
echo "Test Instructions"
echo "========================================="
echo ""
echo "1. Add a screenshot or image to: data/watch/"
echo "   Example: cp ~/Pictures/screenshot.png data/watch/"
echo ""
echo "2. Watch the logs:"
echo "   docker-compose logs -f"
echo ""
echo "3. Check the output:"
echo "   cat data/output/screenshot.txt"
echo ""
echo "4. Archived images will be in: data/archive/"
echo ""
echo "To stop the service:"
echo "   docker-compose down"
echo ""

