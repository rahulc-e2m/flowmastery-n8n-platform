import axios from 'axios'
import type {
  LoginRequest,
  LoginResponse,
  User,
  InvitationCreate,
  Invitation,
  InvitationDetails,
  AcceptInvitationRequest
} from '@/types/auth'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://1d03f1f3201b.ngrok-free.app'

// Debug: Log the API URL being used
console.log('AuthApi using API_BASE_URL:', API_BASE_URL)

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // Add ngrok bypass header to skip browser warning
  config.headers['ngrok-skip-browser-warning'] = 'true'
  
  return config
})

// Handle auth errors and redirects
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
      return Promise.reject(error)
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
}

export default api