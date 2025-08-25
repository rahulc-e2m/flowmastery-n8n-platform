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
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  // Chat API
  static async sendMessage(
    message: string,
    chatbotId?: string
  ): Promise<N8nApiResponse> {
    return this.request<N8nApiResponse>('/api/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        message,
        chatbot_id: chatbotId,
      }),
    })
  }

  // Metrics API
  static async getMetrics(fast = false): Promise<N8nMetrics> {
    const endpoint = fast ? '/api/metrics/fast' : '/api/metrics/dashboard'
    return this.request<N8nMetrics>(endpoint)
  }

  // Configuration API
  static async getConfigStatus(): Promise<ConfigStatus> {
    return this.request<ConfigStatus>('/api/config/n8n/status')
  }

  static async updateConfig(config: {
    api_url: string
    api_key: string
    instance_name: string
  }): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>('/api/config/n8n', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  static async testConfig(config: {
    api_url: string
    api_key: string
    instance_name: string
  }): Promise<{
    connection: 'success' | 'failed'
    message: string
    workflows_found?: number
  }> {
    return this.request('/api/config/n8n/test', {
      method: 'POST',
      body: JSON.stringify(config),
    })
  }

  // Health check
  static async checkHealth(): Promise<{
    status: string
    n8n_integration: boolean
  }> {
    return this.request<{
      status: string
      n8n_integration: boolean
    }>('/health')
  }

  // n8n Direct API
  static async queryN8n(query: string): Promise<any> {
    return this.request('/api/n8n/query', {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
  }

  static async getWorkflows(active?: boolean): Promise<{
    workflows: Array<{
      id: string
      name: string
      active: boolean
      createdAt?: string
      updatedAt?: string
    }>
  }> {
    const params = new URLSearchParams()
    if (active !== undefined) {
      params.append('active', active.toString())
    }
    
    return this.request(`/api/n8n/workflows?${params}`)
  }

  static async getExecutions(
    status?: string,
    workflowId?: string
  ): Promise<{
    executions: Array<{
      id: string
      status: 'success' | 'error' | 'waiting'
      workflowId: string
      startedAt: string
      stoppedAt?: string
    }>
  }> {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (workflowId) params.append('workflow_id', workflowId)
    
    return this.request(`/api/n8n/executions?${params}`)
  }
}

export default ApiService