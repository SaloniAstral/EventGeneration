#!/usr/bin/env python3
"""
Configuration for Monitoring and Observability System
"""

import os
from typing import Dict, List

class MonitoringConfig:
    """Configuration for monitoring system"""
    
    # Service URLs
    SERVICES = {
        "api_server": os.getenv("API_SERVER_URL", "http://localhost:8000"),
        "stream_receiver": os.getenv("STREAM_RECEIVER_URL", "http://localhost:8002"),
        "driver": os.getenv("DRIVER_URL", "http://localhost:8001")
    }
    
    # Monitoring settings
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))  # seconds
    METRICS_COLLECTION_INTERVAL = int(os.getenv("METRICS_COLLECTION_INTERVAL", "60"))  # seconds
    ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "60"))  # seconds
    
    # Alert thresholds
    ALERT_THRESHOLDS = {
        "response_time_warning": float(os.getenv("RESPONSE_TIME_WARNING", "2.0")),  # seconds
        "response_time_error": float(os.getenv("RESPONSE_TIME_ERROR", "5.0")),  # seconds
        "error_rate_warning": float(os.getenv("ERROR_RATE_WARNING", "0.05")),  # 5%
        "error_rate_error": float(os.getenv("ERROR_RATE_ERROR", "0.10")),  # 10%
        "ticks_per_second_min": float(os.getenv("TICKS_PER_SECOND_MIN", "1.0")),
        "events_per_minute_min": float(os.getenv("EVENTS_PER_MINUTE_MIN", "1.0"))
    }
    
    # Dashboard settings
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))
    DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    
    # Logging
    LOG_LEVEL = os.getenv("MONITORING_LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("MONITORING_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # WebSocket settings
    WEBSOCKET_PING_INTERVAL = int(os.getenv("WEBSOCKET_PING_INTERVAL", "30"))  # seconds
    WEBSOCKET_PING_TIMEOUT = int(os.getenv("WEBSOCKET_PING_TIMEOUT", "10"))  # seconds
    
    # Performance monitoring
    PERFORMANCE_METRICS = {
        "cpu_threshold": float(os.getenv("CPU_THRESHOLD", "80.0")),  # percentage
        "memory_threshold": float(os.getenv("MEMORY_THRESHOLD", "80.0")),  # percentage
        "disk_threshold": float(os.getenv("DISK_THRESHOLD", "90.0"))  # percentage
    }
    
    # Alert retention
    ALERT_RETENTION_HOURS = int(os.getenv("ALERT_RETENTION_HOURS", "24"))
    MAX_ALERTS = int(os.getenv("MAX_ALERTS", "100"))
    
    # Metrics retention
    METRICS_RETENTION_HOURS = int(os.getenv("METRICS_RETENTION_HOURS", "168"))  # 7 days
    
    # Notification settings (for future use)
    NOTIFICATIONS = {
        "email_enabled": os.getenv("EMAIL_NOTIFICATIONS", "false").lower() == "true",
        "slack_enabled": os.getenv("SLACK_NOTIFICATIONS", "false").lower() == "true",
        "webhook_enabled": os.getenv("WEBHOOK_NOTIFICATIONS", "false").lower() == "true"
    }
    
    @classmethod
    def get_service_url(cls, service_name: str) -> str:
        """Get URL for a specific service"""
        return cls.SERVICES.get(service_name, "")
    
    @classmethod
    def get_all_service_urls(cls) -> Dict[str, str]:
        """Get all service URLs"""
        return cls.SERVICES.copy()
    
    @classmethod
    def get_alert_threshold(cls, threshold_name: str) -> float:
        """Get alert threshold value"""
        return cls.ALERT_THRESHOLDS.get(threshold_name, 0.0)
    
    @classmethod
    def is_notification_enabled(cls, notification_type: str) -> bool:
        """Check if notification type is enabled"""
        return cls.NOTIFICATIONS.get(f"{notification_type}_enabled", False) 