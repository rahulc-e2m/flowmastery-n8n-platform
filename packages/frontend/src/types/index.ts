// Re-export all types
export * from './auth'
export * from './client'
export * from './metrics'

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