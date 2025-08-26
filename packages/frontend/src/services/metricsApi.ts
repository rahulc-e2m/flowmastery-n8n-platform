import api from './authApi'
import type {
  ClientMetrics,
  ClientWorkflowMetrics,
  AdminMetricsResponse,
  HistoricalMetrics,
  AggregationPeriod,
  MetricsFilters
} from '@/types/metrics'

export class MetricsApi {
  static async getAllClientsMetrics(): Promise<AdminMetricsResponse> {
    const response = await api.get<AdminMetricsResponse>('/metrics/all')
    return response.data
  }

  static async getClientMetrics(clientId: number): Promise<ClientMetrics> {
    const response = await api.get<ClientMetrics>(`/metrics/client/${clientId}`)
    return response.data
  }

  static async getClientWorkflowMetrics(clientId: number): Promise<ClientWorkflowMetrics> {
    const response = await api.get<ClientWorkflowMetrics>(`/metrics/client/${clientId}/workflows`)
    return response.data
  }

  static async getMyMetrics(): Promise<ClientMetrics> {
    const response = await api.get<ClientMetrics>('/metrics/my-metrics')
    return response.data
  }

  static async getMyWorkflowMetrics(): Promise<ClientWorkflowMetrics> {
    const response = await api.get<ClientWorkflowMetrics>('/metrics/my-workflows')
    return response.data
  }

  // Historical Metrics Methods
  static async getClientHistoricalMetrics(
    clientId: number, 
    filters?: MetricsFilters
  ): Promise<HistoricalMetrics> {
    const params = new URLSearchParams()
    if (filters?.period_type) params.append('period_type', filters.period_type)
    if (filters?.start_date) params.append('start_date', filters.start_date)
    if (filters?.end_date) params.append('end_date', filters.end_date)
    if (filters?.workflow_id) params.append('workflow_id', filters.workflow_id.toString())
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<HistoricalMetrics>(`/metrics/client/${clientId}/historical${queryString}`)
    return response.data
  }

  static async getMyHistoricalMetrics(filters?: MetricsFilters): Promise<HistoricalMetrics> {
    const params = new URLSearchParams()
    if (filters?.period_type) params.append('period_type', filters.period_type)
    if (filters?.start_date) params.append('start_date', filters.start_date)
    if (filters?.end_date) params.append('end_date', filters.end_date)
    if (filters?.workflow_id) params.append('workflow_id', filters.workflow_id.toString())
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<HistoricalMetrics>(`/metrics/my-historical${queryString}`)
    return response.data
  }

  // Data Management Methods
  static async forceSync(clientId?: number): Promise<{ message: string; result: any }> {
    if (clientId) {
      const response = await api.post(`/metrics/admin/sync/${clientId}`)
      return response.data
    } else {
      const response = await api.post('/metrics/admin/sync-all')
      return response.data
    }
  }

  static async getSchedulerStatus(): Promise<any> {
    const response = await api.get('/metrics/admin/scheduler-status')
    return response.data
  }

  // Task Management Methods  
  static async triggerClientSync(clientId: number): Promise<{ message: string; task_id: string }> {
    const response = await api.post(`/tasks/sync-client/${clientId}`)
    return response.data
  }

  static async triggerDailyAggregation(): Promise<{ message: string; task_id: string }> {
    const response = await api.post('/tasks/daily-aggregation')
    return response.data
  }

  static async getWorkerStats(): Promise<any> {
    const response = await api.get('/tasks/worker-stats')
    return response.data
  }

  static async getTaskStatus(taskId: string): Promise<any> {
    const response = await api.get(`/tasks/status/${taskId}`)
    return response.data
  }

  // New Execution Data Methods
  static async getClientExecutionStats(clientId: number): Promise<any> {
    const response = await api.get(`/metrics/client/${clientId}/execution-stats`)
    return response.data
  }

  static async getClientExecutions(clientId: number, limit: number = 10): Promise<any> {
    const response = await api.get(`/metrics/client/${clientId}/executions?limit=${limit}`)
    return response.data
  }

  static async getMyExecutionStats(): Promise<any> {
    const response = await api.get('/metrics/my-execution-stats')
    return response.data
  }

  static async getMyExecutions(limit: number = 10): Promise<any> {
    const response = await api.get(`/metrics/my-executions?limit=${limit}`)
    return response.data
  }
}