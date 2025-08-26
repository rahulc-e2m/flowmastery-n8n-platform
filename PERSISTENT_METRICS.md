# Persistent Metrics System Documentation

## Overview

The FlowMastery platform has been enhanced with a comprehensive persistent metrics system that addresses n8n's API limitations (e.g., ~2 days execution history retention) by implementing a background process that periodically fetches and stores workflow execution data for long-term analysis.

## Key Features

### 🔄 Background Data Collection
- **Scheduled Collection**: Runs every 15 minutes to fetch latest execution data
- **Production Filtering**: Intelligently filters out test/dev executions
- **Incremental Sync**: Only syncs new/changed data to minimize API load
- **Error Handling**: Robust error handling with retry logic

### 📊 Historical Data Storage
- **Workflow Metadata**: Stores workflow details, status, and configuration
- **Execution Records**: Complete execution history with timing and status
- **Aggregated Metrics**: Pre-computed daily/weekly/monthly statistics
- **Trend Analysis**: Historical trend calculations and indicators

### 🎯 Production-Only Focus
- **Smart Filtering**: Excludes manual executions and test workflows
- **Pattern Recognition**: Identifies test workflows by name patterns
- **Tag-Based Filtering**: Uses workflow tags to determine environment
- **Configurable Rules**: Customizable filtering rules per client

## Architecture Components

### Database Models

#### Workflow Model (`app/models/workflow.py`)
Stores n8n workflow metadata for long-term reference:
```python
class Workflow(Base):
    n8n_workflow_id: str      # n8n's workflow ID
    client_id: int            # Client association
    name: str                 # Workflow name
    active: bool              # Active status
    tags: str                 # JSON string of tags
    n8n_created_at: datetime  # Original creation time
    last_synced_at: datetime  # Last sync timestamp
```

#### WorkflowExecution Model (`app/models/workflow_execution.py`)
Stores detailed execution records:
```python
class WorkflowExecution(Base):
    n8n_execution_id: str     # n8n's execution ID
    workflow_id: int          # Workflow reference
    status: ExecutionStatus   # SUCCESS, ERROR, etc.
    started_at: datetime      # Execution start time
    finished_at: datetime     # Execution end time
    execution_time_ms: int    # Duration in milliseconds
    is_production: bool       # Production flag
    error_message: str        # Error details if failed
```

#### MetricsAggregation Model (`app/models/metrics_aggregation.py`)
Stores pre-computed metrics for fast retrieval:
```python
class MetricsAggregation(Base):
    client_id: int                    # Client reference
    period_type: AggregationPeriod    # DAILY, WEEKLY, MONTHLY
    period_start: date                # Period start date
    total_executions: int             # Execution count
    success_rate: float               # Success percentage
    avg_execution_time_seconds: float # Average duration
    time_saved_hours: float           # Estimated time savings
```

### Background Services

#### PersistentMetricsCollector (`app/services/persistent_metrics.py`)
- Fetches data from n8n APIs
- Applies production filtering
- Stores/updates database records
- Handles pagination and rate limiting

#### MetricsAggregator (`app/services/metrics_aggregator.py`)
- Computes daily/weekly/monthly aggregations
- Calculates trend indicators
- Manages data retention policies
- Optimizes query performance

#### BackgroundScheduler (`app/services/background_scheduler.py`)
- Manages scheduled tasks using APScheduler
- Handles job failures and retries
- Provides status monitoring
- Configurable scheduling intervals

#### ProductionFilter (`app/services/production_filter.py`)
- Identifies production vs test/dev executions
- Uses multiple filtering criteria:
  - Execution mode (exclude manual)
  - Workflow name patterns
  - Workflow tags
  - Execution timing patterns
  - Custom filtering rules

### API Enhancements

#### New Endpoints
```
GET /api/v1/metrics/client/{id}/historical
- Retrieve historical metrics with date ranges
- Support for daily/weekly/monthly aggregations
- Workflow-specific or client-wide metrics

POST /api/v1/metrics/admin/sync/{client_id}
- Force immediate sync for specific client
- Admin-only endpoint for troubleshooting

GET /api/v1/metrics/admin/scheduler-status  
- View background scheduler status
- Monitor job execution and failures
```

#### Enhanced Existing Endpoints
All existing metrics endpoints now serve data from the persistent store instead of querying n8n directly, providing:
- Faster response times
- Consistent data availability
- Historical data beyond 2-day retention
- Reduced load on n8n systems

## Configuration

### Environment Variables
```bash
# Background scheduler settings
METRICS_SYNC_INTERVAL_MINUTES=15
AGGREGATION_SCHEDULE_HOUR=2
CLEANUP_RETENTION_DAYS=90

# Production filtering
EXCLUDE_MANUAL_EXECUTIONS=true
EXCLUDE_TEST_WORKFLOWS=true
```

### Scheduler Configuration
The background scheduler runs several jobs:

1. **Metrics Collection** (Every 15 minutes)
   - Syncs new executions from all clients
   - Updates workflow metadata
   - Applies production filtering

2. **Daily Aggregation** (2:00 AM daily)
   - Computes daily metrics for previous day
   - Creates client and workflow-level aggregations

3. **Weekly Aggregation** (Sundays, 3:00 AM)
   - Computes weekly metrics for previous week
   - Calculates weekly trends

4. **Monthly Aggregation** (1st of month, 4:00 AM)
   - Computes monthly metrics for previous month
   - Long-term trend analysis

5. **Data Cleanup** (1:00 AM daily)
   - Removes old raw execution data (90 days)
   - Maintains aggregated data (24 months)

## Production Filtering Logic

### Automatic Exclusions
- Manual executions (`mode: "manual"`)
- Workflows with test-related names:
  - Contains: test, dev, debug, sample, demo, staging
- Workflows tagged as non-production
- Executions with test indicators in data/errors

### Automatic Inclusions
- Webhook-triggered executions
- Trigger-based executions  
- Workflows with production indicators:
  - Contains: prod, production, live, main
  - Tagged with production tags

### Customizable Filtering
Per-client filtering rules can be configured:
```python
{
    "exclude_manual": true,
    "exclude_test_workflows": true,
    "exclude_workflow_patterns": [".*test.*", ".*dev.*"],
    "include_workflow_patterns": [".*prod.*"]
}
```

## Data Retention Policy

### Raw Execution Data
- **Retention**: 90 days
- **Purpose**: Real-time queries and recent analysis
- **Cleanup**: Automatic daily cleanup of old records

### Aggregated Metrics  
- **Retention**: 24 months
- **Purpose**: Historical analysis and reporting
- **Cleanup**: Monthly cleanup of very old aggregations

### Workflow Metadata
- **Retention**: Permanent (until workflow deleted from n8n)
- **Purpose**: Reference for execution analysis

## Performance Optimizations

### Database Indexing
Strategic indexes for common query patterns:
```sql
-- Execution queries by client and date
CREATE INDEX ix_workflow_executions_client_date 
ON workflow_executions (client_id, started_at);

-- Production execution filtering
CREATE INDEX ix_workflow_executions_production_status 
ON workflow_executions (is_production, status);

-- Aggregation period queries
CREATE INDEX ix_metrics_aggregations_client_period 
ON metrics_aggregations (client_id, period_type, period_start);
```

### Caching Strategy
- **Redis Caching**: 5-minute cache for aggregated metrics
- **Background Refresh**: Proactive cache warming
- **Cache Invalidation**: Smart invalidation on data updates

### Query Optimization
- **Aggregated Data**: Prefer pre-computed aggregations
- **Fallback Queries**: Raw data fallback for recent metrics
- **Batch Processing**: Efficient bulk operations

## Monitoring & Health Checks

### Scheduler Health
Monitor background job execution:
```bash
GET /api/v1/metrics/admin/scheduler-status
```

### Data Freshness
Track last sync times per client:
- Workflow sync timestamps
- Execution sync timestamps
- Aggregation computation times

### Error Tracking
Comprehensive logging for:
- n8n API connection failures
- Data sync errors
- Aggregation computation failures
- Production filtering statistics

## Migration Guide

### Database Migration
Run the Alembic migration to create new tables:
```bash
cd packages/backend
alembic upgrade head
```

### Dependency Installation
Add required packages:
```bash
pip install apscheduler==3.10.4
```

### Configuration Update
Update environment variables and ensure background scheduler starts with the application.

## Testing

### Test Suite
Run comprehensive tests:
```bash
cd packages/backend
python test_persistent_metrics.py
```

### Manual Testing
1. Verify background scheduler starts
2. Check data collection from n8n
3. Validate production filtering
4. Confirm aggregation generation
5. Test API endpoint responses

## Troubleshooting

### Common Issues

#### Scheduler Not Starting
- Check APScheduler dependencies
- Verify application lifespan configuration
- Review startup logs for errors

#### No Data Collection
- Verify n8n API connectivity
- Check client n8n configuration
- Review production filtering logs

#### Performance Issues
- Monitor database query performance
- Check Redis cache hit rates
- Analyze aggregation computation times

#### Data Inconsistencies
- Compare raw vs aggregated data
- Check production filtering results
- Verify time zone handling

### Debug Endpoints
Use admin endpoints for troubleshooting:
- Force sync specific client
- Check scheduler status
- Review aggregation summaries

## Future Enhancements

### Planned Features
- Custom metric definitions per client
- Real-time alerts for execution failures
- Advanced trend analysis and predictions
- Integration with external monitoring systems
- Workflow performance recommendations

### Scalability Improvements
- Distributed background processing
- Partitioned database tables
- Advanced caching strategies
- API rate limiting and throttling

This persistent metrics system provides a robust foundation for long-term workflow analysis while maintaining excellent performance and reliability.