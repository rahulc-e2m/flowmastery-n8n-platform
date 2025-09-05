import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth, useIsAdmin } from '@/hooks/useAuth'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Shield } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAuth?: boolean
  requireAdmin?: boolean
  fallbackPath?: string
  showAccessDenied?: boolean
}

export function ProtectedRoute({ 
  children, 
  requireAuth = true,
  requireAdmin = false,
  fallbackPath = '/login',
  showAccessDenied = true
}: ProtectedRouteProps) {
  const { user, isLoading } = useAuth()
  const isAdmin = useIsAdmin()
  const location = useLocation()

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  // Check authentication requirement
  if (requireAuth && !user) {
    return <Navigate to={`${fallbackPath}?redirect=${encodeURIComponent(location.pathname)}`} replace />
  }

  // Check admin requirement
  if (requireAdmin && !isAdmin) {
    if (showAccessDenied) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6">
          <div className="max-w-md w-full">
            <Alert className="border-red-200 bg-red-50 dark:bg-red-900/20">
              <Shield className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800 dark:text-red-200">
                <div className="font-semibold mb-2">Access Denied</div>
                This page requires administrator privileges. Please contact your administrator for access.
              </AlertDescription>
            </Alert>
            
            <div className="mt-6 text-center">
              <button
                onClick={() => window.history.back()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      )
    } else {
      return <Navigate to="/dashboard" replace />
    }
  }

  return <>{children}</>
}

// Helper components for specific route types
export const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ProtectedRoute requireAuth={true} requireAdmin={true}>
      {children}
    </ProtectedRoute>
  )
}

export const AuthRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ProtectedRoute requireAuth={true} requireAdmin={false}>
      {children}
    </ProtectedRoute>
  )
}
