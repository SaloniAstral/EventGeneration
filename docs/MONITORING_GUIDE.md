# Financial Data Streaming System - Monitoring & Observability Guide

Complete monitoring and observability solution for the Financial Data Streaming System with real-time dashboards, health checks, and performance tracking.

## 🏗️ Architecture Overview

The monitoring system consists of several components:

1. **Real-time Dashboard** - Web-based monitoring interface
2. **Health Checker** - Comprehensive system health monitoring
3. **Alert System** - Real-time alerts and notifications
4. **Performance Metrics** - System performance tracking
5. **Log Aggregation** - Centralized logging

## 📊 Monitoring Dashboard

### Features

- **Real-time Service Health** - Live status of all services
- **System Metrics** - Performance and throughput metrics
- **Active Alerts** - Real-time alert monitoring
- **WebSocket Updates** - Live data updates
- **Responsive Design** - Mobile-friendly interface

### Access

```bash
# Start the monitoring dashboard
cd monitoring
./start_monitoring.sh start

# Access dashboard
open http://localhost:8080
```

### Dashboard Components

#### Service Health Panel
- Real-time status of API Server, Stream Receiver, and Driver
- Response time monitoring
- Last check timestamps
- Color-coded status indicators

#### System Metrics Panel
- Total events processed
- Events per minute
- Active symbols count
- Total ticks processed
- Ticks per second
- Database records count

#### Active Alerts Panel
- Real-time alert display
- Alert severity levels (info, warning, error, critical)
- Auto-resolution of stale alerts
- Alert history

#### Performance Panel
- Processing rates
- Success rates
- Average response times
- System throughput

## 🏥 Health Checker

### Comprehensive Health Monitoring

The health checker performs comprehensive checks on all system components:

```bash
# Run health check manually
cd monitoring
python3 health_checker.py

# Or use the startup script
./start_monitoring.sh health
```

### Health Check Components

#### Service Health Checks
- **API Server** (Port 8000) - Data ingestion service
- **Stream Receiver** (Port 8002) - Real-time processing
- **Driver** (Port 8001) - Times Square simulator

#### Database Health Checks
- MongoDB connection status
- Database performance metrics
- Collection statistics
- Index health

#### Stream Processing Health
- Accumulo connection status
- Kafka producer/consumer health
- Processing performance metrics
- Message throughput

#### Event System Health
- Event processing statistics
- Event queue health
- SNS publishing status
- Event handler performance

#### External Dependencies
- Alpha Vantage API connectivity
- AWS SNS service status
- Network connectivity

### Health Check Output

```
================================================================================
🏥 FINANCIAL DATA STREAMING SYSTEM - HEALTH REPORT
================================================================================
📅 Timestamp: 2024-01-15T10:30:00Z
🎯 Overall Status: HEALTHY

📊 SERVICES SUMMARY:
   Total Services: 3
   Healthy: 3
   Unhealthy: 0

🔍 INDIVIDUAL SERVICE STATUS:
   ✅ api_server: HEALTHY (0.15s)
   ✅ stream_receiver: HEALTHY (0.12s)
   ✅ driver: HEALTHY (0.18s)

🏗️ COMPONENT STATUS:
   ✅ Database: HEALTHY
   ✅ Stream Processing: HEALTHY
   ✅ Event System: HEALTHY

🔗 EXTERNAL DEPENDENCIES:
   ✅ alpha_vantage: HEALTHY
   ✅ aws_sns: HEALTHY

💡 RECOMMENDATIONS:
   ✅ System is healthy and operating normally
================================================================================
```

## 🚨 Alert System

### Alert Types

#### Service Alerts
- **Service Down** - Service not responding
- **High Response Time** - Service is slow
- **Connection Errors** - Network connectivity issues

#### Performance Alerts
- **Low Throughput** - Processing rate below threshold
- **High Error Rate** - Error rate above threshold
- **Resource Exhaustion** - High CPU/Memory usage

#### Data Alerts
- **Data Staleness** - Data not being updated
- **Missing Data** - Expected data not available
- **Data Quality Issues** - Invalid or corrupted data

### Alert Levels

- **Info** - Informational messages
- **Warning** - Issues that need attention
- **Error** - Problems affecting functionality
- **Critical** - System-breaking issues

### Alert Management

```bash
# View current alerts
curl http://localhost:8080/api/alerts

# Resolve an alert
curl -X POST http://localhost:8080/api/alerts/alert_1234567890/resolve
```

## 📈 Performance Metrics

### Key Metrics Tracked

#### System Performance
- **Events per Minute** - Event processing rate
- **Ticks per Second** - Real-time data processing
- **API Requests per Minute** - API usage
- **Database Records** - Data volume

#### Service Performance
- **Response Times** - Service latency
- **Success Rates** - Operation success rates
- **Error Rates** - Failure rates
- **Throughput** - Processing capacity

#### Resource Utilization
- **CPU Usage** - Processor utilization
- **Memory Usage** - RAM consumption
- **Disk Usage** - Storage utilization
- **Network I/O** - Network activity

### Metrics Collection

```bash
# Get current metrics
curl http://localhost:8080/api/metrics

# Get service health
curl http://localhost:8080/api/health
```

## 🔧 Configuration

### Environment Variables

```bash
# Service URLs
API_SERVER_URL=http://localhost:8000
STREAM_RECEIVER_URL=http://localhost:8002
DRIVER_URL=http://localhost:8001

# Monitoring Settings
DASHBOARD_PORT=8080
HEALTH_CHECK_INTERVAL=300
METRICS_COLLECTION_INTERVAL=60

# Alert Thresholds
RESPONSE_TIME_WARNING=2.0
RESPONSE_TIME_ERROR=5.0
ERROR_RATE_WARNING=0.05
ERROR_RATE_ERROR=0.10

# Performance Thresholds
CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=80.0
DISK_THRESHOLD=90.0

# Logging
MONITORING_LOG_LEVEL=INFO
```

### Configuration File

The monitoring system uses `monitoring/config.py` for centralized configuration:

```python
from monitoring.config import MonitoringConfig

# Get service URLs
api_url = MonitoringConfig.get_service_url("api_server")

# Get alert thresholds
warning_threshold = MonitoringConfig.get_alert_threshold("response_time_warning")
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd monitoring
pip install -r requirements.txt
```

### 2. Start Monitoring

```bash
# Start all monitoring components
./start_monitoring.sh start

# Check status
./start_monitoring.sh status
```

### 3. Access Dashboard

Open your browser and navigate to:
```
http://localhost:8080
```

### 4. Run Health Check

```bash
# Manual health check
./start_monitoring.sh health

# Or run directly
python3 health_checker.py
```

## 📋 Monitoring Commands

### Startup Script Commands

```bash
# Start monitoring system
./start_monitoring.sh start

# Stop monitoring system
./start_monitoring.sh stop

# Check system status
./start_monitoring.sh status

# View recent logs
./start_monitoring.sh logs

# Run health check
./start_monitoring.sh health

# Restart monitoring system
./start_monitoring.sh restart
```

### API Endpoints

```bash
# Dashboard
GET http://localhost:8080/

# Health check
GET http://localhost:8080/health

# Service health status
GET http://localhost:8080/api/health

# System metrics
GET http://localhost:8080/api/metrics

# Current alerts
GET http://localhost:8080/api/alerts

# Resolve alert
POST http://localhost:8080/api/alerts/{alert_id}/resolve

# WebSocket connection
WS ws://localhost:8080/ws
```

## 🔍 Troubleshooting

### Common Issues

#### Dashboard Not Accessible
```bash
# Check if dashboard is running
./start_monitoring.sh status

# Check logs
./start_monitoring.sh logs

# Restart dashboard
./start_monitoring.sh restart
```

#### Health Check Failures
```bash
# Check service status
curl http://localhost:8000/health
curl http://localhost:8002/health

# Check dependencies
python3 health_checker.py
```

#### High Alert Volume
```bash
# Check alert configuration
cat monitoring/config.py

# Adjust thresholds
export RESPONSE_TIME_WARNING=3.0
export ERROR_RATE_WARNING=0.10
```

### Log Analysis

```bash
# View dashboard logs
tail -f monitoring/dashboard.log

# View health checker logs
tail -f monitoring/health_checker.log

# Search for errors
grep -i error monitoring/*.log
```

## 📊 Integration with External Systems

### Prometheus Integration

The monitoring system can be integrated with Prometheus for advanced metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'financial-streaming'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Create Grafana dashboards using the monitoring API:

```json
{
  "dashboard": {
    "title": "Financial Data Streaming",
    "panels": [
      {
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "system_health_status",
            "legendFormat": "{{service}}"
          }
        ]
      }
    ]
  }
}
```

### Slack Notifications

Configure Slack notifications for alerts:

```python
# Example Slack integration
import slack_sdk

client = slack_sdk.WebClient(token=os.environ["SLACK_BOT_TOKEN"])
client.chat_postMessage(
    channel="#alerts",
    text="🚨 Alert: Service api_server is down"
)
```

## 🔐 Security Considerations

### Access Control

- **API Authentication** - Implement API key authentication
- **Dashboard Access** - Restrict dashboard access
- **Network Security** - Use HTTPS in production
- **Log Security** - Secure log storage

### Production Deployment

```bash
# Production environment variables
export DASHBOARD_HOST=0.0.0.0
export DASHBOARD_PORT=8080
export HEALTH_CHECK_INTERVAL=60
export ALERT_RETENTION_HOURS=168

# Start with production settings
./start_monitoring.sh start
```

## 📈 Scaling Considerations

### Horizontal Scaling

- **Multiple Dashboard Instances** - Load balance dashboard access
- **Distributed Health Checks** - Run health checks from multiple locations
- **Centralized Alerting** - Centralize alert management

### Performance Optimization

- **Metrics Aggregation** - Aggregate metrics for better performance
- **Alert Deduplication** - Prevent alert spam
- **Caching** - Cache frequently accessed metrics

## 🎯 Best Practices

### Monitoring Best Practices

1. **Set Appropriate Thresholds** - Configure realistic alert thresholds
2. **Monitor Key Metrics** - Focus on business-critical metrics
3. **Regular Health Checks** - Schedule regular comprehensive health checks
4. **Alert Escalation** - Implement alert escalation procedures
5. **Documentation** - Keep monitoring documentation updated

### Alert Management

1. **Avoid Alert Fatigue** - Don't create too many alerts
2. **Use Meaningful Messages** - Clear, actionable alert messages
3. **Auto-Resolution** - Automatically resolve resolved issues
4. **Alert History** - Maintain alert history for analysis

### Performance Monitoring

1. **Baseline Establishment** - Establish performance baselines
2. **Trend Analysis** - Monitor performance trends
3. **Capacity Planning** - Plan for capacity growth
4. **Performance Optimization** - Continuously optimize performance

---

**🎉 Your Financial Data Streaming System now has comprehensive monitoring and observability!**

The monitoring system provides real-time visibility into system health, performance, and alerts, ensuring your financial data streaming system operates reliably and efficiently. 