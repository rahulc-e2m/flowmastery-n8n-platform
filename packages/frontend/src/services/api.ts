// Legacy API service - kept for backward compatibility
// New multi-tenant APIs are in separate files: authApi.ts, clientApi.ts, metricsApi.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://1d03f1f3201b.ngrok-free.app'

// Debug: Log the actual environment variable value
console.log('Environment VITE_API_URL:', import.meta.env.VITE_API_URL)
console.log('Using API_BASE_URL:', API_BASE_URL)

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
    
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }
    
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      if (response.status === 401) {
        // Handle unauthorized - redirect to login
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  // Health check
  static async checkHealth(): Promise<{
    status: string
    version: string
  }> {
    return this.request<{
      status: string
      version: string
    }>('/health')
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

export default ApiService