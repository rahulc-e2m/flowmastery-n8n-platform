export interface WorkflowMetrics {
  workflow_id: string
  workflow_name: string
  total_executions: number
  successful_executions: number
  failed_executions: number
  success_rate: number
  avg_execution_time?: number
  last_execution?: string
  status: 'active' | 'inactive' | 'error'
  time_saved_per_execution_minutes?: number
  time_saved_hours?: number
  is_production?: boolean
  execution_time_trend?: number
  success_rate_trend?: number
}

export interface MetricsTrend {
  execution_trend: number
  success_rate_trend: number
  performance_trend: number
}

export interface ClientMetrics {
  client_id: number
  client_name: string
  total_workflows: number
  active_workflows: number
  total_executions: number
  successful_executions: number
  failed_executions: number
  success_rate: number
  avg_execution_time?: number
  last_activity?: string
  production_executions?: number
  test_executions?: number
  productivity_score?: number
  time_saved_hours?: number
  last_updated?: string  // When metrics were last computed
  trends?: MetricsTrend  // Trend indicators
}

export interface ClientWorkflowMetrics {
  client_id: number
  client_name: string
  workflows: WorkflowMetrics[]
  summary: ClientMetrics
}

export interface AdminMetricsResponse {
  clients: ClientMetrics[]
  total_clients: number
  total_workflows: number
  total_executions: number
  overall_success_rate: number
  total_production_executions?: number
  overall_productivity_score?: number
  total_time_saved_hours?: number  // Overall time saved across all clients
  last_updated?: string  // When admin metrics were last computed
  trends?: MetricsTrend  // Overall system trends
}

export interface MetricsError {
  error: string
  client_id: number
  client_name: string
  details?: string
}

// Historical Metrics Types
export interface MetricsAggregation {
  id: number
  client_id: number
  workflow_id?: number
  period_type: 'DAILY' | 'WEEKLY' | 'MONTHLY'
  period_start: string
  period_end: string
  total_executions: number
  successful_executions: number
  failed_executions: number
  canceled_executions: number
  success_rate: number
  avg_execution_time_seconds?: number
  min_execution_time_seconds?: number
  max_execution_time_seconds?: number
  total_data_size_bytes?: number
  avg_data_size_bytes?: number
  total_workflows?: number
  active_workflows?: number
  most_common_error?: string
  error_count: number
  time_saved_hours?: number
  productivity_score?: number
  computed_at: string
}

export interface HistoricalMetrics {
  client_id: number
  period_type: 'DAILY' | 'WEEKLY' | 'MONTHLY'
  start_date?: string
  end_date?: string
  workflow_id?: number
  aggregations: MetricsAggregation[]
  summary: {
    total_periods: number
    avg_success_rate: number
    total_executions: number
    avg_execution_time: number
    trend_direction: 'UP' | 'DOWN' | 'STABLE'
    trend_percentage: number
  }
}

export interface WorkflowTrendMetrics {
  id: number
  workflow_id: number
  client_id: number
  date: string
  executions_count: number
  success_count: number
  error_count: number
  avg_duration_seconds?: number
  total_duration_seconds?: number
  success_rate_trend?: number
  performance_trend?: number
}

// Enhanced API Response Types
export interface EnhancedClientMetrics extends ClientMetrics {
  recent_trends?: WorkflowTrendMetrics[]
  historical_summary?: {
    last_30_days: MetricsAggregation
    last_7_days: MetricsAggregation
    yesterday: MetricsAggregation
  }
}

export type AggregationPeriod = 'DAILY' | 'WEEKLY' | 'MONTHLY'

export interface MetricsFilters {
  period_type?: AggregationPeriod
  start_date?: string
  end_date?: string
  workflow_id?: number
  include_test_data?: boolean
}