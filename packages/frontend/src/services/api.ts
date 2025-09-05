// Legacy API service - kept for backward compatibility
// New multi-tenant APIs are in separate files: authApi.ts, clientApi.ts, metricsApi.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface N8nApiResponse {
  response: string
  message_id: string
  timestamp: string
  processing_time: number
  source: 'n8n_api' | 'webhook' | 'fallback' | 'error'
}

export interface N8nMetrics {
  status: string
  timestamp: string
  response_time: number
  connection_healthy: boolean
  workflows: {
    total_workflows: number
    active_workflows: number
    inactive_workflows: number
  }
  executions: {
    total_executions: number
    success_executions: number
    error_executions: number
    success_rate: number
    today_executions: number
  }
  users: {
    total_users: number
    admin_users: number
    member_users: number
  }
  system: {
    total_variables: number
    total_tags: number
  }
  derived_metrics: {
    time_saved_hours: number
    activity_score: number
    automation_efficiency: number
    workflows_per_user: number
    executions_per_workflow: number
  }
}

export interface ConfigStatus {
  configured: boolean
  connection_healthy?: boolean
  instance_name?: string
  api_url?: string
  masked_api_key?: string
  message?: string
}

class ApiService {
  private static async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true', // Skip ngrok browser warning
      ...options.headers,
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Include cookies in requests
    })

    const responseData = await response.json()

    if (!response.ok) {
      if (response.status === 401) {
        // Handle unauthorized - redirect to login
        window.location.href = '/login'
      }
      
      // Handle standardized error response
      if (responseData.status === 'error') {
        const error = new Error(responseData.message || `HTTP ${response.status}: ${response.statusText}`)
        ;(error as any).code = responseData.code
        ;(error as any).details = responseData.details
        ;(error as any).requestId = responseData.request_id
        throw error
      }
      
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    // Handle standardized success response
    if (responseData.status === 'success') {
      return responseData.data
    }

    // Fallback for legacy responses
    return responseData
  }

  // Health check
  static async checkHealth(): Promise<{
    status: string
    version: string
    timestamp: string
  }> {
    return this.request<{
      status: string
      version: string
      timestamp: string
    }>('/api/v1/health/')
  }

  // Legacy chat API (if still needed)
  static async sendMessage(
    message: string,
    chatbotId?: string
  ): Promise<N8nApiResponse> {
    return this.request<N8nApiResponse>('/api/v1/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        message,
        chatbot_id: chatbotId,
      }),
    })
  }
}

// System API for admin operations
export interface SyncRequest {
  type: 'client' | 'all' | 'quick'
  client_id?: string
  options?: Record<string, any>
}

export interface SyncResult {
  message: string
  task_id?: string
  result?: any
}

export interface CacheStats {
  redis_info: Record<string, any>
  cache_summary: Record<string, any>
  client_cache_status: Array<{
    client_id: string
    client_name: string
    cache_status: string
  }>
}

export interface CacheResult {
  message: string
  cleared_keys: number
}

export interface TaskStatus {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  result?: any
  error?: string
  created_at: string
  updated_at: string
}

export interface WorkerStats {
  active_workers: number
  total_tasks: number
  pending_tasks: number
  completed_tasks: number
  failed_tasks: number
}

export class SystemApi {
  static async sync(request: SyncRequest): Promise<SyncResult> {
    return ApiService.request<SyncResult>('/api/v1/system/sync', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static async getCacheStats(): Promise<CacheStats> {
    return ApiService.request<CacheStats>('/api/v1/system/cache/stats')
  }

  static async clearCache(clientId?: string, pattern?: string): Promise<CacheResult> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)
    if (pattern) params.append('pattern', pattern)
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    return ApiService.request<CacheResult>(`/api/v1/system/cache${queryString}`, {
      method: 'DELETE',
    })
  }

  static async getTaskStatus(taskId: string): Promise<TaskStatus> {
    return ApiService.request<TaskStatus>(`/api/v1/system/tasks/${taskId}`)
  }

  static async getWorkerStats(): Promise<WorkerStats> {
    return ApiService.request<WorkerStats>('/api/v1/system/worker-stats')
  }
}

export default ApiService