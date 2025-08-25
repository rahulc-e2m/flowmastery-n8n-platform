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
}

export interface MetricsError {
  error: string
  client_id: number
  client_name: string
  details?: string
}