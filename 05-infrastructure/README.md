# 05-INFRASTRUCTURE
## System Configuration, Database, Docker & Deployment

### 🎯 **Purpose**
This folder contains all the infrastructure components needed to run the complete system: Docker configuration, database connections, shared utilities, and deployment scripts.

### 📁 **Key Components**

#### 🐳 **Docker & Deployment**
- `docker-compose-simple.yml` - Complete system deployment
- `requirements.txt` - Python dependencies
- `quick_start.sh` - One-command system startup
- `update_aws_credentials.sh` - AWS credentials setup

#### 🗄️ **Database**
- `database/mongodb_manager.py` - MongoDB connection management
- `database/models.py` - Data models and schemas

#### ⚙️ **Configuration**
- `config/config_manager.py` - Environment configuration
- `config/database_config.py` - Database settings

#### 🔧 **Shared Utilities**
- `shared/connection_manager.py` - Inter-service communication
- `shared/kafka_client.py` - Kafka connection utilities
- `shared/logger.py` - Centralized logging

#### 📡 **Events**
- `events/sns_event_listener.py` - SNS event handling
- `events/event_handlers.py` - Event processing logic

### 🚀 **Quick Start Commands**
```bash
# Setup AWS credentials
./update_aws_credentials.sh

# Start entire system
docker-compose -f docker-compose-simple.yml up -d

# Check system status
docker-compose -f docker-compose-simple.yml ps
```

### 📊 **Infrastructure Status**
- ✅ 8 containers running and healthy
- ✅ MongoDB, Redis, Kafka operational  
- ✅ All network connections working
- ✅ AWS credentials configured
