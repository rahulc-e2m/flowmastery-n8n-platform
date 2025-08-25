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

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('auth_token')
      const storedUser = localStorage.getItem('user')

      if (storedToken && storedUser) {
        try {
          // Check if token is expired
          const decoded = jwtDecode<JwtPayload>(storedToken)
          const currentTime = Date.now() / 1000

          if (decoded.exp > currentTime) {
            setToken(storedToken)
            setUser(JSON.parse(storedUser))
          } else {
            // Token expired, clear storage
            localStorage.removeItem('auth_token')
            localStorage.removeItem('user')
          }
        } catch (error) {
          console.error('Invalid token:', error)
          localStorage.removeItem('auth_token')
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
      
      localStorage.setItem('auth_token', response.access_token)
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