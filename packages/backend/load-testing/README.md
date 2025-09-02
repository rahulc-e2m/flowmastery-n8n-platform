# Load Testing Framework for FlowMastery n8n Platform

## Overview

This comprehensive load testing framework is designed to test the performance, reliability, and scalability of the FlowMastery n8n Platform APIs using Locust.

## Structure

```
load-testing/
├── README.md                 # This file
├── requirements.txt          # Load testing dependencies
├── config/
│   ├── __init__.py
│   ├── settings.py          # Test configuration settings
│   └── test_data.py         # Test data generators
├── tests/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── test_auth_load.py        # Authentication endpoint tests
│   │   └── test_auth_scenarios.py   # Authentication scenarios
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── test_client_management.py    # Client CRUD operations
│   │   ├── test_client_metrics.py       # Client metrics endpoints
│   │   ├── test_client_n8n.py          # Client n8n integration
│   │   └── test_client_scenarios.py    # Complex client workflows
│   ├── system/
│   │   ├── __init__.py
│   │   ├── test_health_check.py     # Health check endpoints
│   │   ├── test_cache_operations.py # Cache management
│   │   └── test_system_limits.py    # System limits and boundaries
│   └── scenarios/
│       ├── __init__.py
│       ├── test_peak_traffic.py     # Peak traffic simulation
│       ├── test_concurrent_users.py # Concurrent user scenarios  
│       └── test_stress_scenarios.py # Stress testing scenarios
├── utils/
│   ├── __init__.py
│   ├── auth_helper.py       # Authentication utilities
│   ├── data_generator.py    # Test data generation
│   ├── api_client.py        # API client wrapper
│   └── reporters.py         # Custom reporting utilities
├── reports/
│   └── .gitkeep            # For storing test reports
├── scripts/
│   ├── run_client_tests.sh     # Run client-specific tests
│   ├── run_full_suite.sh       # Run complete test suite
│   └── setup_test_data.py      # Setup test data script
└── locustfile.py           # Main Locust configuration
```

## Test Categories

### 1. Authentication Load Testing
- Login/logout performance under load
- Token refresh scenarios
- Rate limiting validation
- Session management stress testing

### 2. Client Management Load Testing
- Client creation/deletion at scale
- Concurrent client operations
- Client data retrieval performance
- Admin vs regular user access patterns

### 3. Client Metrics Load Testing
- Metrics retrieval under heavy load
- Real-time metrics streaming
- Historical data queries
- Aggregation performance testing

### 4. n8n Integration Load Testing
- n8n API configuration testing
- Connection testing under load
- Data synchronization performance
- Workflow metrics collection

### 5. System Performance Testing
- Health check endpoint performance
- Cache operations under load
- Database connection pooling
- Memory and CPU usage patterns

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure test settings:
   ```bash
   cp config/settings.py.example config/settings.py
   # Edit settings.py with your test environment details
   ```

3. Setup test data:
   ```bash
   python scripts/setup_test_data.py
   ```

4. Run client-specific load tests:
   ```bash
   ./scripts/run_client_tests.sh
   ```

5. Run full test suite:
   ```bash
   ./scripts/run_full_suite.sh
   ```

## Test Execution

### Quick Start - Client APIs Only
```bash
locust -f tests/clients/test_client_management.py --host=http://localhost:8000
```

### Full Test Suite
```bash
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10
```

### Headless Mode (CI/CD)
```bash
locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 300s --headless --html=reports/load_test_report.html
```

## Key Metrics to Monitor

1. **Response Times**: 95th percentile under 500ms
2. **Throughput**: Target 1000+ requests per second
3. **Error Rates**: Less than 1% error rate
4. **Authentication**: Login success rate > 99%
5. **Client Operations**: CRUD operations under 200ms
6. **Database Queries**: Complex queries under 1 second

## Environment Requirements

- Python 3.9+
- FlowMastery Backend running on localhost:8000
- PostgreSQL database accessible
- Redis cache accessible
- Admin user credentials for testing

## Security Considerations

- Test data uses mock/dummy information
- No production data is used in load testing
- Authentication tokens are properly managed
- Rate limiting is respected during tests

## Reporting

Test reports are generated in multiple formats:
- HTML reports in `reports/` directory
- CSV data exports for analysis
- Real-time monitoring during test execution
- Performance trend analysis