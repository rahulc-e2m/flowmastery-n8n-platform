// Re-export all types
export * from './auth'
export * from './client'
export * from './metrics'
export * from './api'

// Consolidated API types for the new endpoints
export interface ExecutionFilters {
  limit?: number
  offset?: number
  workflow_id?: number
  status?: string
}

export interface HistoricalFilters {
  period?: 'DAILY' | 'WEEKLY' | 'MONTHLY'
  start_date?: string
  end_date?: string
  workflow_id?: number
}

export interface SyncRequest {
  type: 'client' | 'all' | 'quick'
  client_id?: string
  options?: Record<string, any>
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

export interface CacheStats {
  redis_info: {
    used_memory: string
    connected_clients: number
    total_commands_processed: number
  }
  cache_summary: {
    total_keys: number
    client_keys: number
    system_keys: number
  }
  client_cache_status: Array<{
    client_id: string
    client_name: string
    cache_keys: number
    last_updated: string
  }>
}

export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: 'success' | 'error'
}

export interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  metadata?: {
    source?: string
    processingTime?: number
  }
}

export interface Chatbot {
  id: string
  name: string
  description: string
  webhookUrl: string
  status: 'active' | 'inactive' | 'testing'
  type: 'support' | 'sales' | 'faq' | 'custom'
  analytics: {
    totalMessages: number
    activeUsers: number
    avgResponseTime: string
    satisfactionRate: number
  }
  lastUpdated: string
  features: string[]
}

export interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
}

export interface WorkflowShowcase {
  icon: React.ReactNode
  title: string
  description: string
  color: string
}

export interface MetricCard {
  label: string
  value: string
  trend: number
  isLoading?: boolean
  icon: React.ReactNode
}