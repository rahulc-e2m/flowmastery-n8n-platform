import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  User, 
  Mail, 
  Shield, 
  Calendar, 
  Clock, 
  Building2,
  Edit2,
  Save,
  X,
  Camera,
  UserCheck
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { AuthApi } from '@/services/authApi'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from 'sonner'
import { staggerContainer, staggerItem } from '@/lib/animations'

export function SettingsPage() {
  const { user } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  
  // Initialize form data from user object
  const [formData, setFormData] = useState({
    firstName: user?.first_name || '',
    lastName: user?.last_name || '',
  })
  
  // Update form data when user changes
  useEffect(() => {
    if (user) {
      setFormData({
        firstName: user.first_name || '',
        lastName: user.last_name || '',
      })
    }
  }, [user])

  const handleSave = async () => {
    if (!user) return
    
    try {
      setIsLoading(true)
      
      // Call the API to update the user profile
      await AuthApi.updateProfile({
        first_name: formData.firstName.trim() || undefined,
        last_name: formData.lastName.trim() || undefined,
      })
      
      // Update the auth context by refreshing the current user
      try {
        await AuthApi.getCurrentUser()
        
        // Force a re-login to update the context
        // This is a simple way to refresh the user context
        window.location.reload()
      } catch (error) {
        console.error('Error refreshing user data:', error)
      }
      
      toast.success('Profile updated successfully!')
      setIsEditing(false)
    } catch (error: any) {
      console.error('Error updating profile:', error)
      const message = error.response?.data?.detail || 'Failed to update profile'
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancel = () => {
    if (user) {
      setFormData({
        firstName: user.first_name || '',
        lastName: user.last_name || '',
      })
    }
    setIsEditing(false)
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
      case 'client':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
    }
  }

  const getDisplayName = () => {
    if (user?.first_name || user?.last_name) {
      return `${user.first_name || ''} ${user.last_name || ''}`.trim()
    }
    return user?.email?.split('@')[0] || 'User'
  }

  const getInitials = () => {
    if (user?.first_name) {
      const firstInitial = user.first_name.charAt(0).toUpperCase()
      const lastInitial = user?.last_name?.charAt(0).toUpperCase() || ''
      return firstInitial + lastInitial
    }
    return user?.email?.split('@')[0].charAt(0).toUpperCase() || 'U'
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading user data...</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div 
      className="container mx-auto p-6 max-w-4xl"
      variants={staggerContainer}
      initial="initial"
      animate="animate"
    >
      <motion.div variants={staggerItem}>
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-2">
            Manage your account settings and preferences
          </p>
        </div>
      </motion.div>

      <div className="grid gap-6">
        {/* Profile Section */}
        <motion.div variants={staggerItem}>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <User className="w-5 h-5" />
                    Profile Information
                  </CardTitle>
                  <CardDescription>
                    Your personal account information and details
                  </CardDescription>
                </div>
                {!isEditing ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                    className="flex items-center gap-2"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCancel}
                      className="flex items-center gap-2"
                    >
                      <X className="w-4 h-4" />
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSave}
                      disabled={isLoading}
                      className="flex items-center gap-2"
                    >
                      {isLoading ? (
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Save className="w-4 h-4" />
                      )}
                      {isLoading ? 'Saving...' : 'Save'}
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Avatar Section */}
              <div className="flex items-center gap-6">
                <div className="relative">
                  <div className="w-24 h-24 bg-gradient-to-br from-primary/20 to-accent/20 rounded-full flex items-center justify-center border-4 border-background shadow-lg">
                    <span className="text-3xl font-bold text-foreground">
                      {getInitials()}
                    </span>
                  </div>
                  <Button
                    size="sm"
                    variant="secondary"
                    className="absolute -bottom-2 -right-2 rounded-full w-8 h-8 p-0 shadow-md"
                    disabled
                  >
                    <Camera className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold">
                    {getDisplayName()}
                  </h3>
                  <p className="text-muted-foreground">{user.email}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge className={getRoleColor(user.role)}>
                      {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                    </Badge>
                    {user.is_active && (
                      <Badge variant="outline" className="text-green-600 border-green-600">
                        <UserCheck className="w-3 h-3 mr-1" />
                        Active
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              <div className="border-t border-border my-4" />

              {/* Profile Details */}
              <div className="grid gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="firstName" className="flex items-center gap-2">
                      <User className="w-4 h-4" />
                      First Name
                    </Label>
                    {isEditing ? (
                      <Input
                        id="firstName"
                        type="text"
                        value={formData.firstName}
                        onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                        placeholder="Enter your first name"
                        disabled={isLoading}
                      />
                    ) : (
                      <div className="p-2 bg-muted/50 rounded-md text-sm">
                        {user.first_name || 'Not set'}
                      </div>
                    )}
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="lastName" className="flex items-center gap-2">
                      <User className="w-4 h-4" />
                      Last Name
                    </Label>
                    {isEditing ? (
                      <Input
                        id="lastName"
                        type="text"
                        value={formData.lastName}
                        onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                        placeholder="Enter your last name"
                        disabled={isLoading}
                      />
                    ) : (
                      <div className="p-2 bg-muted/50 rounded-md text-sm">
                        {user.last_name || 'Not set'}
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label className="flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    Email Address
                  </Label>
                  <div className="p-2 bg-muted/30 rounded-md text-sm border border-dashed">
                    <div className="flex items-center justify-between">
                      <span>{user.email}</span>
                      <span className="text-xs text-muted-foreground">Read-only</span>
                    </div>
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label className="flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    User Role
                  </Label>
                  <div className="p-2 bg-muted/50 rounded-md text-sm">
                    {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Account Created
                  </Label>
                  <div className="p-2 bg-muted/50 rounded-md text-sm">
                    {formatDate(user.created_at)}
                  </div>
                </div>

                {user.last_login && (
                  <div className="grid gap-2">
                    <Label className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Last Login
                    </Label>
                    <div className="p-2 bg-muted/50 rounded-md text-sm">
                      {formatDate(user.last_login)}
                    </div>
                  </div>
                )}

                {user.client_id && (
                  <div className="grid gap-2">
                    <Label className="flex items-center gap-2">
                      <Building2 className="w-4 h-4" />
                      Client ID
                    </Label>
                    <div className="p-2 bg-muted/50 rounded-md text-sm">
                      {user.client_id}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Account Security Section */}
        <motion.div variants={staggerItem}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Account Security
              </CardTitle>
              <CardDescription>
                Manage your account security settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <h4 className="font-medium">Change Password</h4>
                    <p className="text-sm text-muted-foreground">
                      Update your password to keep your account secure
                    </p>
                  </div>
                  <Button variant="outline" disabled>
                    Change Password
                  </Button>
                </div>
                
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <h4 className="font-medium">Two-Factor Authentication</h4>
                    <p className="text-sm text-muted-foreground">
                      Add an extra layer of security to your account
                    </p>
                  </div>
                  <Button variant="outline" disabled>
                    Enable 2FA
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Account Information */}
        <motion.div variants={staggerItem}>
          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
              <CardDescription>
                Additional details about your account
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm font-medium">User ID</span>
                  <span className="text-sm text-muted-foreground">#{user.id}</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm font-medium">Account Status</span>
                  <Badge variant={user.is_active ? "default" : "secondary"}>
                    {user.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm font-medium">Account Type</span>
                  <span className="text-sm text-muted-foreground capitalize">{user.role}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  )
}