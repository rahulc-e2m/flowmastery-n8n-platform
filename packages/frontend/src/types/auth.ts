export interface User {
  id: number
  email: string
  role: 'admin' | 'client'
  is_active: boolean
  client_id?: number
  created_at: string
  last_login?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface InvitationCreate {
  email: string
  role: 'admin' | 'client'
  client_id?: number
}

export interface Invitation {
  id: number
  email: string
  role: 'admin' | 'client'
  status: 'pending' | 'accepted' | 'expired' | 'revoked'
  expiry_date: string
  client_id?: number
  created_at: string
}

export interface InvitationDetails {
  email: string
  role: 'admin' | 'client'
  expires_at: string
}

export interface AcceptInvitationRequest {
  token: string
  password: string
}

export interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
  isAuthenticated: boolean
  isAdmin: boolean
  isClient: boolean
}