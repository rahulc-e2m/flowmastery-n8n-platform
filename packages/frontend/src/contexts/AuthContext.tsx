import React, { createContext, useContext, useEffect, useState } from 'react'
import { AuthApi } from '@/services/authApi'
import type { User, AuthContextType } from '@/types/auth'
import { toast } from 'sonner'

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Proactive token refresh - since we use httpOnly cookies, we'll rely on axios interceptors
  // for token refresh instead of proactive checking

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Try to get current user info (will work if valid cookie exists)
        const currentUser = await AuthApi.getCurrentUser()
        setUser(currentUser)
        setToken('authenticated') // Just a flag since we don't store actual token
      } catch (error: any) {
        // No valid authentication found - this is expected for new users
        // Only log if it's not a 401 (which is expected)
        if (error.response?.status !== 401) {
          console.error('Auth initialization error:', error)
        }
        setUser(null)
        setToken(null)
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true)
      const response = await AuthApi.login({ email, password })

      setToken('authenticated') // Just a flag since token is in httpOnly cookie
      setUser(response.user)

      toast.success('Login successful!')
    } catch (error: any) {
      // Handle standardized error format
      const message = error.message || error.response?.data?.message || error.response?.data?.detail || 'Login failed'
      toast.error(message)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await AuthApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setToken(null)
      setUser(null)
      toast.success('Logged out successfully')
    }
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