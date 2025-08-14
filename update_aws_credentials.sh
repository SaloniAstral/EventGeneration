#!/bin/bash

# Script to update AWS credentials across the system
# This script updates AWS credentials in all necessary places

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get AWS credentials from user
echo -e "${YELLOW}Please enter your AWS credentials:${NC}"
echo ""
read -p "AWS Access Key ID: " AWS_ACCESS_KEY_ID
read -p "AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
read -p "AWS Session Token (press Enter if none): " AWS_SESSION_TOKEN
read -p "AWS Region [us-east-2]: " AWS_REGION_INPUT
AWS_REGION=${AWS_REGION_INPUT:-us-east-2}

# Validate region input
if [ "$AWS_REGION" = "yes" ] || [ "$AWS_REGION" = "y" ]; then
    AWS_REGION="us-east-2"
fi

# Update docker/.env
echo -e "${GREEN}Updating docker/.env...${NC}"
if [ -f "docker/.env" ]; then
    # Update existing file
    sed -i '' "s|AWS_ACCESS_KEY_ID=.*|AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}|g" docker/.env
    sed -i '' "s|AWS_SECRET_ACCESS_KEY=.*|AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}|g" docker/.env
    sed -i '' "s|AWS_SESSION_TOKEN=.*|AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}|g" docker/.env
    sed -i '' "s|AWS_REGION=.*|AWS_REGION=${AWS_REGION}|g" docker/.env
else
    # Create new file
    cat > docker/.env << EOF
# AWS Configuration
AWS_REGION=${AWS_REGION}
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}
SNS_TOPIC_ARN=arn:aws:sns:us-east-2:000936194577:stock-data-events

# Other configurations will be added by deploy_local.sh
EOF
fi

# Update database/mongodb_local_config.env
echo -e "${GREEN}Updating database/mongodb_local_config.env...${NC}"
if [ -f "database/mongodb_local_config.env" ]; then
    sed -i '' "s|AWS_ACCESS_KEY_ID=.*|AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}|g" database/mongodb_local_config.env
    sed -i '' "s|AWS_SECRET_ACCESS_KEY=.*|AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}|g" database/mongodb_local_config.env
    sed -i '' "s|AWS_SESSION_TOKEN=.*|AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}|g" database/mongodb_local_config.env
    sed -i '' "s|AWS_REGION=.*|AWS_REGION=${AWS_REGION}|g" database/mongodb_local_config.env
fi

# Export to current shell
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
export AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}
export AWS_REGION=${AWS_REGION}

echo -e "${GREEN}AWS credentials have been updated in:${NC}"
echo "1. docker/.env"
echo "2. database/mongodb_local_config.env"
echo "3. Current shell environment"
echo ""
echo -e "${YELLOW}To use these credentials in your current shell, run:${NC}"
echo "source update_aws_credentials.sh"