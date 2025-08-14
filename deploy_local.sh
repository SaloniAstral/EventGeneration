#!/bin/bash

# Financial Data Streaming System - Local Deployment Script
# This script deploys the system locally using Docker

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/docker"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker first."
    fi
    
    log "Prerequisites check passed"
}

# Create environment file
create_env_file() {
    log "Creating environment file..."
    
    if [ ! -f "$DOCKER_DIR/.env" ]; then
        cat > "$DOCKER_DIR/.env" << EOF
# Financial Data Streaming System - Environment Variables

# AWS Configuration
AWS_REGION=us-east-2
SNS_TOPIC_ARN=arn:aws:sns:us-east-2:123456789012:stock-data-events
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_SESSION_TOKEN=

# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=AS0C2O859HMRJXVL

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_NAME=stock-ticks
KAFKA_GROUP_ID=financial-streaming-group

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Service Configuration
STOCK_THRESHOLD=5
TICK_INTERVAL=1.0
LOG_LEVEL=INFO
EOF
        log "Environment file created: $DOCKER_DIR/.env"
        warn "Please update the AWS credentials in the .env file"
    else
        log "Environment file already exists"
    fi
}

# Build and start services
deploy_services() {
    log "Building and starting services..."
    
    cd "$DOCKER_DIR"
    
    # Stop any existing containers
    log "Stopping existing containers..."
    docker-compose down --remove-orphans
    
    # Check if images exist
    if docker images | grep -q "financial-api-server"; then
        log "Using existing images (fast mode)"
        docker-compose up -d
    else
        log "Building Docker images (first time only)..."
        docker-compose build
        docker-compose up -d
    fi
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service status
    log "Checking service status..."
    docker-compose ps
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check if all services are running
    if docker-compose ps | grep -q "Up"; then
        log "✅ All services are running"
    else
        error "❌ Some services failed to start"
    fi
    
    # Test API endpoints
    log "Testing API endpoints..."
    
    # Test API Server
    if curl -f http://localhost:8000/health &> /dev/null; then
        log "✅ API Server is responding"
    else
        warn "⚠️ API Server is not responding"
    fi
    
    # Test Stream Receiver
    if curl -f http://localhost:8002/health &> /dev/null; then
        log "✅ Stream Receiver is responding"
    else
        warn "⚠️ Stream Receiver is not responding"
    fi
    
    # Test MongoDB
    if docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        log "✅ MongoDB is responding"
    else
        warn "⚠️ MongoDB is not responding"
    fi
    
    # Test Kafka
    if docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; then
        log "✅ Kafka is responding"
    else
        warn "⚠️ Kafka is not responding"
    fi
    
    # Test Redis
    if docker-compose exec redis redis-cli ping &> /dev/null; then
        log "✅ Redis is responding"
    else
        warn "⚠️ Redis is not responding"
    fi
}

# Show service URLs
show_service_urls() {
    log "Service URLs:"
    echo ""
    echo "🌐 API Server:     http://localhost:8000"
    echo "🌐 Stream Receiver: http://localhost:8002"
    echo "🌐 Driver:         http://localhost:8001"
    echo "🌐 Nginx:          http://localhost:80"
    echo "📊 MongoDB:        mongodb://localhost:27017"
    echo "📊 Kafka:          localhost:9092"
    echo "📊 Redis:          localhost:6379"
    echo "📊 Zookeeper:      localhost:2181"
    echo ""
    echo "📋 Useful Commands:"
    echo "  View logs:       docker-compose logs -f"
    echo "  Stop services:   docker-compose down"
    echo "  Restart:         docker-compose restart"
    echo "  Status:          docker-compose ps"
    echo ""
}

# Main deployment function
main() {
    log "🚀 Starting Financial Data Streaming System deployment..."
    
    check_prerequisites
    create_env_file
    deploy_services
    verify_deployment
    show_service_urls
    
    log "🎉 Deployment completed successfully!"
    log "The system is now running locally."
}

# Run main function
main "$@" 