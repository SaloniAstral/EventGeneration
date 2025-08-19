#!/bin/bash

# Quick Start Script - Fast deployment without rebuilding
# Use this for daily development

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] $1${NC}"
}

# Check if images exist
if ! docker images | grep -q "financial-api-server"; then
    warn "Images not found. Running full build first..."
    ./deploy_local.sh
    exit 0
fi

log "🚀 Quick Start - Using existing images"

cd docker

# Just start services (no rebuild)
log "Starting services..."
docker-compose up -d

log "✅ Services started!"
echo ""
echo "🌐 API Server:     http://localhost:8000"
echo "🌐 Stream Receiver: http://localhost:8002"
echo "🌐 Driver:         http://localhost:8001"
echo ""
echo "📋 Commands:"
echo "  View logs:       docker-compose logs -f"
echo "  Stop:            docker-compose down"
echo "  Status:          docker-compose ps" 