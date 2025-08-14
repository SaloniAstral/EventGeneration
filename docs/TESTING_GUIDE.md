# Financial Data Streaming System - Testing Guide

Complete testing infrastructure with unit tests, integration tests, performance tests, and automated test execution.

## 🏗️ Testing Architecture

The testing system provides:

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Service interaction testing
3. **Performance Tests** - Load and stress testing
4. **API Tests** - REST API endpoint testing
5. **Automated Test Runner** - CI/CD integration
6. **Code Coverage** - Test coverage reporting
7. **Code Quality** - Linting and security scanning

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
cd tests
pip install -r requirements.txt
```

### 2. Run All Tests

```bash
# Run all tests with coverage
python run_tests.py --coverage

# Run specific test types
python run_tests.py --test-type unit
python run_tests.py --test-type integration
python run_tests.py --test-type performance
python run_tests.py --test-type api
```

### 3. Run with Code Quality Checks

```bash
# Run tests with linting and security scan
python run_tests.py --lint --security --coverage

# Run in strict mode (fail on quality issues)
python run_tests.py --strict --lint --security
```

## 🧪 Test Types

### Unit Tests

Unit tests verify individual components in isolation:

```python
# Example unit test
def test_alpha_vantage_client():
    client = AlphaVantageClient(api_key="test-key")
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = Mock(return_value={"data": "test"})
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await client.fetch_stock_data("AAPL")
        assert result is not None
        assert "data" in result
```

**Run unit tests:**
```bash
python run_tests.py --test-type unit
```

### Integration Tests

Integration tests verify component interactions:

```python
# Example integration test
def test_api_to_stream_integration():
    # 1. Fetch data via API
    response = api_client.get("/api/v1/stocks/AAPL/data")
    assert response.status_code == 200
    
    # 2. Send to stream receiver
    tick_data = {"symbol": "AAPL", "price": 187.50}
    response = stream_client.post("/api/v1/stream/ticks", json=tick_data)
    assert response.status_code == 200
    
    # 3. Verify in stream
    response = stream_client.get("/api/v1/stream/ticks/AAPL/latest")
    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
```

**Run integration tests:**
```bash
python run_tests.py --test-type integration
```

### Performance Tests

Performance tests verify system performance under load:

```python
# Example performance test
def test_concurrent_requests_performance():
    def make_request():
        start_time = time.time()
        response = api_client.get("/api/v1/stocks/AAPL/data")
        end_time = time.time()
        return end_time - start_time
    
    # Test with 50 concurrent requests
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        response_times = [future.result() for future in futures]
    
    avg_time = statistics.mean(response_times)
    assert avg_time < 2.0  # Average < 2 seconds
    assert max(response_times) < 5.0  # Max < 5 seconds
```

**Run performance tests:**
```bash
python run_tests.py --test-type performance
```

### API Tests

API tests verify REST API endpoints:

```python
# Example API test
def test_get_stock_data_endpoint():
    response = api_client.get("/api/v1/stocks/AAPL/data")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["symbol"] == "AAPL"
    assert "close" in data[0]
    assert "volume" in data[0]
```

**Run API tests:**
```bash
python run_tests.py --test-type api
```

## 🔧 Test Configuration

### Pytest Configuration

The testing system uses pytest with custom configuration:

```python
# conftest.py
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def mock_config_manager():
    """Mock configuration manager."""
    with patch('config.config_manager.get_config_manager') as mock:
        config_manager = Mock()
        config_manager.get_config.return_value = SystemConfig(...)
        mock.return_value = config_manager
        yield config_manager
```

### Test Markers

Tests are organized using pytest markers:

```python
@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration_function():
    pass

@pytest.mark.performance
def test_performance_function():
    pass

@pytest.mark.api
def test_api_function():
    pass
```

### Mock Configuration

The testing system provides comprehensive mocking:

```python
# Mock external services
@pytest.fixture
def mock_alpha_vantage():
    """Mock Alpha Vantage API."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = Mock(return_value=mock_data)
        mock_get.return_value.__aenter__.return_value = mock_response
        yield mock_get

@pytest.fixture
def mock_sns():
    """Mock AWS SNS."""
    with patch('boto3.client') as mock_boto3:
        mock_sns_client = Mock()
        mock_sns_client.publish.return_value = {"MessageId": "test"}
        mock_boto3.return_value = mock_sns_client
        yield mock_sns_client
```

## 📊 Test Coverage

### Coverage Configuration

The testing system generates comprehensive coverage reports:

```bash
# Run tests with coverage
python run_tests.py --coverage

# Coverage reports are generated in:
# - test_results/coverage/all/ (HTML report)
# - test_results/coverage/all_coverage.xml (XML report)
```

### Coverage Targets

The system aims for high test coverage:

- **Unit Tests**: >90% coverage
- **Integration Tests**: >80% coverage
- **API Tests**: >95% coverage
- **Overall**: >85% coverage

### Coverage Reports

Coverage reports include:

1. **HTML Reports** - Interactive coverage visualization
2. **XML Reports** - CI/CD integration
3. **Terminal Reports** - Quick coverage overview
4. **Missing Lines** - Lines not covered by tests

## 🔍 Code Quality

### Linting

The testing system includes code quality checks:

```bash
# Run linting
python run_tests.py --lint

# Linting tools:
# - flake8: Style guide enforcement
# - black: Code formatting
# - isort: Import sorting
```

### Security Scanning

Security scanning identifies potential vulnerabilities:

```bash
# Run security scan
python run_tests.py --security

# Security tools:
# - bandit: Security vulnerability scanner
# - Custom security checks
```

### Quality Gates

Quality gates ensure code meets standards:

```bash
# Run with quality gates
python run_tests.py --strict --lint --security

# Quality gates:
# - All tests must pass
# - Linting must pass
# - Security scan must pass
# - Coverage must meet minimum thresholds
```

## 🚀 Test Runner

### Command Line Options

The test runner provides comprehensive options:

```bash
# Basic usage
python run_tests.py

# Test type selection
python run_tests.py --test-type unit
python run_tests.py --test-type integration
python run_tests.py --test-type performance
python run_tests.py --test-type api
python run_tests.py --test-type all

# Coverage and quality
python run_tests.py --coverage
python run_tests.py --lint
python run_tests.py --security

# Dependencies and strict mode
python run_tests.py --install-deps
python run_tests.py --strict

# Parallel execution
python run_tests.py --parallel
```

### Test Results

Test results are saved to `test_results/`:

```
test_results/
├── unit_tests.xml          # JUnit XML results
├── unit_tests.html         # HTML test report
├── integration_tests.xml   # Integration test results
├── performance_tests.xml   # Performance test results
├── api_tests.xml          # API test results
├── all_tests.xml          # All test results
├── test_report.json       # Summary report
├── coverage/              # Coverage reports
│   ├── all/              # HTML coverage
│   ├── unit/             # Unit test coverage
│   └── integration/      # Integration coverage
└── linting_results.txt   # Linting results
```

## 🔄 CI/CD Integration

### GitHub Actions

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r tests/requirements.txt
    
    - name: Run tests
      run: |
        python tests/run_tests.py --coverage --lint --security
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./test_results/coverage/all_coverage.xml
```

### Jenkins Pipeline

Example Jenkins pipeline:

```groovy
pipeline {
    agent any
    
    stages {
        stage('Install Dependencies') {
            steps {
                sh 'pip install -r tests/requirements.txt'
            }
        }
        
        stage('Run Tests') {
            steps {
                sh 'python tests/run_tests.py --coverage --lint --security'
            }
        }
        
        stage('Publish Results') {
            steps {
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'test_results',
                    reportFiles: 'all_tests.html',
                    reportName: 'Test Report'
                ])
                
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'test_results/coverage/all',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
            }
        }
    }
}
```

## 📈 Performance Testing

### Load Testing

Performance tests verify system behavior under load:

```python
def test_concurrent_load():
    """Test system under concurrent load."""
    concurrency_levels = [10, 50, 100, 200]
    
    for concurrency in concurrency_levels:
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrency)]
            results = [future.result() for future in futures]
        
        duration = time.time() - start_time
        success_rate = sum(1 for r in results if r['status'] == 200) / len(results)
        
        assert success_rate > 0.95  # 95% success rate
        assert duration < 30  # Complete within 30 seconds
```

### Stress Testing

Stress tests verify system limits:

```python
def test_stress_conditions():
    """Test system under stress conditions."""
    # Test with maximum concurrent connections
    max_connections = 1000
    
    with ThreadPoolExecutor(max_workers=max_connections) as executor:
        futures = [executor.submit(make_request) for _ in range(max_connections)]
        results = [future.result() for future in futures]
    
    # System should handle stress gracefully
    success_count = sum(1 for r in results if r['status'] == 200)
    assert success_count > max_connections * 0.8  # 80% success rate
```

### Memory and CPU Testing

Resource usage testing:

```python
def test_resource_usage():
    """Test memory and CPU usage."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform high-load operations
    for i in range(1000):
        response = api_client.get("/api/v1/stocks/AAPL/data")
        assert response.status_code == 200
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Memory should not increase excessively
    assert memory_increase < 100  # < 100MB increase
```

## 🐛 Debugging Tests

### Test Debugging

Debug failing tests:

```bash
# Run with verbose output
python run_tests.py --test-type unit -v

# Run specific test
python -m pytest tests/unit/test_api_server.py::TestAPIServerEndpoints::test_get_stock_data -v

# Run with debugger
python -m pytest tests/unit/test_api_server.py --pdb
```

### Test Isolation

Ensure test isolation:

```python
@pytest.fixture(scope="function")
def clean_database():
    """Clean database before each test."""
    # Setup
    yield
    # Cleanup
    # Clear test data
```

### Mock Debugging

Debug mock issues:

```python
def test_with_mock_debugging():
    with patch('module.function') as mock_func:
        mock_func.return_value = "test"
        
        # Debug mock calls
        result = function_under_test()
        
        # Verify mock was called correctly
        mock_func.assert_called_once_with(expected_args)
        print(f"Mock called {mock_func.call_count} times")
        print(f"Mock call args: {mock_func.call_args_list}")
```

## 📚 Best Practices

### Test Organization

1. **Test Structure**
   - Group related tests in classes
   - Use descriptive test names
   - Follow AAA pattern (Arrange, Act, Assert)

2. **Test Data**
   - Use fixtures for test data
   - Create realistic test scenarios
   - Avoid hardcoded test data

3. **Mocking**
   - Mock external dependencies
   - Use appropriate mock scopes
   - Verify mock interactions

### Test Maintenance

1. **Keep Tests Fast**
   - Use appropriate test scopes
   - Mock slow operations
   - Run tests in parallel when possible

2. **Keep Tests Reliable**
   - Avoid flaky tests
   - Use proper cleanup
   - Handle async operations correctly

3. **Keep Tests Readable**
   - Use clear test names
   - Add descriptive comments
   - Follow consistent patterns

### Coverage Strategy

1. **Unit Tests**
   - Test all public methods
   - Test edge cases and error conditions
   - Aim for >90% coverage

2. **Integration Tests**
   - Test component interactions
   - Test data flow between services
   - Test error handling

3. **Performance Tests**
   - Test under expected load
   - Test system limits
   - Monitor resource usage

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Add project root to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Mock Issues**
   ```python
   # Ensure correct import path for mocking
   with patch('module.submodule.function') as mock_func:
       # Mock the actual import path
   ```

3. **Async Test Issues**
   ```python
   # Use pytest-asyncio for async tests
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

### Performance Issues

1. **Slow Tests**
   - Use appropriate mock scopes
   - Mock external API calls
   - Run tests in parallel

2. **Memory Leaks**
   - Clean up resources in fixtures
   - Use context managers
   - Monitor memory usage

3. **Flaky Tests**
   - Add proper cleanup
   - Use deterministic test data
   - Handle timing issues

---

**🎉 Your Financial Data Streaming System now has comprehensive testing infrastructure!**

The testing system provides complete coverage with unit tests, integration tests, performance tests, and automated quality checks for production-ready reliability. 