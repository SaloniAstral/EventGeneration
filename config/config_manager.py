#!/usr/bin/env python3
"""
Configuration Management System for Financial Data Streaming
Provides centralized configuration management with environment support,
AWS Systems Manager integration, and secrets management.
"""

import os
import json
import logging
import boto3
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml
from botocore.exceptions import ClientError, NoCredentialsError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    mongodb_uri: str = "mongodb://localhost:27017/stockdata"
    mongodb_database: str = "stockdata"
    connection_timeout: int = 30000
    max_pool_size: int = 100
    retry_writes: bool = True

@dataclass
class APIConfig:
    """API configuration"""
    alpha_vantage_api_key: str = ""
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    api_rate_limit: int = 5  # requests per minute
    request_timeout: int = 30
    max_retries: int = 3

@dataclass
class AWSConfig:
    """AWS configuration"""
    region: str = "us-east-2"
    sns_topic_arn: str = ""
    access_key_id: str = ""
    secret_access_key: str = ""
    session_token: str = ""
    use_iam_role: bool = True

@dataclass
class KafkaConfig:
    """Kafka configuration"""
    bootstrap_servers: str = "localhost:9092"
    topic: str = "stock-ticks"
    group_id: str = "financial-streaming-group"
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True

@dataclass
class AccumuloConfig:
    """Accumulo configuration"""
    instance_name: str = "stockdata"
    zookeeper_hosts: str = "localhost:2181"
    username: str = "root"
    password: str = ""
    table_name: str = "stock_ticks"

@dataclass
class ServiceConfig:
    """Service configuration"""
    api_server_host: str = "0.0.0.0"
    api_server_port: int = 8000
    stream_receiver_host: str = "0.0.0.0"
    stream_receiver_port: int = 8002
    driver_host: str = "0.0.0.0"
    driver_port: int = 8001
    monitoring_host: str = "0.0.0.0"
    monitoring_port: int = 8080

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_ssl: bool = False
    ssl_cert_path: str = ""
    ssl_key_path: str = ""
    cors_origins: List[str] = None
    api_key_required: bool = False
    jwt_secret: str = ""

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    health_check_interval: int = 30
    metrics_collection_interval: int = 60
    alert_check_interval: int = 60
    response_time_warning: float = 2.0
    response_time_error: float = 5.0
    error_rate_warning: float = 0.05
    error_rate_error: float = 0.10

@dataclass
class SystemConfig:
    """Complete system configuration"""
    environment: str = "development"
    debug: bool = False
    database: DatabaseConfig = None
    api: APIConfig = None
    aws: AWSConfig = None
    kafka: KafkaConfig = None
    accumulo: AccumuloConfig = None
    service: ServiceConfig = None
    logging: LoggingConfig = None
    security: SecurityConfig = None
    monitoring: MonitoringConfig = None
    
    def __post_init__(self):
        """Initialize default configurations"""
        if self.database is None:
            self.database = DatabaseConfig()
        if self.api is None:
            self.api = APIConfig()
        if self.aws is None:
            self.aws = AWSConfig()
        if self.kafka is None:
            self.kafka = KafkaConfig()
        if self.accumulo is None:
            self.accumulo = AccumuloConfig()
        if self.service is None:
            self.service = ServiceConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()

class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self, config_path: str = None, environment: str = None):
        self.config_path = config_path or "config"
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.config = None
        self.ssm_client = None
        self.secrets_client = None
        
        # Initialize AWS clients if credentials are available
        self._init_aws_clients()
        
        # Load configuration
        self.load_configuration()
    
    def _init_aws_clients(self):
        """Initialize AWS clients for Systems Manager and Secrets Manager"""
        try:
            if self._has_aws_credentials():
                self.ssm_client = boto3.client('ssm')
                self.secrets_client = boto3.client('secretsmanager')
                logger.info("✅ AWS clients initialized")
            else:
                logger.warning("⚠️ AWS credentials not found, using local configuration only")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize AWS clients: {e}")
    
    def _has_aws_credentials(self) -> bool:
        """Check if AWS credentials are available"""
        try:
            boto3.client('sts').get_caller_identity()
            return True
        except (NoCredentialsError, ClientError):
            return False
    
    def load_configuration(self):
        """Load configuration from multiple sources"""
        logger.info(f"🔧 Loading configuration for environment: {self.environment}")
        
        # Start with default configuration
        self.config = SystemConfig(environment=self.environment)
        
        # Load from configuration files
        self._load_from_files()
        
        # Load from environment variables
        self._load_from_environment()
        
        # Load from AWS Systems Manager (if available)
        if self.ssm_client:
            self._load_from_ssm()
        
        # Load secrets from AWS Secrets Manager (if available)
        if self.secrets_client:
            self._load_secrets()
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info("✅ Configuration loaded successfully")
    
    def _load_from_files(self):
        """Load configuration from YAML/JSON files"""
        config_files = [
            f"{self.config_path}/config.yaml",
            f"{self.config_path}/config.yml",
            f"{self.config_path}/config.json",
            f"{self.config_path}/{self.environment}.yaml",
            f"{self.config_path}/{self.environment}.yml",
            f"{self.environment}.json"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        if config_file.endswith(('.yaml', '.yml')):
                            config_data = yaml.safe_load(f)
                        else:
                            config_data = json.load(f)
                    
                    self._merge_config(config_data)
                    logger.info(f"✅ Loaded configuration from {config_file}")
                    break
                except Exception as e:
                    logger.error(f"❌ Error loading {config_file}: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # Database
            'MONGODB_URI': ('database', 'mongodb_uri'),
            'MONGODB_DATABASE': ('database', 'mongodb_database'),
            
            # API
            'ALPHA_VANTAGE_API_KEY': ('api', 'alpha_vantage_api_key'),
            'ALPHA_VANTAGE_BASE_URL': ('api', 'alpha_vantage_base_url'),
            
            # AWS
            'AWS_REGION': ('aws', 'region'),
            'SNS_TOPIC_ARN': ('aws', 'sns_topic_arn'),
            'AWS_ACCESS_KEY_ID': ('aws', 'access_key_id'),
            'AWS_SECRET_ACCESS_KEY': ('aws', 'secret_access_key'),
            'AWS_SESSION_TOKEN': ('aws', 'session_token'),
            
            # Kafka
            'KAFKA_BOOTSTRAP_SERVERS': ('kafka', 'bootstrap_servers'),
            'KAFKA_TOPIC': ('kafka', 'topic'),
            'KAFKA_GROUP_ID': ('kafka', 'group_id'),
            
            # Services
            'API_SERVER_HOST': ('service', 'api_server_host'),
            'API_SERVER_PORT': ('service', 'api_server_port'),
            'STREAM_RECEIVER_HOST': ('service', 'stream_receiver_host'),
            'STREAM_RECEIVER_PORT': ('service', 'stream_receiver_port'),
            
            # Logging
            'LOG_LEVEL': ('logging', 'level'),
            'LOG_FILE_PATH': ('logging', 'file_path'),
            
            # Security
            'ENABLE_SSL': ('security', 'enable_ssl'),
            'API_KEY_REQUIRED': ('security', 'api_key_required'),
            'JWT_SECRET': ('security', 'jwt_secret'),
            
            # Monitoring
            'HEALTH_CHECK_INTERVAL': ('monitoring', 'health_check_interval'),
            'METRICS_COLLECTION_INTERVAL': ('monitoring', 'metrics_collection_interval'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if key.endswith('_port') or key.endswith('_interval'):
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif key in ['enable_ssl', 'api_key_required', 'retry_writes', 'enable_auto_commit']:
                    value = value.lower() in ['true', '1', 'yes']
                
                setattr(getattr(self.config, section), key, value)
    
    def _load_from_ssm(self):
        """Load configuration from AWS Systems Manager Parameter Store"""
        if not self.ssm_client:
            return
        
        try:
            # Get parameters for this environment
            parameter_names = [
                f"/financial-streaming/{self.environment}/database/mongodb-uri",
                f"/financial-streaming/{self.environment}/api/alpha-vantage-key",
                f"/financial-streaming/{self.environment}/aws/sns-topic-arn",
                f"/financial-streaming/{self.environment}/kafka/bootstrap-servers",
                f"/financial-streaming/{self.environment}/security/jwt-secret",
            ]
            
            response = self.ssm_client.get_parameters(
                Names=parameter_names,
                WithDecryption=True
            )
            
            for param in response['Parameters']:
                param_name = param['Name']
                param_value = param['Value']
                
                # Map parameter names to configuration
                if 'mongodb-uri' in param_name:
                    self.config.database.mongodb_uri = param_value
                elif 'alpha-vantage-key' in param_name:
                    self.config.api.alpha_vantage_api_key = param_value
                elif 'sns-topic-arn' in param_name:
                    self.config.aws.sns_topic_arn = param_value
                elif 'bootstrap-servers' in param_name:
                    self.config.kafka.bootstrap_servers = param_value
                elif 'jwt-secret' in param_name:
                    self.config.security.jwt_secret = param_value
            
            logger.info(f"✅ Loaded {len(response['Parameters'])} parameters from SSM")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load from SSM: {e}")
    
    def _load_secrets(self):
        """Load secrets from AWS Secrets Manager"""
        if not self.secrets_client:
            return
        
        try:
            secret_name = f"financial-streaming/{self.environment}/secrets"
            
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            secrets = json.loads(response['SecretString'])
            
            # Apply secrets to configuration
            if 'database' in secrets:
                for key, value in secrets['database'].items():
                    setattr(self.config.database, key, value)
            
            if 'api' in secrets:
                for key, value in secrets['api'].items():
                    setattr(self.config.api, key, value)
            
            if 'aws' in secrets:
                for key, value in secrets['aws'].items():
                    setattr(self.config.aws, key, value)
            
            logger.info("✅ Loaded secrets from Secrets Manager")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load secrets: {e}")
    
    def _merge_config(self, config_data: Dict[str, Any]):
        """Merge configuration data into the current config"""
        for section_name, section_data in config_data.items():
            if hasattr(self.config, section_name):
                section = getattr(self.config, section_name)
                for key, value in section_data.items():
                    if hasattr(section, key):
                        setattr(section, key, value)
    
    def _validate_configuration(self):
        """Validate the loaded configuration"""
        errors = []
        
        # Validate required fields
        if not self.config.api.alpha_vantage_api_key:
            errors.append("Alpha Vantage API key is required")
        
        if not self.config.database.mongodb_uri:
            errors.append("MongoDB URI is required")
        
        if self.config.security.enable_ssl:
            if not self.config.security.ssl_cert_path or not self.config.security.ssl_key_path:
                errors.append("SSL certificate and key paths are required when SSL is enabled")
        
        # Validate port ranges
        ports = [
            self.config.service.api_server_port,
            self.config.service.stream_receiver_port,
            self.config.service.driver_port,
            self.config.service.monitoring_port
        ]
        
        for port in ports:
            if not (1024 <= port <= 65535):
                errors.append(f"Port {port} is not in valid range (1024-65535)")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_config(self) -> SystemConfig:
        """Get the current configuration"""
        return self.config
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service"""
        service_configs = {
            'api_server': {
                'host': self.config.service.api_server_host,
                'port': self.config.service.api_server_port,
                'database': asdict(self.config.database),
                'api': asdict(self.config.api),
                'aws': asdict(self.config.aws),
                'logging': asdict(self.config.logging),
                'security': asdict(self.config.security)
            },
            'stream_receiver': {
                'host': self.config.service.stream_receiver_host,
                'port': self.config.service.stream_receiver_port,
                'kafka': asdict(self.config.kafka),
                'accumulo': asdict(self.config.accumulo),
                'logging': asdict(self.config.logging),
                'security': asdict(self.config.security)
            },
            'driver': {
                'host': self.config.service.driver_host,
                'port': self.config.service.driver_port,
                'database': asdict(self.config.database),
                'kafka': asdict(self.config.kafka),
                'logging': asdict(self.config.logging)
            },
            'monitoring': {
                'host': self.config.service.monitoring_host,
                'port': self.config.service.monitoring_port,
                'monitoring': asdict(self.config.monitoring),
                'logging': asdict(self.config.logging)
            }
        }
        
        return service_configs.get(service_name, {})
    
    def save_configuration(self, file_path: str = None):
        """Save current configuration to file"""
        if not file_path:
            file_path = f"{self.config_path}/config_{self.environment}.json"
        
        try:
            # Convert dataclass to dict
            config_dict = asdict(self.config)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            logger.info(f"✅ Configuration saved to {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Error saving configuration: {e}")
    
    def export_environment_variables(self, file_path: str = None):
        """Export configuration as environment variables"""
        if not file_path:
            file_path = f"{self.config_path}/.env.{self.environment}"
        
        try:
            env_vars = []
            
            # Database
            env_vars.append(f"MONGODB_URI={self.config.database.mongodb_uri}")
            env_vars.append(f"MONGODB_DATABASE={self.config.database.mongodb_database}")
            
            # API
            env_vars.append(f"ALPHA_VANTAGE_API_KEY={self.config.api.alpha_vantage_api_key}")
            env_vars.append(f"ALPHA_VANTAGE_BASE_URL={self.config.api.alpha_vantage_base_url}")
            
            # AWS
            env_vars.append(f"AWS_REGION={self.config.aws.region}")
            env_vars.append(f"SNS_TOPIC_ARN={self.config.aws.sns_topic_arn}")
            
            # Kafka
            env_vars.append(f"KAFKA_BOOTSTRAP_SERVERS={self.config.kafka.bootstrap_servers}")
            env_vars.append(f"KAFKA_TOPIC={self.config.kafka.topic}")
            
            # Services
            env_vars.append(f"API_SERVER_HOST={self.config.service.api_server_host}")
            env_vars.append(f"API_SERVER_PORT={self.config.service.api_server_port}")
            env_vars.append(f"STREAM_RECEIVER_HOST={self.config.service.stream_receiver_host}")
            env_vars.append(f"STREAM_RECEIVER_PORT={self.config.service.stream_receiver_port}")
            
            # Logging
            env_vars.append(f"LOG_LEVEL={self.config.logging.level}")
            
            # Environment
            env_vars.append(f"ENVIRONMENT={self.config.environment}")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write('\n'.join(env_vars))
            
            logger.info(f"✅ Environment variables exported to {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Error exporting environment variables: {e}")
    
    def update_parameter(self, section: str, key: str, value: Any):
        """Update a configuration parameter"""
        if hasattr(self.config, section):
            section_obj = getattr(self.config, section)
            if hasattr(section_obj, key):
                setattr(section_obj, key, value)
                logger.info(f"✅ Updated {section}.{key} = {value}")
            else:
                raise ValueError(f"Invalid key: {key}")
        else:
            raise ValueError(f"Invalid section: {section}")
    
    def reload_configuration(self):
        """Reload configuration from all sources"""
        logger.info("🔄 Reloading configuration...")
        self.load_configuration()

# Global configuration manager instance
_config_manager = None

def get_config_manager(config_path: str = None, environment: str = None) -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path, environment)
    return _config_manager

def get_config() -> SystemConfig:
    """Get the current system configuration"""
    return get_config_manager().get_config()

def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get configuration for a specific service - simplified interface"""
    # For backward compatibility, provide a simple interface
    base_config = {
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'debug': os.getenv('DEBUG', 'false').lower() == 'true',
        'aws_region': os.getenv('AWS_REGION', 'us-east-2'),
        'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
        'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'aws_session_token': os.getenv('AWS_SESSION_TOKEN'),
        'sns_topic_arn': os.getenv('SNS_TOPIC_ARN'),
        'mongodb_uri': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/stockdata'),
        'mongodb_database': os.getenv('MONGODB_DATABASE', 'stockdata'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
    
    if service_name == 'api_server':
        return {
            **base_config,
            'port': int(os.getenv('API_SERVER_PORT', 8000)),
            'alpha_vantage_api_key': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'alpha_vantage_base_url': 'https://www.alphavantage.co/query',
            'stock_symbols': [
                'SPY', 'DIA', 'QQQ', 'IWM', 'VXX',
                'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC',
                'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'V', 'PFE', 'ABBV'
            ]
        }
    elif service_name == 'driver':
        return {
            **base_config,
            'port': int(os.getenv('DRIVER_PORT', 8001)),
            'stock_threshold': int(os.getenv('STOCK_THRESHOLD', 30)),
            'tick_interval': float(os.getenv('TICK_INTERVAL', 1.0)),
            'streaming_enabled': os.getenv('STREAMING_ENABLED', 'false').lower() == 'true',
            'api_server_url': os.getenv('API_SERVER_URL', 'http://localhost:8000')
        }
    elif service_name == 'stream_receiver':
        return {
            **base_config,
            'port': int(os.getenv('STREAM_RECEIVER_PORT', 8002)),
            'kafka_bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'kafka_topic_name': os.getenv('KAFKA_TOPIC_NAME', 'stock_ticks'),
            'kafka_group_id': os.getenv('KAFKA_GROUP_ID', 'stream_receiver_group'),
            'accumulo_instance_name': os.getenv('ACCUMULO_INSTANCE_NAME', 'stockdata'),
            'accumulo_username': os.getenv('ACCUMULO_USERNAME', 'root'),
            'accumulo_password': os.getenv('ACCUMULO_PASSWORD', 'secret'),
            'accumulo_zookeepers': os.getenv('ACCUMULO_ZOOKEEPERS', 'localhost:2181'),
            'accumulo_table_name': os.getenv('ACCUMULO_TABLE_NAME', 'stock_ticks'),
            'driver_url': os.getenv('DRIVER_URL', 'http://localhost:8001')
        }
    elif service_name == 'monitoring':
        return {
            **base_config,
            'port': int(os.getenv('MONITORING_PORT', 8080)),
            'api_server_url': os.getenv('API_SERVER_URL', 'http://localhost:8000'),
            'driver_url': os.getenv('DRIVER_URL', 'http://localhost:8001'),
            'stream_receiver_url': os.getenv('STREAM_RECEIVER_URL', 'http://localhost:8002')
        }
    else:
        return base_config

# Create a simple config instance for backward compatibility
config = type('Config', (), {
    'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
    'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
    'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
    'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
    'AWS_SESSION_TOKEN': os.getenv('AWS_SESSION_TOKEN'),
    'AWS_REGION': os.getenv('AWS_REGION', 'us-east-2'),
    'SNS_TOPIC_ARN': os.getenv('SNS_TOPIC_ARN'),
    'MONGODB_URI': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/stockdata'),
    'MONGODB_DATABASE': os.getenv('MONGODB_DATABASE', 'stockdata'),
    'ALPHA_VANTAGE_API_KEY': os.getenv('ALPHA_VANTAGE_API_KEY'),
    'ALPHA_VANTAGE_BASE_URL': 'https://www.alphavantage.co/query',
    'API_SERVER_PORT': int(os.getenv('API_SERVER_PORT', 8000)),
    'DRIVER_PORT': int(os.getenv('DRIVER_PORT', 8001)),
    'STREAM_RECEIVER_PORT': int(os.getenv('STREAM_RECEIVER_PORT', 8002)),
    'MONITORING_PORT': int(os.getenv('MONITORING_PORT', 8080)),
    'API_SERVER_URL': os.getenv('API_SERVER_URL', 'http://localhost:8000'),
    'DRIVER_URL': os.getenv('DRIVER_URL', 'http://localhost:8001'),
    'STREAM_RECEIVER_URL': os.getenv('STREAM_RECEIVER_URL', 'http://localhost:8002'),
    'STOCK_THRESHOLD': int(os.getenv('STOCK_THRESHOLD', 30)),
    'TICK_INTERVAL': float(os.getenv('TICK_INTERVAL', 1.0)),
    'STREAMING_ENABLED': os.getenv('STREAMING_ENABLED', 'false').lower() == 'true',
    'KAFKA_BOOTSTRAP_SERVERS': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    'KAFKA_TOPIC_NAME': os.getenv('KAFKA_TOPIC_NAME', 'stock_ticks'),
    'KAFKA_GROUP_ID': os.getenv('KAFKA_GROUP_ID', 'stream_receiver_group'),
    'ACCUMULO_INSTANCE_NAME': os.getenv('ACCUMULO_INSTANCE_NAME', 'stockdata'),
    'ACCUMULO_USERNAME': os.getenv('ACCUMULO_USERNAME', 'root'),
    'ACCUMULO_PASSWORD': os.getenv('ACCUMULO_PASSWORD', 'secret'),
    'ACCUMULO_ZOOKEEPERS': os.getenv('ACCUMULO_ZOOKEEPERS', 'localhost:2181'),
    'ACCUMULO_TABLE_NAME': os.getenv('ACCUMULO_TABLE_NAME', 'stock_ticks'),
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'STOCK_INDEXES': ['SPY', 'DIA', 'QQQ', 'IWM', 'VXX'],
    'MAJOR_STOCKS': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC', 'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'V', 'PFE', 'ABBV'],
    'ALL_SYMBOLS': ['SPY', 'DIA', 'QQQ', 'IWM', 'VXX', 'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC', 'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'V', 'PFE', 'ABBV']
})()
def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get configuration for a specific service"""
    return get_config_manager().get_service_config(service_name)