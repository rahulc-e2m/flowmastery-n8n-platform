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

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
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

  static async createInvitation(invitation: InvitationCreate): Promise<Invitation> {
    const response = await api.post<Invitation>('/auth/invitations', invitation)
    return response.data
  }

  static async getInvitations(): Promise<Invitation[]> {
    const response = await api.get<Invitation[]>('/auth/invitations')
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
}

export default api