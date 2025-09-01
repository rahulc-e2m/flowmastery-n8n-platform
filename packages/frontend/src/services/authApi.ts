import axios from 'axios'
import type {
  LoginRequest,
  LoginResponse,
  User,
  InvitationCreate,
  Invitation,
  InvitationDetails,
  AcceptInvitationRequest,
  RefreshTokenRequest,
  TokenRefreshResponse
} from '@/types/auth'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Debug: Log the API URL being used
console.log('AuthApi using API_BASE_URL:', API_BASE_URL)

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies in requests
})

// Add headers to requests
api.interceptors.request.use((config) => {
  // Add ngrok bypass header to skip browser warning
  config.headers['ngrok-skip-browser-warning'] = 'true'
  
  return config
})

// Track if we're currently refreshing to avoid multiple refresh attempts
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (error?: any) => void
}> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token)
    }
  })
  
  failedQueue = []
}

// Handle auth errors and automatic token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If we're already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => {
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // Try to refresh the token using cookies
        await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {}, {
          withCredentials: true
        })

        // Token refreshed successfully (stored in httpOnly cookie)
        processQueue(null)
        
        // Retry the original request
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, log out user
        processQueue(refreshError, null)
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
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
    
    return Promise.reject(error)
  }
)

export class AuthApi {
  static async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/login', credentials)
    return response.data
  }

  static async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me')
    return response.data
  }

  static async updateProfile(profileData: { first_name?: string; last_name?: string }): Promise<User> {
    const response = await api.put<User>('/auth/profile', profileData)
    return response.data
  }

  static async createInvitation(invitation: InvitationCreate): Promise<Invitation> {
    const response = await api.post<Invitation>('/auth/invitations', invitation)
    return response.data
  }

  static async getInvitations(): Promise<Invitation[]> {
    const response = await api.get<Invitation[]>('/auth/invitations')
    return response.data
  }

  static async getInvitationLink(invitationId: string): Promise<{ invitation_link: string; token: string }> {
    const response = await api.get<{ invitation_link: string; token: string }>(`/auth/invitations/${invitationId}/link`)
    return response.data
  }

  static async getInvitationDetails(token: string): Promise<InvitationDetails> {
    const response = await api.get<InvitationDetails>(`/auth/invitations/${token}`)
    return response.data
  }

  static async acceptInvitation(data: AcceptInvitationRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/invitations/accept', data)
    return response.data
  }

  static async revokeInvitation(invitationId: string): Promise<{ message: string; invitation_id: string; email: string }> {
    const response = await api.delete<{ message: string; invitation_id: string; email: string }>(`/auth/invitations/${invitationId}`)
    return response.data
  }

  static async refreshToken(): Promise<TokenRefreshResponse> {
    const response = await api.post<TokenRefreshResponse>('/auth/refresh', {})
    return response.data
  }

  static async logout(): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/logout', {})
    return response.data
  }
}

export default api