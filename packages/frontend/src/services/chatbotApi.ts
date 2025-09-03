import axios from 'axios'
import { extractApiData, createApiError } from '@/utils/apiUtils'
import type { StandardResponse, ErrorResponse } from '@/types/api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Debug: Log the API URL being used
console.log('ChatbotApi using API_BASE_URL:', API_BASE_URL)

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request logging for debugging
api.interceptors.request.use((config) => {
  console.log('ChatbotApi Request:', config.method?.toUpperCase(), config.url || (config.baseURL || '') + (config.url || ''))
  return config
}, (error) => {
  console.error('ChatbotApi Request Error:', error)
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
    console.log('ChatbotApi Response:', response.status, response.config.url)
    return response
  },
  async (error) => {
    console.error('ChatbotApi Error:', error.response?.status, error.config?.url, error.response?.headers)
    
    if (error.response?.status === 401) {
      window.location.href = '/login'
      return Promise.reject(createApiError(error))
    }
    
    // Handle 307 redirects caused by missing trailing slash
    if (error.response?.status === 307) {
      const redirectLocation = error.response.headers.location
      console.log('307 Redirect detected:', redirectLocation)
      
      if (redirectLocation) {
        // Ensure the redirect URL uses HTTPS
        const httpsLocation = redirectLocation.replace(/^http:/, 'https:')
        console.log('Corrected URL:', httpsLocation)
        
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

export class ChatbotApi {
  static async getAll(): Promise<ChatbotListResponse> {
    const res = await api.get<StandardResponse<ChatbotListResponse> | ErrorResponse>('/chatbots/')
    return extractApiData<ChatbotListResponse>(res)
  }

  static async getById(id: string): Promise<Chatbot> {
    const res = await api.get<StandardResponse<Chatbot> | ErrorResponse>(`/chatbots/${id}`)
    return extractApiData<Chatbot>(res)
  }

  static async create(data: CreateChatbotData): Promise<Chatbot> {
    const res = await api.post<StandardResponse<Chatbot> | ErrorResponse>('/chatbots/', data)
    return extractApiData<Chatbot>(res)
  }

  static async update(id: string, data: UpdateChatbotData): Promise<Chatbot> {
    const res = await api.patch<StandardResponse<Chatbot> | ErrorResponse>(`/chatbots/${id}`, data)
    return extractApiData<Chatbot>(res)
  }

  static async delete(id: string): Promise<void> {
    await api.delete<StandardResponse<void> | ErrorResponse>(`/chatbots/${id}`)
    // Delete operations typically return 204 No Content, so no data to extract
  }

  static async getMine(): Promise<ChatbotListResponse> {
    const res = await api.get<StandardResponse<ChatbotListResponse> | ErrorResponse>('/chatbots/my')
    return extractApiData<ChatbotListResponse>(res)
  }
}