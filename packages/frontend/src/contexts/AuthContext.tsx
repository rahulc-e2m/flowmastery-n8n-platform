import React, { createContext, useContext, useEffect, useState } from 'react'
import { jwtDecode } from 'jwt-decode'
import { AuthApi } from '@/services/authApi'
import type { User, AuthContextType } from '@/types/auth'
import { toast } from 'sonner'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface JwtPayload {
  sub: string
  email: string
  role: string
  exp: number
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Proactive token refresh
  useEffect(() => {
    if (!token) return

    const checkTokenExpiry = () => {
      try {
        const decoded = jwtDecode<JwtPayload>(token)
        const currentTime = Date.now() / 1000
        const timeUntilExpiry = decoded.exp - currentTime

        // Refresh token if it expires in less than 5 minutes (300 seconds)
        if (timeUntilExpiry < 300 && timeUntilExpiry > 0) {
          const refreshToken = localStorage.getItem('refresh_token')
          if (refreshToken) {
            AuthApi.refreshToken(refreshToken)
              .then((response) => {
                localStorage.setItem('auth_token', response.access_token)
                localStorage.setItem('refresh_token', response.refresh_token)
                setToken(response.access_token)
              })
              .catch((error) => {
                console.error('Proactive token refresh failed:', error)
                // Don't logout here, let the axios interceptor handle it
              })
          }
        }
      } catch (error) {
        console.error('Error checking token expiry:', error)
      }
    }

    // Check token expiry every minute
    const interval = setInterval(checkTokenExpiry, 60000)
    
    // Also check immediately
    checkTokenExpiry()

    return () => clearInterval(interval)
  }, [token])

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('auth_token')
      const storedRefreshToken = localStorage.getItem('refresh_token')
      const storedUser = localStorage.getItem('user')

      if (storedToken && storedRefreshToken && storedUser) {
        try {
          // Check if access token is expired
          const decoded = jwtDecode<JwtPayload>(storedToken)
          const currentTime = Date.now() / 1000

          if (decoded.exp > currentTime) {
            // Token is still valid
            setToken(storedToken)
            setUser(JSON.parse(storedUser))
          } else {
            // Access token expired, try to refresh
            try {
              const refreshResponse = await AuthApi.refreshToken(storedRefreshToken)
              
              // Update tokens
              localStorage.setItem('auth_token', refreshResponse.access_token)
              localStorage.setItem('refresh_token', refreshResponse.refresh_token)
              
              setToken(refreshResponse.access_token)
              setUser(JSON.parse(storedUser))
            } catch (refreshError) {
              // Refresh failed, clear storage
              console.error('Token refresh failed:', refreshError)
              localStorage.removeItem('auth_token')
              localStorage.removeItem('refresh_token')
              localStorage.removeItem('user')
            }
          }
        } catch (error) {
          console.error('Invalid token:', error)
          localStorage.removeItem('auth_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
        }
      }

      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true)
      const response = await AuthApi.login({ email, password })
      
      setToken(response.access_token)
      setUser(response.user)
      
      // Store both tokens
      localStorage.setItem('auth_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      
      toast.success('Login successful!')
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed'
      toast.error(message)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    toast.success('Logged out successfully')
  }

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    isLoading,
    isAuthenticated: !!token && !!user,
    isAdmin: user?.role === 'admin',
    isClient: user?.role === 'client',
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}