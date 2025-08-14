# Data Quality & Validation System Guide

Complete guide for the Financial Data Streaming System's data quality validation, cleansing, and monitoring capabilities.

## 🎯 Overview

The Data Quality & Validation System ensures that all financial data entering the streaming pipeline is accurate, consistent, and reliable. It provides comprehensive validation, data cleansing, outlier detection, and real-time quality monitoring.

## 🏗️ Architecture

### Core Components

1. **DataQualityValidator**: Main validation engine with configurable rules
2. **DataCleanser**: Data normalization and cleaning utilities
3. **DataQualityMonitor**: Real-time quality monitoring and alerting
4. **FastAPI Service**: REST API for data quality management
5. **Validation Rules**: Configurable validation logic for different data types

### Data Types Supported

- **STOCK_DATA**: Stock price and volume information
- **COMPANY_INFO**: Company metadata and financial ratios
- **STREAM_TICK**: Real-time streaming tick data
- **EVENT_DATA**: System events and notifications

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r data_quality/requirements.txt

# Start the data quality API service
cd data_quality
python api.py
```

### Basic Usage

```python
from data_quality.validator import validate_financial_data, DataType

# Validate stock data
stock_data = {
    "symbol": "AAPL",
    "price": 150.25,
    "volume": 1000000,
    "change": 2.50,
    "change_percent": 1.69,
    "high": 152.00,
    "low": 148.50,
    "open_price": 149.75,
    "previous_close": 147.75,
    "timestamp": "2024-01-15T10:30:00Z"
}

is_acceptable, report = await validate_financial_data(stock_data, DataType.STOCK_DATA)
print(f"Data acceptable: {is_acceptable}")
print(f"Quality score: {report.quality_score}")
```

## 📊 Validation Rules

### Stock Data Rules

| Field | Rule Type | Parameters | Severity | Description |
|-------|-----------|------------|----------|-------------|
| symbol | format | `^[A-Z]{1,5}$` | ERROR | Symbol must be 1-5 uppercase letters |
| price | range | min: 0.01, max: 1,000,000 | ERROR | Price must be reasonable |
| volume | range | min: 0, max: 1,000,000,000 | ERROR | Volume must be non-negative |
| change_percent | range | min: -100, max: 1000 | WARNING | Change percent should be reasonable |
| timestamp | freshness | max_age_hours: 24 | WARNING | Data should not be too old |

### Company Info Rules

| Field | Rule Type | Parameters | Severity | Description |
|-------|-----------|------------|----------|-------------|
| name | required | - | ERROR | Company name is required |
| market_cap | range | min: 0, max: 1,000,000,000,000 | WARNING | Market cap should be reasonable |
| pe_ratio | range | min: 0, max: 1000 | INFO | P/E ratio should be reasonable |

### Stream Tick Rules

| Field | Rule Type | Parameters | Severity | Description |
|-------|-----------|------------|----------|-------------|
| symbol | format | `^[A-Z]{1,5}$` | ERROR | Symbol must be 1-5 uppercase letters |
| price | range | min: 0.01, max: 1,000,000 | ERROR | Price must be reasonable |
| timestamp | freshness | max_age_seconds: 60 | ERROR | Stream tick should be recent |

## 🔧 API Endpoints

### Data Validation

#### Validate Single Record
```http
POST /api/v1/validate
Content-Type: application/json

{
  "data": {
    "symbol": "AAPL",
    "price": 150.25,
    "volume": 1000000
  },
  "data_type": "stock_data",
  "validate_and_clean": true
}
```

#### Validate Batch Records
```http
POST /api/v1/validate/batch
Content-Type: application/json

{
  "data_list": [
    {"symbol": "AAPL", "price": 150.25},
    {"symbol": "GOOGL", "price": 2800.50}
  ],
  "data_type": "stock_data",
  "validate_and_clean": true,
  "remove_outliers": true,
  "outlier_field": "price",
  "outlier_method": "iqr"
}
```

### Quality Monitoring

#### Get Quality Report
```http
GET /api/v1/quality/report?hours=24
```

#### Get Quality Trends
```http
GET /api/v1/quality/trends?hours=24
```

#### Get Validation Statistics
```http
GET /api/v1/stats?hours=24
```

### Configuration Management

#### Get Validation Rules
```http
GET /api/v1/rules?data_type=stock_data
```

#### Add Validation Rule
```http
POST /api/v1/rules
Content-Type: application/json

{
  "field_name": "price",
  "rule_type": "range",
  "parameters": {"min": 0.01, "max": 10000},
  "severity": "error",
  "description": "Price must be between $0.01 and $10,000",
  "enabled": true
}
```

#### Update Quality Thresholds
```http
POST /api/v1/thresholds/quality
Content-Type: application/json

{
  "min_quality_score": 0.85,
  "max_error_rate": 0.03,
  "max_warning_rate": 0.08
}
```

### Data Cleaning

#### Clean Single Record
```http
POST /api/v1/clean
Content-Type: application/json

{
  "data": {"symbol": " aapl ", "price": "150.25"},
  "data_type": "stock_data"
}
```

#### Clean Batch Records
```http
POST /api/v1/clean/batch
Content-Type: application/json

{
  "data_list": [
    {"symbol": " aapl ", "price": "150.25"},
    {"symbol": " googl ", "price": "2800.50"}
  ],
  "data_type": "stock_data"
}
```

## 🧹 Data Cleansing

### Stock Data Cleaning

The `DataCleanser` class provides comprehensive data cleaning:

```python
from data_quality.validator import DataCleanser

# Clean stock data
raw_data = {
    "symbol": " aapl ",  # Extra spaces
    "price": "150.25",   # String instead of float
    "volume": "1000000", # String instead of int
    "timestamp": "2024-01-15T10:30:00Z"
}

cleaned_data = DataCleanser.clean_stock_data(raw_data)
# Result: {"symbol": "AAPL", "price": 150.25, "volume": 1000000, "timestamp": datetime}
```

### Outlier Detection

Remove outliers using statistical methods:

```python
# Remove outliers using IQR method
clean_data = DataCleanser.remove_outliers(
    data_list, 
    field="price", 
    method="iqr"
)

# Remove outliers using Z-score method
clean_data = DataCleanser.remove_outliers(
    data_list, 
    field="price", 
    method="zscore"
)
```

## 📈 Quality Monitoring

### Real-time Monitoring

The `DataQualityMonitor` tracks quality metrics over time:

```python
from data_quality.validator import monitor

# Get quality trends for last 24 hours
trends = monitor.get_quality_trends(hours=24)

print(f"Average quality score: {trends['avg_quality_score']}")
print(f"Error rate: {trends['avg_error_rate']}")
print(f"Trend: {trends['trend']}")
```

### Quality Alerts

Automatic alerts are triggered when quality thresholds are exceeded:

- **Low Quality Score**: Below configured threshold
- **High Error Rate**: Above maximum error rate
- **Slow Processing**: Processing time exceeds threshold

### Quality Scoring

Quality scores are calculated based on validation results:

- **Error Weight**: 60% (most important)
- **Warning Weight**: 30% (moderately important)
- **Info Weight**: 10% (least important)

Formula: `Quality Score = 1.0 - (error_count * 0.6 + warning_count * 0.3 + info_count * 0.1) / total_checks`

## ⚙️ Configuration

### Quality Thresholds

```python
# Configure quality thresholds
validator.quality_thresholds = {
    'min_quality_score': 0.8,    # Minimum acceptable quality score
    'max_error_rate': 0.05,      # Maximum error rate (5%)
    'max_warning_rate': 0.1      # Maximum warning rate (10%)
}
```

### Alert Thresholds

```python
# Configure alert thresholds
monitor.alert_thresholds = {
    'quality_score': 0.8,        # Alert if quality score < 0.8
    'error_rate': 0.05,          # Alert if error rate > 5%
    'processing_time': 5.0       # Alert if processing time > 5s
}
```

### Custom Validation Rules

```python
from data_quality.validator import ValidationRule, ValidationSeverity

# Create custom validation rule
custom_rule = ValidationRule(
    field_name="custom_field",
    rule_type="range",
    parameters={"min": 0, "max": 100},
    severity=ValidationSeverity.WARNING,
    description="Custom field must be between 0 and 100",
    enabled=True
)

# Add to validator
validator.validation_rules["stock_data"].append(custom_rule)
```

## 🔍 Validation Types

### Format Validation

Validates data format using regular expressions:

```python
# Symbol format validation
rule = ValidationRule(
    field_name="symbol",
    rule_type="format",
    parameters={"pattern": r"^[A-Z]{1,5}$"},
    severity=ValidationSeverity.ERROR,
    description="Symbol must be 1-5 uppercase letters"
)
```

### Range Validation

Validates numeric values within specified ranges:

```python
# Price range validation
rule = ValidationRule(
    field_name="price",
    rule_type="range",
    parameters={"min": 0.01, "max": 1000000},
    severity=ValidationSeverity.ERROR,
    description="Price must be between $0.01 and $1,000,000"
)
```

### Required Field Validation

Ensures required fields are present and non-empty:

```python
# Required field validation
rule = ValidationRule(
    field_name="name",
    rule_type="required",
    parameters={},
    severity=ValidationSeverity.ERROR,
    description="Company name is required"
)
```

### Freshness Validation

Validates data timestamps are recent:

```python
# Data freshness validation
rule = ValidationRule(
    field_name="timestamp",
    rule_type="freshness",
    parameters={"max_age_hours": 24},
    severity=ValidationSeverity.WARNING,
    description="Data should not be older than 24 hours"
)
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from data_quality.validator import validate_financial_data, DataType

@pytest.mark.asyncio
async def test_stock_data_validation():
    # Valid stock data
    valid_data = {
        "symbol": "AAPL",
        "price": 150.25,
        "volume": 1000000,
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    is_acceptable, report = await validate_financial_data(valid_data, DataType.STOCK_DATA)
    assert is_acceptable == True
    assert report.quality_score > 0.8

@pytest.mark.asyncio
async def test_invalid_stock_data():
    # Invalid stock data
    invalid_data = {
        "symbol": "INVALID",  # Too long
        "price": -10,         # Negative price
        "volume": "invalid"   # Non-numeric
    }
    
    is_acceptable, report = await validate_financial_data(invalid_data, DataType.STOCK_DATA)
    assert is_acceptable == False
    assert report.quality_score < 0.5
```

### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from data_quality.api import app

client = TestClient(app)

def test_validate_endpoint():
    response = client.post("/api/v1/validate", json={
        "data": {"symbol": "AAPL", "price": 150.25},
        "data_type": "stock_data"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "quality_score" in data
```

## 📊 Quality Metrics

### Key Performance Indicators

1. **Quality Score**: Overall data quality (0.0 - 1.0)
2. **Error Rate**: Percentage of validation errors
3. **Warning Rate**: Percentage of validation warnings
4. **Processing Time**: Time to validate data
5. **Acceptance Rate**: Percentage of data passing validation

### Quality Grades

- **A+**: Quality score ≥ 0.95
- **A**: Quality score ≥ 0.90
- **B+**: Quality score ≥ 0.85
- **B**: Quality score ≥ 0.80
- **C+**: Quality score ≥ 0.75
- **C**: Quality score ≥ 0.70
- **D**: Quality score < 0.70

## 🔄 Integration

### With API Server

```python
# In ec2_api_server/main.py
from data_quality.validator import validate_financial_data, DataType

@app.post("/api/v1/stocks")
async def add_stock_data(stock_data: dict):
    # Validate data before storing
    is_acceptable, report = await validate_financial_data(stock_data, DataType.STOCK_DATA)
    
    if not is_acceptable:
        raise HTTPException(
            status_code=400, 
            detail=f"Data quality check failed: {report.quality_score}"
        )
    
    # Store validated data
    # ... storage logic
```

### With Stream Receiver

```python
# In ec2_stream_receiver/main.py
from data_quality.validator import validate_financial_data, DataType

@app.post("/api/v1/stream/tick")
async def process_tick(tick_data: dict):
    # Validate tick data
    is_acceptable, report = await validate_financial_data(tick_data, DataType.STREAM_TICK)
    
    if is_acceptable:
        # Process valid tick
        # ... processing logic
    else:
        # Log quality issues
        logger.warning(f"Tick validation failed: {report.quality_score}")
```

### With Monitoring System

```python
# In monitoring/dashboard.py
from data_quality.validator import monitor

@app.get("/api/v1/monitoring/quality")
async def get_quality_metrics():
    trends = monitor.get_quality_trends(hours=24)
    return {
        "quality_score": trends['avg_quality_score'],
        "error_rate": trends['avg_error_rate'],
        "trend": trends['trend']
    }
```

## 🚨 Troubleshooting

### Common Issues

1. **High Error Rate**
   - Check data source quality
   - Review validation rules
   - Adjust quality thresholds

2. **Slow Processing**
   - Optimize validation rules
   - Use batch processing
   - Increase processing resources

3. **False Positives**
   - Fine-tune validation parameters
   - Add custom validation rules
   - Review data patterns

### Debug Commands

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed validation results
is_acceptable, report = await validate_financial_data(data, DataType.STOCK_DATA)
for result in report.validation_results:
    print(f"{result.field_name}: {result.passed} - {result.message}")

# Check quality trends
trends = monitor.get_quality_trends(hours=1)
print(f"Recent quality: {trends}")
```

## 📚 Best Practices

### Data Quality Rules

1. **Validate Early**: Validate data as soon as it enters the system
2. **Clean Consistently**: Apply consistent cleaning rules across all data sources
3. **Monitor Continuously**: Track quality metrics in real-time
4. **Alert Appropriately**: Set up alerts for quality degradation
5. **Document Rules**: Maintain clear documentation of validation rules

### Performance Optimization

1. **Batch Processing**: Validate data in batches for better performance
2. **Async Validation**: Use async validation for non-blocking operations
3. **Caching**: Cache validation results for repeated data
4. **Parallel Processing**: Use multiple workers for large datasets

### Maintenance

1. **Regular Reviews**: Review validation rules monthly
2. **Threshold Adjustments**: Adjust thresholds based on business needs
3. **Rule Updates**: Update rules as data patterns change
4. **Performance Monitoring**: Monitor validation performance

---

**🎉 Your Data Quality & Validation System is now ready to ensure high-quality financial data throughout your streaming pipeline!**

The system provides comprehensive validation, cleansing, monitoring, and alerting capabilities to maintain data integrity and reliability. 