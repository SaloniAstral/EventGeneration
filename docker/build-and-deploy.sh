#!/bin/bash

# Financial Data Streaming System - Docker Build and Deploy Script
# This script builds and deploys all EC2 services using Docker

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="financial-data-streaming"
DOCKER_REGISTRY=""
AWS_REGION=${AWS_REGION:-"us-east-2"}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if AWS CLI is installed (for production deployment)
    if ! command -v aws &> /dev/null; then
        print_warning "AWS CLI is not installed. Production deployment features will be limited."
    fi
    
    print_success "Prerequisites check completed"
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build API Server
    print_status "Building API Server image..."
    docker build -f ec2-api-server/Dockerfile -t ${PROJECT_NAME}-api-server:latest ./ec2-api-server
    
    # Build Driver
    print_status "Building Driver image..."
    docker build -f ec2-driver/Dockerfile -t ${PROJECT_NAME}-driver:latest ./ec2-driver
    
    # Build Stream Receiver
    print_status "Building Stream Receiver image..."
    docker build -f ec2-stream-receiver/Dockerfile -t ${PROJECT_NAME}-stream-receiver:latest ./ec2-stream-receiver
    
    print_success "All Docker images built successfully"
}

# Function to create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    cat > .env << EOF
# Financial Data Streaming System Environment Configuration

# AWS Configuration
AWS_REGION=${AWS_REGION}
SNS_TOPIC_ARN=${SNS_TOPIC_ARN:-"arn:aws:sns:us-east-2:000936194577:financial-data-events"}

# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY:-"AS0C2O859HMRJXVL"}

# MongoDB Configuration
MONGODB_URI=mongodb://admin:password123@mongodb:27017/stockdata?authSource=admin
MONGODB_DATABASE=stockdata

# Streaming Configuration
STOCK_THRESHOLD=${STOCK_THRESHOLD:-5}
TICK_INTERVAL=${TICK_INTERVAL:-1.0}

# Service URLs
API_SERVER_URL=http://localhost:8000
DRIVER_URL=http://localhost:8001
STREAM_RECEIVER_URL=http://localhost:8002

# Logging
LOG_LEVEL=INFO
EOF
    
    print_success "Environment file created: .env"
}

# Function to start services
start_services() {
    print_status "Starting services with Docker Compose..."
    
    # Create logs directory
    mkdir -p ../logs
    
    # Start services
    docker-compose up -d
    
    print_success "Services started successfully"
}

# Function to check service health
check_health() {
    print_status "Checking service health..."
    
    # Wait for services to start
    sleep 10
    
    # Check MongoDB
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        print_success "MongoDB is healthy"
    else
        print_error "MongoDB health check failed"
        return 1
    fi
    
    # Check API Server
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API Server is healthy"
    else
        print_warning "API Server health check failed (may still be starting)"
    fi
    
    # Check Stream Receiver
    if curl -f http://localhost:8002/health > /dev/null 2>&1; then
        print_success "Stream Receiver is healthy"
    else
        print_warning "Stream Receiver health check failed (may still be starting)"
    fi
    
    print_success "Health checks completed"
}

# Function to show service status
show_status() {
    print_status "Service Status:"
    echo ""
    
    # Docker Compose status
    docker-compose ps
    
    echo ""
    print_status "Service URLs:"
    echo "  API Server:     http://localhost:8000"
    echo "  Stream Receiver: http://localhost:8002"
    echo "  Nginx Proxy:    http://localhost:80"
    echo ""
    print_status "Health Check URLs:"
    echo "  API Server:     http://localhost:8000/health"
    echo "  Stream Receiver: http://localhost:8002/health"
    echo "  Nginx Status:   http://localhost/status"
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove images
    docker rmi ${PROJECT_NAME}-api-server:latest 2>/dev/null || true
    docker rmi ${PROJECT_NAME}-driver:latest 2>/dev/null || true
    docker rmi ${PROJECT_NAME}-stream-receiver:latest 2>/dev/null || true
    
    # Remove unused images
    docker image prune -f
    
    print_success "Cleanup completed"
}

# Function to show logs
show_logs() {
    print_status "Showing service logs..."
    docker-compose logs -f
}

# Function to show help
show_help() {
    echo "Financial Data Streaming System - Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build       Build all Docker images"
    echo "  start       Start all services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  status      Show service status"
    echo "  health      Check service health"
    echo "  logs        Show service logs"
    echo "  cleanup     Clean up Docker resources"
    echo "  deploy      Full deployment (build + start + health check)"
    echo "  help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  AWS_REGION              AWS region (default: us-east-2)"
    echo "  SNS_TOPIC_ARN           SNS topic ARN for events"
    echo "  ALPHA_VANTAGE_API_KEY   Alpha Vantage API key"
    echo "  STOCK_THRESHOLD         Minimum stocks for streaming (default: 5)"
    echo "  TICK_INTERVAL           Tick interval in seconds (default: 1.0)"
}

# Main script logic
case "${1:-help}" in
    "build")
        check_prerequisites
        build_images
        ;;
    "start")
        check_prerequisites
        create_env_file
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        start_services
        ;;
    "status")
        show_status
        ;;
    "health")
        check_health
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup
        ;;
    "deploy")
        check_prerequisites
        build_images
        create_env_file
        start_services
        check_health
        show_status
        ;;
    "help"|*)
        show_help
        ;;
esac 