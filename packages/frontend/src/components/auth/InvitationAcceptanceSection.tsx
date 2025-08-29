import React, { useState, useEffect, forwardRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, UserPlus, CheckCircle, Mail, Clock, Shield } from 'lucide-react'
import { AuthApi } from '@/services/authApi'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'
import type { InvitationDetails } from '@/types/auth'

const acceptInvitationSchema = z.object({
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

type AcceptInvitationFormData = z.infer<typeof acceptInvitationSchema>

interface InvitationAcceptanceSectionProps {
  token: string | null
  onSuccess?: () => void
  embedded?: boolean
}

export const InvitationAcceptanceSection = forwardRef<HTMLDivElement, InvitationAcceptanceSectionProps>(
  ({ token, onSuccess, embedded = false }, ref) => {
    const navigate = useNavigate()
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [invitation, setInvitation] = useState<InvitationDetails | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSubmitting, setIsSubmitting] = useState(false)

    const {
      register,
      handleSubmit,
      formState: { errors, isValid },
      watch
    } = useForm<AcceptInvitationFormData>({
      resolver: zodResolver(acceptInvitationSchema),
      mode: 'onChange' // Enable real-time validation
    })

    // Watch form values for validation
    const watchedValues = watch()

    useEffect(() => {
      const fetchInvitation = async () => {
        if (!token) {
          if (!embedded) {
            toast.error('Invalid invitation link')
            navigate('/login')
          }
          setIsLoading(false)
          return
        }

        try {
          const invitationDetails = await AuthApi.getInvitationDetails(token)
          setInvitation(invitationDetails)
        } catch (error: any) {
          const message = error.response?.data?.detail || 'Invalid or expired invitation'
          if (!embedded) {
            toast.error(message)
            navigate('/login')
          } else {
            toast.error(message)
          }
        } finally {
          setIsLoading(false)
        }
      }

      fetchInvitation()
    }, [token, navigate, embedded])

    const onSubmit = async (data: AcceptInvitationFormData) => {
      if (!token) {
        toast.error('Invalid invitation token')
        return
      }

      try {
        setIsSubmitting(true)
        
        const response = await AuthApi.acceptInvitation({
          token,
          password: data.password,
        })

        // Auto-login the user
        localStorage.setItem('auth_token', response.access_token)
        localStorage.setItem('user', JSON.stringify(response.user))
        
        toast.success('Account created successfully! Welcome to FlowMastery.')
        
        if (onSuccess) {
          onSuccess()
        } else {
          navigate('/dashboard')
        }
      } catch (error: any) {
        const message = error.response?.data?.detail || 'Failed to create account'
        toast.error(message)
      } finally {
        setIsSubmitting(false)
      }
    }

    if (!token) {
      return null
    }

    if (isLoading) {
      return (
        <div ref={ref} className={embedded ? "py-16" : "min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100"}>
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Validating invitation...</p>
          </div>
        </div>
      )
    }

    if (!invitation) {
      return null
    }

    const containerClass = embedded 
      ? "container mx-auto px-4 py-16" 
      : "min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100 p-4"

    const cardClass = embedded 
      ? "w-full max-w-2xl mx-auto" 
      : "w-full max-w-md"

    return (
      <div ref={ref} className={containerClass}>
        <Card className={cardClass}>
          <CardHeader className="space-y-1">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center">
                <Mail className="w-6 h-6 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl lg:text-3xl font-bold text-center">
              {embedded ? "Complete Your Invitation" : "Accept Invitation"}
            </CardTitle>
            <CardDescription className="text-center">
              {embedded 
                ? "You're just one step away from joining FlowMastery" 
                : "Complete your account setup"
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Invitation Details */}
            <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
              <div className="flex items-center space-x-2 mb-4">
                <CheckCircle className="w-5 h-5 text-primary" />
                <span className="font-medium text-primary">Invitation Details</span>
              </div>
              <div className="grid grid-cols-1 gap-3 text-sm">
                <div className="flex items-center justify-between p-3 bg-background/50 rounded-md">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Email:</span>
                  </div>
                  <span className="font-medium">{invitation.email}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-background/50 rounded-md">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Role:</span>
                  </div>
                  <Badge variant={invitation.role === 'admin' ? 'default' : 'secondary'}>
                    {invitation.role === 'admin' ? 'Administrator' : 'Client User'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-background/50 rounded-md">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Expires:</span>
                  </div>
                  <span className="font-medium">
                    {new Date(invitation.expires_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Password Setup Form */}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Debug Section - Remove in production */}
              {process.env.NODE_ENV === 'development' && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded text-sm">
                  <strong>Debug Info:</strong>
                  <div>Form Valid: {isValid ? 'Yes' : 'No'}</div>
                  <div>Has Errors: {Object.keys(errors).length > 0 ? 'Yes' : 'No'}</div>
                  <div>Is Submitting: {isSubmitting ? 'Yes' : 'No'}</div>
                  <div>Password Length: {watchedValues.password?.length || 0}</div>
                  <div>Passwords Match: {watchedValues.password === watchedValues.confirmPassword ? 'Yes' : 'No'}</div>
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="password">Create Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Create a secure password (min 8 characters)"
                    {...register('password')}
                    className={errors.password ? 'border-red-500 pr-10' : 'pr-10'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
                {errors.password && (
                  <p className="text-sm text-red-500">{errors.password.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Confirm your password"
                    {...register('confirmPassword')}
                    className={errors.confirmPassword ? 'border-red-500 pr-10' : 'pr-10'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="text-sm text-red-500">{errors.confirmPassword.message}</p>
                )}
              </div>

              <Button
                type="submit"
                size="lg"
                className={`w-full transition-all duration-300 ${
                  isSubmitting || !isValid
                    ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-600/90 text-white shadow-lg hover:shadow-xl hover:-translate-y-1 cursor-pointer'
                }`}
                disabled={isSubmitting || !isValid}
              >
                {isSubmitting ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Creating account...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <UserPlus className="w-4 h-4" />
                    Complete Setup & Join FlowMastery
                  </div>
                )}
              </Button>
            </form>

            {!embedded && (
              <div className="text-center text-sm text-muted-foreground">
                <p>Already have an account? <a href="/login" className="text-primary hover:underline">Sign in</a></p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }
)

InvitationAcceptanceSection.displayName = 'InvitationAcceptanceSection'