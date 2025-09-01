export interface User {
  id: string
  email: string
  first_name?: string
  last_name?: string
  role: 'admin' | 'client'
  is_active: boolean
  client_id?: string
  created_at: string
  last_login?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface TokenRefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface InvitationCreate {
  email: string
  role: 'admin' | 'client'
  client_id?: string
}

export interface Invitation {
  id: string
  email: string
  role: 'admin' | 'client'
  status: 'pending' | 'accepted' | 'expired' | 'revoked'
  expiry_date: string
  client_id?: string
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