import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { LoginForm } from '@/components/auth/LoginForm'
import { AcceptInvitationForm } from '@/components/auth/AcceptInvitationForm'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { DashboardPage } from '@/pages/DashboardPage'
import { ClientDashboardPage } from '@/pages/ClientDashboardPage'
import { MetricsPage } from '@/pages/MetricsPage'
import { ClientsPage } from '@/pages/admin/ClientsPage'
import { UsersPage } from '@/pages/admin/UsersPage'
import { WorkflowsPage } from '@/pages/WorkflowsPage'
import HomePage from '@/pages/HomePage'
import { SettingsPage } from '@/pages/SettingsPage'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <Routes>
      {/* Root route - HomePage for unauthenticated, Dashboard for authenticated */}
      <Route 
        path="/" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <HomePage />} 
      />

      {/* Public routes */}
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginForm />} 
      />
      <Route 
        path="/accept-invitation" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <AcceptInvitationForm />} 
      />

      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <DashboardPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/metrics"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <MetricsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <WorkflowsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows/chatbot"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <WorkflowsPage workflowType="chatbot" />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows/email"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <WorkflowsPage workflowType="email" />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows/calendar"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <WorkflowsPage workflowType="calendar" />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows/documents"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <WorkflowsPage workflowType="documents" />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
        path="/settings"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <SettingsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/client/:clientId"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <ClientDashboardPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/workflows/custom"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <WorkflowsPage workflowType="custom" />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <SettingsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/client/:clientId"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <ClientDashboardPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
=======
        path="/settings"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <SettingsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/client/:clientId"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <ClientDashboardPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      {/* Admin only routes */}
      <Route
        path="/admin/clients"
        element={
          <ProtectedRoute requireAdmin>
            <DashboardLayout>
              <ClientsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/users"
        element={
          <ProtectedRoute requireAdmin>
            <DashboardLayout>
              <UsersPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      {/* Catch all - redirect to root */}
      <Route 
        path="*" 
        element={<Navigate to="/" replace />} 
      />
    </Routes>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <Router>
            <AppRoutes />
            <Toaster 
              position="top-right" 
              theme="system"
              richColors
              closeButton
            />
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App