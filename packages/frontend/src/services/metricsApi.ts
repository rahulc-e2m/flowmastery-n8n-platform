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

export interface ExecutionFilters {
  limit?: number
  offset?: number
  workflow_id?: number
  status?: string
}

export interface DataFreshnessInfo {
  clients: Array<{
    client_id: string
    client_name: string
    last_sync: string
    status: 'fresh' | 'stale' | 'error'
  }>
  summary: {
    total_clients: number
    fresh_clients: number
    stale_clients: number
    error_clients: number
  }
}

export interface CacheRefreshResult {
  message: string
  warmed_clients: number
  cache_stats: Record<string, any>
}

export interface AggregationResult {
  message: string
  task_id: string
  target_date?: string
}

export class MetricsApi {
  // New consolidated methods
  static async getOverview(clientId?: string): Promise<AdminMetricsResponse | ClientMetrics> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<StandardResponse<AdminMetricsResponse | ClientMetrics> | ErrorResponse>(`/metrics/overview${queryString}`)
    return extractApiData<AdminMetricsResponse | ClientMetrics>(response)
  }

  static async getWorkflows(clientId?: string): Promise<ClientWorkflowMetrics> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<StandardResponse<ClientWorkflowMetrics> | ErrorResponse>(`/metrics/workflows${queryString}`)
    return extractApiData<ClientWorkflowMetrics>(response)
  }

  static async getExecutions(clientId?: string, filters?: ExecutionFilters): Promise<any> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)
    if (filters?.limit) params.append('limit', filters.limit.toString())
    if (filters?.offset) params.append('offset', filters.offset.toString())
    if (filters?.workflow_id) params.append('workflow_id', filters.workflow_id.toString())
    if (filters?.status) params.append('status', filters.status)
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<StandardResponse<any> | ErrorResponse>(`/metrics/executions${queryString}`)
    return extractApiData<any>(response)
  }

  static async getExecutionStats(clientId?: string): Promise<any> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<StandardResponse<any> | ErrorResponse>(`/metrics/execution-stats${queryString}`)
    return extractApiData<any>(response)
  }

  static async getHistorical(clientId?: string, filters?: MetricsFilters): Promise<HistoricalMetrics> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)
    if (filters?.period_type) params.append('period_type', filters.period_type)
    if (filters?.start_date) params.append('start_date', filters.start_date)
    if (filters?.end_date) params.append('end_date', filters.end_date)
    if (filters?.workflow_id) params.append('workflow_id', filters.workflow_id.toString())
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<StandardResponse<HistoricalMetrics> | ErrorResponse>(`/metrics/historical${queryString}`)
    return extractApiData<HistoricalMetrics>(response)
  }

  static async getDataFreshness(): Promise<DataFreshnessInfo> {
    const response = await api.get<StandardResponse<DataFreshnessInfo> | ErrorResponse>('/metrics/data-freshness')
    return extractApiData<DataFreshnessInfo>(response)
  }

  static async refreshCache(clientId?: string): Promise<CacheRefreshResult> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.post<StandardResponse<CacheRefreshResult> | ErrorResponse>(`/metrics/refresh-cache${queryString}`)
    return extractApiData<CacheRefreshResult>(response)
  }

  static async triggerAggregation(targetDate?: string): Promise<AggregationResult> {
    const params = new URLSearchParams()
    if (targetDate) params.append('target_date', targetDate)
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.post<StandardResponse<AggregationResult> | ErrorResponse>(`/metrics/trigger-aggregation${queryString}`)
    return extractApiData<AggregationResult>(response)
  }

  // Legacy methods for backward compatibility
  static async getAllClientsMetrics(): Promise<AdminMetricsResponse> {
    const result = await this.getOverview()
    return result as AdminMetricsResponse
  }

  static async getMyMetrics(): Promise<ClientMetrics> {
    const result = await this.getOverview()
    return result as ClientMetrics
  }

  static async getClientMetrics(clientId: string): Promise<ClientMetrics> {
    const result = await this.getOverview(clientId)
    return result as ClientMetrics
  }

  static async getMyWorkflowMetrics(): Promise<ClientWorkflowMetrics> {
    return this.getWorkflows()
  }

  static async getClientWorkflowMetrics(clientId: string): Promise<ClientWorkflowMetrics> {
    return this.getWorkflows(clientId)
  }

  // Legacy methods for backward compatibility (continued)
  static async getClientHistoricalMetrics(
    clientId: string, 
    filters?: MetricsFilters
  ): Promise<HistoricalMetrics> {
    return this.getHistorical(clientId, filters)
  }

  static async getMyHistoricalMetrics(filters?: MetricsFilters): Promise<HistoricalMetrics> {
    return this.getHistorical(undefined, filters)
  }

  static async getClientExecutionStats(clientId: string): Promise<any> {
    return this.getExecutionStats(clientId)
  }

  static async getMyExecutionStats(): Promise<any> {
    return this.getExecutionStats()
  }

  static async getClientExecutions(clientId: string, limit: number = 10): Promise<any> {
    return this.getExecutions(clientId, { limit })
  }

  static async getMyExecutions(limit: number = 10): Promise<any> {
    return this.getExecutions(undefined, { limit })
  }

  // Deprecated methods - use SystemApi instead
  static async forceSync(clientId?: string): Promise<{ message: string; result: any }> {
    console.warn('MetricsApi.forceSync is deprecated. Use SystemApi.sync instead.')
    // For backward compatibility, map to new system API
    const response = await api.post<StandardResponse<{ message: string; result: any }> | ErrorResponse>('/system/sync', {
      type: clientId ? 'client' : 'all',
      client_id: clientId
    })
    return extractApiData<{ message: string; result: any }>(response)
  }

  static async quickSync(): Promise<{ message: string; successful: number; failed: number }> {
    console.warn('MetricsApi.quickSync is deprecated. Use SystemApi.sync instead.')
    const response = await api.post<StandardResponse<{ message: string; successful: number; failed: number }> | ErrorResponse>('/system/sync', {
      type: 'quick'
    })
    return extractApiData<{ message: string; successful: number; failed: number }>(response)
  }

  static async triggerClientSync(clientId: string): Promise<{ message: string; task_id: string }> {
    console.warn('MetricsApi.triggerClientSync is deprecated. Use SystemApi.sync instead.')
    const response = await api.post<StandardResponse<{ message: string; task_id: string }> | ErrorResponse>('/system/sync', {
      type: 'client',
      client_id: clientId
    })
    return extractApiData<{ message: string; task_id: string }>(response)
  }

  static async triggerDailyAggregation(): Promise<{ message: string; task_id: string }> {
    console.warn('MetricsApi.triggerDailyAggregation is deprecated. Use MetricsApi.triggerAggregation instead.')
    return this.triggerAggregation()
  }

  static async getWorkerStats(): Promise<any> {
    console.warn('MetricsApi.getWorkerStats is deprecated. Use SystemApi.getWorkerStats instead.')
    const response = await api.get<StandardResponse<any> | ErrorResponse>('/system/worker-stats')
    return extractApiData<any>(response)
  }

  static async getTaskStatus(taskId: string): Promise<any> {
    console.warn('MetricsApi.getTaskStatus is deprecated. Use SystemApi.getTaskStatus instead.')
    const response = await api.get<StandardResponse<any> | ErrorResponse>(`/system/tasks/${taskId}`)
    return extractApiData<any>(response)
  }

  static async getSchedulerStatus(): Promise<any> {
    console.warn('MetricsApi.getSchedulerStatus is deprecated.')
    const response = await api.get<StandardResponse<any> | ErrorResponse>('/system/worker-stats')
    return extractApiData<any>(response)
  }
}