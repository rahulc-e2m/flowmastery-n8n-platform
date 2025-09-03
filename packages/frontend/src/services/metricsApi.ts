import api from './authApi'
import type {
  ClientMetrics,
  ClientWorkflowMetrics,
  AdminMetricsResponse,
  HistoricalMetrics,
  MetricsFilters
} from '@/types/metrics'
import { extractApiData } from '@/utils/apiUtils'
import type { StandardResponse, ErrorResponse } from '@/types/api'

export class MetricsApi {
  static async getAllClientsMetrics(): Promise<AdminMetricsResponse> {
    const response = await api.get<StandardResponse<AdminMetricsResponse> | ErrorResponse>('/metrics/all')
    return extractApiData<AdminMetricsResponse>(response)
  }

  static async getClientMetrics(clientId: string): Promise<ClientMetrics> {
    const response = await api.get<StandardResponse<ClientMetrics> | ErrorResponse>(`/metrics/client/${clientId}`)
    return extractApiData<ClientMetrics>(response)
  }

  static async getClientWorkflowMetrics(clientId: string): Promise<ClientWorkflowMetrics> {
    const response = await api.get<StandardResponse<ClientWorkflowMetrics> | ErrorResponse>(`/metrics/client/${clientId}/workflows`)
    return extractApiData<ClientWorkflowMetrics>(response)
  }

  static async getMyMetrics(): Promise<ClientMetrics> {
    const response = await api.get<StandardResponse<ClientMetrics> | ErrorResponse>('/metrics/my-metrics')
    return extractApiData<ClientMetrics>(response)
  }

  static async getMyWorkflowMetrics(): Promise<ClientWorkflowMetrics> {
    const response = await api.get<StandardResponse<ClientWorkflowMetrics> | ErrorResponse>('/metrics/my-workflows')
    return extractApiData<ClientWorkflowMetrics>(response)
  }

  // Historical Metrics Methods
  static async getClientHistoricalMetrics(
    clientId: string, 
    filters?: MetricsFilters
  ): Promise<HistoricalMetrics> {
    const params = new URLSearchParams()
    if (filters?.period_type) params.append('period_type', filters.period_type)
    if (filters?.start_date) params.append('start_date', filters.start_date)
    if (filters?.end_date) params.append('end_date', filters.end_date)
    if (filters?.workflow_id) params.append('workflow_id', filters.workflow_id.toString())
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<StandardResponse<HistoricalMetrics> | ErrorResponse>(`/metrics/client/${clientId}/historical${queryString}`)
    return extractApiData<HistoricalMetrics>(response)
  }

  static async getMyHistoricalMetrics(filters?: MetricsFilters): Promise<HistoricalMetrics> {
    const params = new URLSearchParams()
    if (filters?.period_type) params.append('period_type', filters.period_type)
    if (filters?.start_date) params.append('start_date', filters.start_date)
    if (filters?.end_date) params.append('end_date', filters.end_date)
    if (filters?.workflow_id) params.append('workflow_id', filters.workflow_id.toString())
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<StandardResponse<HistoricalMetrics> | ErrorResponse>(`/metrics/my-historical${queryString}`)
    return extractApiData<HistoricalMetrics>(response)
  }

  // Data Management Methods
  static async forceSync(clientId?: string): Promise<{ message: string; result: any }> {
    if (clientId) {
      const response = await api.post<StandardResponse<{ message: string; result: any }> | ErrorResponse>(`/metrics/admin/sync/${clientId}`)
      return extractApiData<{ message: string; result: any }>(response)
    } else {
      const response = await api.post<StandardResponse<{ message: string; result: any }> | ErrorResponse>('/metrics/admin/sync-all')
      return extractApiData<{ message: string; result: any }>(response)
    }
  }

  static async quickSync(): Promise<{ message: string; successful: number; failed: number }> {
    const response = await api.post<StandardResponse<{ message: string; successful: number; failed: number }> | ErrorResponse>('/metrics/admin/quick-sync')
    return extractApiData<{ message: string; successful: number; failed: number }>(response)
  }

  static async refreshCache(): Promise<{ message: string; warmed_clients: number }> {
    const response = await api.post<StandardResponse<{ message: string; warmed_clients: number }> | ErrorResponse>('/metrics/admin/refresh-cache')
    return extractApiData<{ message: string; warmed_clients: number }>(response)
  }

  static async getSchedulerStatus(): Promise<any> {
    const response = await api.get<StandardResponse<any> | ErrorResponse>('/metrics/admin/scheduler-status')
    return extractApiData<any>(response)
  }

  // Task Management Methods  
  static async triggerClientSync(clientId: string): Promise<{ message: string; task_id: string }> {
    const response = await api.post<StandardResponse<{ message: string; task_id: string }> | ErrorResponse>(`/tasks/sync-client/${clientId}`)
    return extractApiData<{ message: string; task_id: string }>(response)
  }

  static async triggerDailyAggregation(): Promise<{ message: string; task_id: string }> {
    const response = await api.post<StandardResponse<{ message: string; task_id: string }> | ErrorResponse>('/tasks/daily-aggregation')
    return extractApiData<{ message: string; task_id: string }>(response)
  }

  static async getWorkerStats(): Promise<any> {
    const response = await api.get<StandardResponse<any> | ErrorResponse>('/tasks/worker-stats')
    return extractApiData<any>(response)
  }

  static async getTaskStatus(taskId: string): Promise<any> {
    const response = await api.get<StandardResponse<any> | ErrorResponse>(`/tasks/status/${taskId}`)
    return extractApiData<any>(response)
  }

  // New Execution Data Methods
  static async getClientExecutionStats(clientId: string): Promise<any> {
    const response = await api.get<StandardResponse<any> | ErrorResponse>(`/metrics/client/${clientId}/execution-stats`)
    return extractApiData<any>(response)
  }

  static async getClientExecutions(clientId: string, limit: number = 10): Promise<any> {
    const response = await api.get<StandardResponse<any> | ErrorResponse>(`/metrics/client/${clientId}/executions?limit=${limit}`)
    return extractApiData<any>(response)
  }

  static async getMyExecutionStats(): Promise<any> {
    const response = await api.get<StandardResponse<any> | ErrorResponse>('/metrics/my-execution-stats')
    return extractApiData<any>(response)
  }

  static async getMyExecutions(limit: number = 10): Promise<any> {
    const response = await api.get<StandardResponse<any> | ErrorResponse>(`/metrics/my-executions?limit=${limit}`)
    return extractApiData<any>(response)
  }
}