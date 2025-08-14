#!/bin/bash

# Financial Data Streaming System - Production Deployment Script
# This script deploys the entire system to AWS ECS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-production}
REGION=${2:-us-east-2}
STACK_NAME="financial-streaming-${ENVIRONMENT}"

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
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it first."
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker first."
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials are not configured. Please run 'aws configure' first."
    fi
    
    # Check if we're in the right region
    CURRENT_REGION=$(aws configure get region)
    if [ "$CURRENT_REGION" != "$REGION" ]; then
        warn "Current AWS region is $CURRENT_REGION, but deployment region is $REGION"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Deployment cancelled"
        fi
    fi
    
    log "Prerequisites check passed"
}

# Get VPC and subnet information
get_network_info() {
    log "Getting network information..."
    
    # Get default VPC
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
    if [ "$VPC_ID" == "None" ]; then
        error "No default VPC found. Please specify a VPC ID."
    fi
    
    # Get subnets
    PUBLIC_SUBNET_1=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" --query 'Subnets[0].SubnetId' --output text)
    PUBLIC_SUBNET_2=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" --query 'Subnets[1].SubnetId' --output text)
    PRIVATE_SUBNET_1=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=false" --query 'Subnets[0].SubnetId' --output text)
    PRIVATE_SUBNET_2=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=false" --query 'Subnets[1].SubnetId' --output text)
    
    if [ "$PUBLIC_SUBNET_1" == "None" ] || [ "$PUBLIC_SUBNET_2" == "None" ] || [ "$PRIVATE_SUBNET_1" == "None" ] || [ "$PRIVATE_SUBNET_2" == "None" ]; then
        error "Could not find required subnets. Please ensure you have at least 2 public and 2 private subnets."
    fi
    
    log "VPC ID: $VPC_ID"
    log "Public Subnets: $PUBLIC_SUBNET_1, $PUBLIC_SUBNET_2"
    log "Private Subnets: $PRIVATE_SUBNET_1, $PRIVATE_SUBNET_2"
}

# Build and push Docker images
build_and_push_images() {
    log "Building and pushing Docker images..."
    
    # Get ECR login token
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com
    
    # Build and push API Server
    log "Building API Server image..."
    docker build -t financial-streaming-api-server:$ENVIRONMENT $PROJECT_ROOT/ec2_api_server
    docker tag financial-streaming-api-server:$ENVIRONMENT $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/financial-streaming-api-server-$ENVIRONMENT:latest
    docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/financial-streaming-api-server-$ENVIRONMENT:latest
    
    # Build and push Stream Receiver
    log "Building Stream Receiver image..."
    docker build -t financial-streaming-stream-receiver:$ENVIRONMENT $PROJECT_ROOT/ec2_stream_receiver
    docker tag financial-streaming-stream-receiver:$ENVIRONMENT $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/financial-streaming-stream-receiver-$ENVIRONMENT:latest
    docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/financial-streaming-stream-receiver-$ENVIRONMENT:latest
    
    # Build and push Driver
    log "Building Driver image..."
    docker build -t financial-streaming-driver:$ENVIRONMENT $PROJECT_ROOT/ec2_driver
    docker tag financial-streaming-driver:$ENVIRONMENT $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/financial-streaming-driver-$ENVIRONMENT:latest
    docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/financial-streaming-driver-$ENVIRONMENT:latest
    
    # Build and push Monitoring
    log "Building Monitoring image..."
    docker build -t financial-streaming-monitoring:$ENVIRONMENT $PROJECT_ROOT/monitoring
    docker tag financial-streaming-monitoring:$ENVIRONMENT $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/financial-streaming-monitoring-$ENVIRONMENT:latest
    docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/financial-streaming-monitoring-$ENVIRONMENT:latest
    
    log "All images built and pushed successfully"
}

# Deploy ECS cluster
deploy_ecs_cluster() {
    log "Deploying ECS cluster..."
    
    # Deploy cluster stack
    aws cloudformation deploy \
        --template-file $SCRIPT_DIR/ecs-cluster.yaml \
        --stack-name ${STACK_NAME}-cluster \
        --parameter-overrides \
            Environment=$ENVIRONMENT \
            VpcId=$VPC_ID \
            PublicSubnet1=$PUBLIC_SUBNET_1 \
            PublicSubnet2=$PUBLIC_SUBNET_2 \
            PrivateSubnet1=$PRIVATE_SUBNET_1 \
            PrivateSubnet2=$PRIVATE_SUBNET_2 \
            InstanceType=t3.medium \
            MinSize=2 \
            MaxSize=10 \
            DesiredCapacity=2 \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION
    
    # Get stack outputs
    CLUSTER_NAME=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' --output text)
    ALB_ARN=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerArn`].OutputValue' --output text)
    TASK_EXECUTION_ROLE_ARN=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECSTaskExecutionRoleArn`].OutputValue' --output text)
    TASK_ROLE_ARN=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECSTaskRoleArn`].OutputValue' --output text)
    ECR_API_SERVER_URI=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryAPIServerURI`].OutputValue' --output text)
    ECR_STREAM_RECEIVER_URI=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryStreamReceiverURI`].OutputValue' --output text)
    ECR_DRIVER_URI=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryDriverURI`].OutputValue' --output text)
    ECR_MONITORING_URI=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryMonitoringURI`].OutputValue' --output text)
    
    log "ECS cluster deployed successfully"
    log "Cluster name: $CLUSTER_NAME"
    log "ALB ARN: $ALB_ARN"
}

# Deploy ECS services
deploy_ecs_services() {
    log "Deploying ECS services..."
    
    # Deploy services stack
    aws cloudformation deploy \
        --template-file $SCRIPT_DIR/ecs-services.yaml \
        --stack-name ${STACK_NAME}-services \
        --parameter-overrides \
            Environment=$ENVIRONMENT \
            ECSClusterName=$CLUSTER_NAME \
            ApplicationLoadBalancerArn=$ALB_ARN \
            ECSTaskExecutionRoleArn=$TASK_EXECUTION_ROLE_ARN \
            ECSTaskRoleArn=$TASK_ROLE_ARN \
            ECRRepositoryAPIServerURI=$ECR_API_SERVER_URI \
            ECRRepositoryStreamReceiverURI=$ECR_STREAM_RECEIVER_URI \
            ECRRepositoryDriverURI=$ECR_DRIVER_URI \
            ECRRepositoryMonitoringURI=$ECR_MONITORING_URI \
            VpcId=$VPC_ID \
            PrivateSubnet1=$PRIVATE_SUBNET_1 \
            PrivateSubnet2=$PRIVATE_SUBNET_2 \
            APIServerDesiredCount=2 \
            StreamReceiverDesiredCount=2 \
            DriverDesiredCount=1 \
            MonitoringDesiredCount=1 \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION
    
    log "ECS services deployed successfully"
}

# Wait for services to be stable
wait_for_services() {
    log "Waiting for services to be stable..."
    
    # Get service names
    API_SERVER_SERVICE=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-services --query 'Stacks[0].Outputs[?OutputKey==`APIServerServiceName`].OutputValue' --output text)
    STREAM_RECEIVER_SERVICE=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-services --query 'Stacks[0].Outputs[?OutputKey==`StreamReceiverServiceName`].OutputValue' --output text)
    DRIVER_SERVICE=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-services --query 'Stacks[0].Outputs[?OutputKey==`DriverServiceName`].OutputValue' --output text)
    MONITORING_SERVICE=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-services --query 'Stacks[0].Outputs[?OutputKey==`MonitoringServiceName`].OutputValue' --output text)
    
    # Wait for each service
    for service in "$API_SERVER_SERVICE" "$STREAM_RECEIVER_SERVICE" "$DRIVER_SERVICE" "$MONITORING_SERVICE"; do
        log "Waiting for service $service to be stable..."
        aws ecs wait services-stable \
            --cluster $CLUSTER_NAME \
            --services $service \
            --region $REGION
        log "Service $service is stable"
    done
    
    log "All services are stable"
}

# Get deployment information
get_deployment_info() {
    log "Getting deployment information..."
    
    # Get ALB DNS name
    ALB_DNS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerDNS`].OutputValue' --output text)
    
    # Get service URLs
    API_SERVER_URL="http://$ALB_DNS"
    STREAM_RECEIVER_URL="http://$ALB_DNS:8002"
    DRIVER_URL="http://$ALB_DNS:8001"
    MONITORING_URL="http://$ALB_DNS:8080"
    
    log "Deployment completed successfully!"
    echo
    echo "=== DEPLOYMENT INFORMATION ==="
    echo "Environment: $ENVIRONMENT"
    echo "Region: $REGION"
    echo "ECS Cluster: $CLUSTER_NAME"
    echo "Application Load Balancer: $ALB_DNS"
    echo
    echo "=== SERVICE ENDPOINTS ==="
    echo "API Server: $API_SERVER_URL"
    echo "Stream Receiver: $STREAM_RECEIVER_URL"
    echo "Driver: $DRIVER_URL"
    echo "Monitoring Dashboard: $MONITORING_URL"
    echo
    echo "=== HEALTH CHECK ENDPOINTS ==="
    echo "API Server Health: $API_SERVER_URL/health"
    echo "Stream Receiver Health: $STREAM_RECEIVER_URL/health"
    echo "Driver Health: $DRIVER_URL/health"
    echo "Monitoring Health: $MONITORING_URL/health"
    echo
    echo "=== API ENDPOINTS ==="
    echo "Stock Data: $API_SERVER_URL/api/v1/stocks"
    echo "Search Stocks: $API_SERVER_URL/api/v1/search"
    echo "Stream Status: $STREAM_RECEIVER_URL/api/v1/stream/status"
    echo "Monitoring Dashboard: $MONITORING_URL/dashboard"
    echo
    echo "=== MONITORING ==="
    echo "CloudWatch Logs: /ecs/financial-streaming-$ENVIRONMENT"
    echo "ECS Console: https://console.aws.amazon.com/ecs/home?region=$REGION#/clusters/$CLUSTER_NAME"
    echo "ALB Console: https://console.aws.amazon.com/ec2/v2/home?region=$REGION#LoadBalancer:loadBalancerArn=$ALB_ARN"
}

# Test deployment
test_deployment() {
    log "Testing deployment..."
    
    # Get ALB DNS name
    ALB_DNS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-cluster --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerDNS`].OutputValue' --output text)
    
    # Test health endpoints
    log "Testing health endpoints..."
    
    # API Server health
    if curl -f -s "$ALB_DNS/health" > /dev/null; then
        log "✅ API Server health check passed"
    else
        warn "❌ API Server health check failed"
    fi
    
    # Stream Receiver health
    if curl -f -s "$ALB_DNS:8002/health" > /dev/null; then
        log "✅ Stream Receiver health check passed"
    else
        warn "❌ Stream Receiver health check failed"
    fi
    
    # Driver health
    if curl -f -s "$ALB_DNS:8001/health" > /dev/null; then
        log "✅ Driver health check passed"
    else
        warn "❌ Driver health check failed"
    fi
    
    # Monitoring health
    if curl -f -s "$ALB_DNS:8080/health" > /dev/null; then
        log "✅ Monitoring health check passed"
    else
        warn "❌ Monitoring health check failed"
    fi
    
    log "Deployment testing completed"
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    
    # Remove local Docker images
    docker rmi financial-streaming-api-server:$ENVIRONMENT 2>/dev/null || true
    docker rmi financial-streaming-stream-receiver:$ENVIRONMENT 2>/dev/null || true
    docker rmi financial-streaming-driver:$ENVIRONMENT 2>/dev/null || true
    docker rmi financial-streaming-monitoring:$ENVIRONMENT 2>/dev/null || true
    
    log "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting Financial Data Streaming System deployment"
    log "Environment: $ENVIRONMENT"
    log "Region: $REGION"
    log "Stack Name: $STACK_NAME"
    
    # Check prerequisites
    check_prerequisites
    
    # Get network information
    get_network_info
    
    # Build and push images
    build_and_push_images
    
    # Deploy ECS cluster
    deploy_ecs_cluster
    
    # Deploy ECS services
    deploy_ecs_services
    
    # Wait for services to be stable
    wait_for_services
    
    # Test deployment
    test_deployment
    
    # Get deployment information
    get_deployment_info
    
    # Cleanup
    cleanup
    
    log "Deployment completed successfully!"
}

# Handle script arguments
case "${1:-production}" in
    production|staging|development)
        main
        ;;
    help|--help|-h)
        echo "Usage: $0 [environment] [region]"
        echo
        echo "Environments:"
        echo "  production  - Deploy to production (default)"
        echo "  staging     - Deploy to staging"
        echo "  development - Deploy to development"
        echo
        echo "Regions:"
        echo "  us-east-2   - US East (Ohio) (default)"
        echo "  us-west-2   - US West (Oregon)"
        echo "  eu-west-1   - Europe (Ireland)"
        echo
        echo "Examples:"
        echo "  $0                    # Deploy to production in us-east-2"
        echo "  $0 staging            # Deploy to staging in us-east-2"
        echo "  $0 production us-west-2  # Deploy to production in us-west-2"
        ;;
    *)
        error "Invalid environment: $1. Use 'help' for usage information."
        ;;
esac 