# Financial Data Streaming System - Configuration Management Guide

Complete configuration management solution with environment support, AWS Systems Manager integration, and secrets management.

## 🏗️ Architecture Overview

The configuration management system provides:

1. **Centralized Configuration** - Single source of truth for all settings
2. **Environment Support** - Development, staging, and production configurations
3. **AWS Integration** - Systems Manager Parameter Store and Secrets Manager
4. **Security** - Secure handling of sensitive configuration
5. **Validation** - Configuration validation and error checking
6. **CLI Tools** - Command-line interface for configuration management

## 🔧 Configuration Structure

### Configuration Sections

```yaml
# Main configuration sections
environment: development
debug: true

database:
  mongodb_uri: "mongodb://localhost:27017/stockdata"
  mongodb_database: "stockdata"
  connection_timeout: 30000
  max_pool_size: 50
  retry_writes: true

api:
  alpha_vantage_api_key: "your-api-key"
  alpha_vantage_base_url: "https://www.alphavantage.co/query"
  api_rate_limit: 5
  request_timeout: 30
  max_retries: 3

aws:
  region: "us-east-2"
  sns_topic_arn: "arn:aws:sns:us-east-2:account:topic"
  use_iam_role: true

kafka:
  bootstrap_servers: "localhost:9092"
  topic: "stock-ticks"
  group_id: "financial-streaming-group"
  auto_offset_reset: "latest"
  enable_auto_commit: true

service:
  api_server_host: "0.0.0.0"
  api_server_port: 8000
  stream_receiver_host: "0.0.0.0"
  stream_receiver_port: 8002
  driver_host: "0.0.0.0"
  driver_port: 8001
  monitoring_host: "0.0.0.0"
  monitoring_port: 8080

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "logs/app.log"
  max_file_size: 10485760
  backup_count: 5

security:
  enable_ssl: false
  ssl_cert_path: ""
  ssl_key_path: ""
  cors_origins: ["http://localhost:3000"]
  api_key_required: false
  jwt_secret: "your-jwt-secret"

monitoring:
  health_check_interval: 30
  metrics_collection_interval: 60
  alert_check_interval: 60
  response_time_warning: 2.0
  response_time_error: 5.0
  error_rate_warning: 0.05
  error_rate_error: 0.10
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd config
pip install -r requirements.txt
```

### 2. Basic Configuration Usage

```python
from config.config_manager import get_config, get_service_config

# Get full configuration
config = get_config()
print(f"Environment: {config.environment}")
print(f"MongoDB URI: {config.database.mongodb_uri}")

# Get service-specific configuration
api_config = get_service_config('api_server')
print(f"API Server Port: {api_config['port']}")
```

### 3. Configuration Management

```bash
# Show current configuration
# Configuration is managed through YAML files in the config/ directory
cat config/development.yaml

# Show configuration for specific service
# Edit the appropriate YAML file for service-specific settings

# Validate configuration
# Configuration validation is handled automatically by the config manager

# Export configuration
# Configuration is stored in YAML format in config/ directory
```

## 🔄 Configuration Sources

The configuration system loads settings from multiple sources in order of priority:

### 1. Environment Variables (Highest Priority)

```bash
# Database
export MONGODB_URI="mongodb://localhost:27017/stockdata"
export MONGODB_DATABASE="stockdata"

# API
export ALPHA_VANTAGE_API_KEY="your-api-key"
export ALPHA_VANTAGE_BASE_URL="https://www.alphavantage.co/query"

# AWS
export AWS_REGION="us-east-2"
export SNS_TOPIC_ARN="arn:aws:sns:us-east-2:account:topic"

# Services
export API_SERVER_HOST="0.0.0.0"
export API_SERVER_PORT="8000"
export STREAM_RECEIVER_HOST="0.0.0.0"
export STREAM_RECEIVER_PORT="8002"

# Logging
export LOG_LEVEL="INFO"
export LOG_FILE_PATH="logs/app.log"

# Security
export ENABLE_SSL="false"
export API_KEY_REQUIRED="false"
export JWT_SECRET="your-jwt-secret"

# Monitoring
export HEALTH_CHECK_INTERVAL="30"
export METRICS_COLLECTION_INTERVAL="60"
```

### 2. Configuration Files

The system looks for configuration files in this order:

1. `config/config.yaml`
2. `config/config.yml`
3. `config/config.json`
4. `config/{environment}.yaml`
5. `config/{environment}.yml`
6. `{environment}.json`

### 3. AWS Systems Manager Parameter Store

For production environments, configuration can be stored in AWS Systems Manager:

```bash
# Setup AWS SSM parameters using AWS CLI
aws ssm put-parameter \
    --name "/financial-streaming/production/database/mongodb-uri" \
    --value "mongodb://prod-host:27017/stockdata" \
    --type "SecureString" \
    --region "us-east-2"

# Parameters are stored as:
/financial-streaming/production/database/mongodb-uri
/financial-streaming/production/api/alpha-vantage-key
/financial-streaming/production/aws/sns-topic-arn
/financial-streaming/production/kafka/bootstrap-servers
/financial-streaming/production/security/jwt-secret
```

### 4. AWS Secrets Manager

Sensitive configuration can be stored in AWS Secrets Manager:

```bash
# Secrets are stored as:
financial-streaming/production/secrets
financial-streaming/development/secrets
```

### 5. Default Values (Lowest Priority)

If no configuration is found, the system uses sensible defaults.

## 🛠️ Configuration Management

### Configuration Files

The system uses YAML configuration files located in the `config/` directory:

- `config/development.yaml` - Development environment settings
- `config/production.yaml` - Production environment settings
- `config/config_manager.py` - Configuration management logic

### Environment Variables

Configuration can be overridden using environment variables:

```bash
# Database
export MONGODB_URI="mongodb://localhost:27017/stockdata"
export MONGODB_DATABASE="stockdata"

# API
export ALPHA_VANTAGE_API_KEY="your-api-key"

# AWS
export AWS_REGION="us-east-2"
export SNS_TOPIC_ARN="arn:aws:sns:us-east-2:account:topic"

# Services
export API_SERVER_PORT="8000"
export STREAM_RECEIVER_PORT="8002"
export DRIVER_PORT="8001"
```

### AWS Systems Manager Setup

```bash
# Setup development environment
aws ssm put-parameter --name "/financial-streaming/development/database/mongodb-uri" --value "mongodb://localhost:27017/stockdata" --type "SecureString" --region "us-east-2"

# Setup production environment
aws ssm put-parameter --name "/financial-streaming/production/database/mongodb-uri" --value "mongodb://prod-host:27017/stockdata" --type "SecureString" --region "us-east-2"

# Setup both environments
# Run the above commands for both development and production

# Setup in different region
aws ssm put-parameter --name "/financial-streaming/production/database/mongodb-uri" --value "mongodb://prod-host:27017/stockdata" --type "SecureString" --region "us-west-2"
```

## 🔐 Security Configuration

### SSL/TLS Configuration

```yaml
security:
  enable_ssl: true
  ssl_cert_path: "/etc/ssl/certs/financial-streaming.crt"
  ssl_key_path: "/etc/ssl/private/financial-streaming.key"
```

### API Authentication

```yaml
security:
  api_key_required: true
  jwt_secret: "${JWT_SECRET}"  # Use environment variable
```

### CORS Configuration

```yaml
security:
  cors_origins:
    - "https://financial-streaming.example.com"
    - "https://dashboard.financial-streaming.example.com"
```

## 🌍 Environment-Specific Configuration

### Development Environment

```yaml
# config/development.yaml
environment: development
debug: true

database:
  mongodb_uri: "mongodb://localhost:27017/stockdata"

api:
  alpha_vantage_api_key: "dev-api-key"

security:
  enable_ssl: false
  api_key_required: false
  jwt_secret: "dev-secret-key-change-in-production"
```

### Production Environment

```yaml
# config/production.yaml
environment: production
debug: false

database:
  mongodb_uri: "${MONGODB_URI}"  # Use environment variable

api:
  alpha_vantage_api_key: "${ALPHA_VANTAGE_API_KEY}"

security:
  enable_ssl: true
  api_key_required: true
  jwt_secret: "${JWT_SECRET}"
```

## 🔄 AWS Integration

### Systems Manager Parameter Store

```python
# Setup parameters using AWS CLI or SDK
# Example using AWS CLI:
aws ssm put-parameter \
    --name "/production/database/mongodb-uri" \
    --value "mongodb://prod-host:27017/stockdata" \
    --type "SecureString" \
    --region "us-east-2"

aws ssm put-parameter \
    --name "/production/api/alpha-vantage-key" \
    --value "prod-api-key" \
    --type "SecureString" \
    --region "us-east-2"

aws ssm put-parameter \
    --name "/production/aws/sns-topic-arn" \
    --value "arn:aws:sns:us-east-2:account:topic" \
    --type "String" \
    --region "us-east-2"
```

### Secrets Manager

```python
# Create secrets
secrets = {
    "database": {
        "connection_timeout": "30000",
        "max_pool_size": "100"
    },
    "api": {
        "rate_limit": "5",
        "request_timeout": "30"
    },
    "security": {
        "jwt_secret": "super-secret-jwt-key"
    }
}

ssm_manager.create_secret("production", "secrets", secrets)
```

## ✅ Configuration Validation

### Automatic Validation

The configuration system automatically validates:

- Required fields (API keys, database URIs)
- Port ranges (1024-65535)
- SSL certificate paths when SSL is enabled
- Environment-specific requirements

### Manual Validation

```bash
# Validate configuration
# Configuration validation is handled automatically by the config manager
# Check the logs for any validation errors during startup

# Example validation checks:
# - Required fields (API keys, database URIs)
# - Port ranges (1024-65535)
# - SSL certificate paths when SSL is enabled
# - Environment-specific requirements
```

## 🔧 Integration with Services

### API Server Integration

```python
# ec2-api-server/main.py
from config.config_manager import get_service_config

config = get_service_config('api_server')

app = FastAPI()
app.run(
    host=config['host'],
    port=config['port']
)
```

### Stream Receiver Integration

```python
# ec2-stream-receiver/main.py
from config.config_manager import get_service_config

config = get_service_config('stream_receiver')

# Use configuration
kafka_config = config['kafka']
accumulo_config = config['accumulo']
```

### Monitoring Integration

```python
# monitoring/dashboard.py
from config.config_manager import get_service_config

config = get_service_config('monitoring')

# Use monitoring configuration
health_check_interval = config['monitoring']['health_check_interval']
```

## 🚀 Production Deployment

### Environment Variables

```bash
# Production environment variables
export ENVIRONMENT="production"
export MONGODB_URI="mongodb://prod-host:27017/stockdata"
export ALPHA_VANTAGE_API_KEY="prod-api-key"
export SNS_TOPIC_ARN="arn:aws:sns:us-east-2:account:topic"
export JWT_SECRET="super-secret-jwt-key"
export ENABLE_SSL="true"
export API_KEY_REQUIRED="true"
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Copy configuration
COPY config/ /app/config/

# Set environment
ENV ENVIRONMENT=production

# Run with configuration
CMD ["python", "main.py"]
```

### Kubernetes Integration

```yaml
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: financial-streaming-config
data:
  ENVIRONMENT: "production"
  MONGODB_URI: "mongodb://mongodb:27017/stockdata"
  KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"

---
# kubernetes/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: financial-streaming-secrets
type: Opaque
data:
  ALPHA_VANTAGE_API_KEY: <base64-encoded-key>
  JWT_SECRET: <base64-encoded-secret>
```

## 🔍 Troubleshooting

### Common Issues

#### Configuration Not Loading

```bash
# Check configuration path
cat config/development.yaml

# Check environment
echo $ENVIRONMENT
```

#### AWS Integration Issues

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check SSM parameters
aws ssm get-parameter --name "/financial-streaming/development/database/mongodb-uri" --region "us-east-2"
```

#### Validation Errors

```bash
# Validate configuration
# Check application logs for validation errors during startup

# Fix validation errors
# Update the appropriate YAML configuration file or environment variables
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

from config.config_manager import get_config_manager
config_manager = get_config_manager()
```

## 📚 Best Practices

### 1. Environment Separation

- Use different configuration files for each environment
- Use environment variables for sensitive data
- Never commit production secrets to version control

### 2. Security

- Use AWS Secrets Manager for sensitive configuration
- Rotate API keys and secrets regularly
- Use IAM roles instead of access keys when possible

### 3. Validation

- Always validate configuration before deployment
- Use configuration validation in CI/CD pipelines
- Monitor configuration changes

### 4. Documentation

- Document all configuration parameters
- Keep configuration examples updated
- Use clear naming conventions

---

**🎉 Your Financial Data Streaming System now has comprehensive configuration management!**

The configuration system provides centralized, secure, and environment-aware configuration management with full AWS integration and validation. 