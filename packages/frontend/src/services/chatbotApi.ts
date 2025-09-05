import axios from 'axios'
import { extractApiData, createApiError } from '@/utils/apiUtils'
import type { StandardResponse, ErrorResponse } from '@/types/api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request logging for debugging
api.interceptors.request.use((config) => {
  return config
}, (error) => {
  return Promise.reject(error)
})

// Configure axios for cookie-based auth
api.defaults.withCredentials = true

// Add headers to requests
api.interceptors.request.use((config) => {
  // Add ngrok bypass header to skip browser warning
  config.headers['ngrok-skip-browser-warning'] = 'true'

  return config
})

// Handle auth errors and redirects
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
      return Promise.reject(createApiError(error))
    }

    // Handle 307 redirects caused by missing trailing slash
    if (error.response?.status === 307) {
      const redirectLocation = error.response.headers.location

      if (redirectLocation) {
        // Ensure the redirect URL uses HTTPS
        const httpsLocation = redirectLocation.replace(/^http:/, 'https:')

        const config = error.config
        config.url = httpsLocation
        config.baseURL = '' // Clear baseURL to use full URL

        // Retry the request with the corrected URL
        return api.request(config)
      }
    }

    return Promise.reject(createApiError(error))
  }
)

export interface Chatbot {
  id: string
  name: string
  description?: string
  webhook_url: string
  client_id: string
  client_name: string
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface CreateChatbotData {
  name: string
  description?: string
  webhook_url: string
  client_id: string
}

export interface UpdateChatbotData {
  name?: string
  description?: string
  webhook_url?: string
  client_id?: string
  is_active?: boolean
}

export interface ChatbotListResponse {
  chatbots: Chatbot[]
  total: number
}

export interface ChatMessage {
  message: string
  chatbot_id?: string
  conversation_id?: string
}

export interface ChatResponse {
  response: string
  timestamp: string
}

export interface ChatFilters {
  limit?: number
  offset?: number
  start_date?: string
  end_date?: string
  conversation_id?: string
}

export interface ChatHistoryResponse {
  messages: Array<{
    id: string
    message: string
    response: string
    timestamp: string
  }>
  total: number
}

// New Automation API class
export class AutomationApi {
  static async getChatbots(clientId?: string): Promise<ChatbotListResponse> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)

    const queryString = params.toString() ? `?${params.toString()}` : ''
    const res = await api.get<StandardResponse<ChatbotListResponse> | ErrorResponse>(`/automation/chatbots${queryString}`)
    return extractApiData<ChatbotListResponse>(res)
  }

  static async createChatbot(data: CreateChatbotData): Promise<Chatbot> {
    const res = await api.post<StandardResponse<Chatbot> | ErrorResponse>('/automation/chatbots', data)
    return extractApiData<Chatbot>(res)
  }

  static async getChatbot(chatbotId: string): Promise<Chatbot> {
    const res = await api.get<StandardResponse<Chatbot> | ErrorResponse>(`/automation/chatbots/${chatbotId}`)
    return extractApiData<Chatbot>(res)
  }

  static async updateChatbot(chatbotId: string, data: UpdateChatbotData): Promise<Chatbot> {
    const res = await api.patch<StandardResponse<Chatbot> | ErrorResponse>(`/automation/chatbots/${chatbotId}`, data)
    return extractApiData<Chatbot>(res)
  }

  static async deleteChatbot(chatbotId: string): Promise<void> {
    await api.delete<StandardResponse<void> | ErrorResponse>(`/automation/chatbots/${chatbotId}`)
  }

  static async sendMessage(message: ChatMessage): Promise<ChatResponse> {
    const res = await api.post<StandardResponse<ChatResponse> | ErrorResponse>('/automation/chat', message)
    return extractApiData<ChatResponse>(res)
  }

  static async getChatHistory(chatbotId: string, filters?: any): Promise<ChatHistoryResponse> {
    const params = new URLSearchParams()
    if (filters?.limit) params.append('limit', filters.limit.toString())
    if (filters?.offset) params.append('offset', filters.offset.toString())
    if (filters?.start_date) params.append('start_date', filters.start_date)
    if (filters?.end_date) params.append('end_date', filters.end_date)
    if (filters?.conversation_id) params.append('conversation_id', filters.conversation_id)

    const queryString = params.toString() ? `?${params.toString()}` : ''
    const res = await api.get<StandardResponse<ChatHistoryResponse> | ErrorResponse>(`/automation/chat/${chatbotId}/history${queryString}`)
    return extractApiData<ChatHistoryResponse>(res)
  }

  static async getChatConversations(chatbotId: string): Promise<any> {
    const res = await api.get<StandardResponse<any> | ErrorResponse>(`/automation/chat/${chatbotId}/conversations`)
    return extractApiData<any>(res)
  }
}

// Legacy ChatbotApi for backward compatibility
export class ChatbotApi {
  static async getAll(): Promise<ChatbotListResponse> {
    console.warn('ChatbotApi.getAll is deprecated. Use AutomationApi.getChatbots instead.')
    return AutomationApi.getChatbots()
  }

  static async getMine(): Promise<ChatbotListResponse> {
    console.warn('ChatbotApi.getMine is deprecated. Use AutomationApi.getChatbots instead.')
    return AutomationApi.getChatbots()
  }

  static async getById(id: string): Promise<Chatbot> {
    console.warn('ChatbotApi.getById is deprecated. Use AutomationApi.getChatbot instead.')
    return AutomationApi.getChatbot(id)
  }

  static async create(data: CreateChatbotData): Promise<Chatbot> {
    console.warn('ChatbotApi.create is deprecated. Use AutomationApi.createChatbot instead.')
    return AutomationApi.createChatbot(data)
  }

  static async update(id: string, data: UpdateChatbotData): Promise<Chatbot> {
    console.warn('ChatbotApi.update is deprecated. Use AutomationApi.updateChatbot instead.')
    return AutomationApi.updateChatbot(id, data)
  }

  static async delete(id: string): Promise<void> {
    console.warn('ChatbotApi.delete is deprecated. Use AutomationApi.deleteChatbot instead.')
    return AutomationApi.deleteChatbot(id)
  }
}