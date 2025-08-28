import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  BarChart3,
  Bot,
  Building2,
  Calendar,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FileText,
  Home,
  LogOut,
  Mail,
  Menu,
  MessageCircle,
  Settings,
  Shield,
  User,
  UserPlus,
  Users,
  Workflow,
  X,
  Zap,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { MetricsApi } from '@/services/metricsApi'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { DataSourceIndicator } from '@/components/ui/data-source-indicator'
import { 
  fadeInLeft, 
  fadeInRight, 
  navItemHover, 
  buttonTap, 
  slideUpModal,
  staggerContainer,
  staggerItem
} from '@/lib/animations'

interface DashboardLayoutProps {
  children: React.ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [hoveredItem, setHoveredItem] = useState<string | null>(null)
  const { user, logout, isAdmin, isClient } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  // Get user display name from user data or fallback to email
  const getUserDisplayName = () => {
    if (user?.first_name || user?.last_name) {
      return `${user.first_name || ''} ${user.last_name || ''}`.trim()
    }
    return user?.email?.split('@')[0] || 'User'
  }

  const getUserInitials = () => {
    if (user?.first_name) {
      const firstInitial = user.first_name.charAt(0).toUpperCase()
      const lastInitial = user?.last_name?.charAt(0).toUpperCase() || ''
      return firstInitial + lastInitial
    }
    return user?.email?.split('@')[0].charAt(0).toUpperCase() || 'U'
  }

  // Fetch metrics data to get last_updated timestamp
  const { data: metricsData } = useQuery({
    queryKey: isAdmin ? ['admin-metrics'] : ['my-metrics'],
    queryFn: isAdmin ? MetricsApi.getAllClientsMetrics : MetricsApi.getMyMetrics,
    refetchInterval: 300000, // 5 minutes
    staleTime: 240000, // 4 minutes
  })

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const workflowSubOptions = [
    {
      name: 'Chatbot Workflows',
      href: '/workflows/chatbot',
      icon: MessageCircle,
      description: 'AI-powered chatbot interfaces'
    },
    {
      name: 'Email Automation',
      href: '/workflows/email',
      icon: Mail,
      description: 'Automated email sequences'
    },
    {
      name: 'Calendar Integration',
      href: '/workflows/calendar',
      icon: Calendar,
      description: 'Schedule and booking workflows'
    },
    {
      name: 'Document Processing',
      href: '/workflows/documents',
      icon: FileText,
      description: 'Automated document workflows'
    },
    {
      name: 'Custom Workflows',
      href: '/workflows/custom',
      icon: Bot,
      description: 'Build your own workflows'
    }
  ]

  const navigation = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: Home,
      show: true,
      description: 'Overview & insights'
    },
    {
      name: 'Workflows',
      href: '/workflows',
      icon: Activity,
      show: true,
      description: 'Manage workflows',
      hasSubMenu: true,
      subOptions: workflowSubOptions
    },
    {
      name: 'Metrics',
      href: '/metrics',
      icon: Activity,
      show: true,
      description: 'Workflow analytics'
    },
    {
      name: 'Clients',
      href: '/admin/clients',
      icon: Building2,
      show: isAdmin,
      description: 'Manage clients'
    },
    {
      name: 'Users & Invitations',
      href: '/admin/users',
      icon: Users,
      show: isAdmin,
      description: 'User management'
    },
  ]

  const isActive = (href: string) => {
    return location.pathname === href || location.pathname.startsWith(href + '/')
  }

  const SidebarContent = () => (
    <div 
      className="flex flex-col h-full dashboard-sidebar backdrop-blur-md"
      style={{ width: sidebarCollapsed ? '80px' : '320px' }}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-border/50 justify-between">
        <div className={`flex items-center ${sidebarCollapsed ? 'justify-center w-full' : 'space-x-3'}`}>
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary/80 rounded-xl flex items-center justify-center shadow-lg">
            <Zap className="w-6 h-6 text-primary-foreground" />
          </div>
          {!sidebarCollapsed && (
            <div>
              <h1 className="text-xl font-bold text-gradient">FlowMastery</h1>
              <p className="text-xs text-muted-foreground">Workflow Analytics</p>
            </div>
          )}
        </div>
        
        {/* Collapse button - only on desktop */}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="hidden lg:flex items-center justify-center w-8 h-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.filter(item => item.show).map((item, index) => {
          const isItemActive = isActive(item.href)
          return (
            <div
              key={item.name}
              className="relative"
            >
              <div
                onMouseEnter={() => item.hasSubMenu && !sidebarCollapsed && setHoveredItem(item.name)}
                onMouseLeave={() => item.hasSubMenu && setHoveredItem(null)}
              >
                <Link
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  title={sidebarCollapsed ? item.name : undefined}
                >
                  <motion.div
                    className={`
                      group flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'space-x-3 px-4'} py-3 rounded-xl text-sm font-medium
                      transition-all duration-200 cursor-pointer
                      ${isItemActive
                        ? 'dashboard-nav-item active text-primary bg-primary/10 border border-primary/20 shadow-sm'
                        : 'dashboard-nav-item text-muted-foreground hover:text-foreground hover:bg-accent/50'
                      }
                    `}
                    variants={navItemHover}
                    initial="rest"
                    whileHover="hover"
                    whileTap={{ scale: 0.98 }}
                  >
                    <motion.div
                      className={`
                        p-1.5 rounded-lg transition-colors
                        ${isItemActive 
                          ? 'bg-primary/20 text-primary' 
                          : 'bg-muted/50 text-muted-foreground group-hover:bg-accent group-hover:text-foreground'
                        }
                      `}
                      whileHover={{ scale: 1.1 }}
                    >
                      <item.icon className="w-4 h-4" />
                    </motion.div>
                    {!sidebarCollapsed && (
                      <div className="flex-1">
                        <div className="font-medium flex items-center">
                          {item.name}
                          {item.hasSubMenu && (
                            <ChevronDown className={`w-3 h-3 ml-2 text-muted-foreground transition-transform ${
                              hoveredItem === item.name ? 'rotate-180' : ''
                            }`} />
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">{item.description}</div>
                      </div>
                    )}
                    {isItemActive && !sidebarCollapsed && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="w-2 h-2 bg-primary rounded-full"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                      />
                    )}
                    {isItemActive && sidebarCollapsed && (
                      <motion.div
                        className="absolute right-1 w-1 h-8 bg-primary rounded-full"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                      />
                    )}
                  </motion.div>
                </Link>
                
                {/* Submenu - Simple show/hide without complex animations */}
                {item.hasSubMenu && hoveredItem === item.name && !sidebarCollapsed && (
                  <div className="mt-2 ml-4 bg-background/95 backdrop-blur-md border border-border/50 rounded-lg shadow-lg">
                    <div className="p-2">
                      <div className="space-y-1">
                        {item.subOptions?.map((subOption, subIndex) => (
                          <Link
                            key={subOption.name}
                            to={subOption.href}
                            onClick={() => {
                              setSidebarOpen(false)
                              setHoveredItem(null)
                            }}
                          >
                            <div className="flex items-center space-x-3 px-3 py-2 rounded-lg text-sm hover:bg-accent/50 transition-colors cursor-pointer group">
                              <div className="p-1.5 rounded-md bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors flex-shrink-0">
                                <subOption.icon className="w-3 h-3" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-foreground group-hover:text-primary transition-colors truncate">
                                  {subOption.name}
                                </div>
                                <div className="text-xs text-muted-foreground truncate">
                                  {subOption.description}
                                </div>
                              </div>
                            </div>
                          </Link>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </nav>


    </div>
  )

  return (
    <div className="min-h-screen dashboard-page">
      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div 
              className="fixed inset-0 z-40 lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div 
                className="fixed inset-0 bg-black/50 backdrop-blur-sm" 
                onClick={() => setSidebarOpen(false)} 
              />
            </motion.div>
            <motion.div 
              className="fixed inset-y-0 left-0 z-50 flex w-80 flex-col lg:hidden"
              variants={slideUpModal}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <SidebarContent />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Desktop sidebar */}
      <motion.div 
        className={`hidden lg:fixed lg:inset-y-0 lg:flex lg:flex-col transition-all duration-300 ${sidebarCollapsed ? 'lg:w-20' : 'lg:w-80'}`}
        variants={fadeInLeft}
        initial="initial"
        animate="animate"
      >
        <SidebarContent />
      </motion.div>

      {/* Main content */}
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-80'}`}>
        {/* Top bar */}
        <motion.div 
          className="sticky top-0 z-30 flex h-16 items-center justify-between dashboard-header backdrop-blur-md px-4 sm:px-6 lg:px-8"
          variants={fadeInRight}
          initial="initial"
          animate="animate"
        >
          <div className="flex items-center space-x-4">
            <motion.button
              onClick={() => setSidebarOpen(true)}
              className="text-muted-foreground hover:text-foreground lg:hidden transition-colors p-2 rounded-lg hover:bg-accent/50"
              variants={buttonTap}
              whileTap="tap"
            >
              <Menu className="w-6 h-6" />
            </motion.button>
            
            <DataSourceIndicator 
              compact={true} 
              lastUpdated={metricsData?.last_updated}
              className=""
            />
          </div>

          <div className="flex items-center space-x-4">
            
            <ThemeToggle />
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <motion.div
                  variants={buttonTap}
                  whileTap="tap"
                >
                  <Button variant="ghost" size="sm" className="flex items-center space-x-3 rounded-xl p-2 h-auto">
                    {/* Enhanced Avatar */}
                    <div className="w-10 h-10 bg-gradient-to-br from-primary/20 to-accent/20 rounded-full flex items-center justify-center border-2 border-background shadow-lg">
                      <span className="text-lg font-bold text-foreground">
                        {getUserInitials()}
                      </span>
                    </div>
                    
                    {/* User Info - Hidden on mobile */}
                    <div className="hidden md:flex flex-col items-start text-left">
                      <span className="text-sm font-medium text-foreground">
                        {getUserDisplayName()}
                      </span>
                      <span className="text-xs text-muted-foreground capitalize">
                        {user?.role}
                      </span>
                    </div>
                    
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  </Button>
                </motion.div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-72">
                {/* User Profile Header */}
                <div className="px-4 py-3 border-b border-border">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-accent/20 rounded-full flex items-center justify-center border-2 border-background shadow-lg">
                      <span className="text-xl font-bold text-foreground">
                        {getUserInitials()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-semibold text-foreground truncate">
                        {getUserDisplayName()}
                      </h4>
                      <p className="text-xs text-muted-foreground truncate">
                        {user?.email}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <div className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          user?.role === 'admin' 
                            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                            : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                        }`}>
                          {user?.role?.charAt(0).toUpperCase()}{user?.role?.slice(1)}
                        </div>
                        {user?.is_active && (
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Account Details */}
                <div className="px-4 py-3 border-b border-border">
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <User className="w-3 h-3" />
                        User ID
                      </span>
                      <span className="font-medium">#{user?.id}</span>
                    </div>
                    {user?.client_id && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground flex items-center gap-1">
                          <Building2 className="w-3 h-3" />
                          Client ID
                        </span>
                        <span className="font-medium">#{user?.client_id}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        Member since
                      </span>
                      <span className="font-medium">
                        {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { 
                          month: 'short', 
                          year: 'numeric' 
                        }) : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Menu Items */}
                <div className="py-1">
                  <DropdownMenuItem 
                    onClick={() => navigate('/settings')}
                    className="flex items-center px-4 py-2 cursor-pointer"
                  >
                    <Settings className="w-4 h-4 mr-3 text-muted-foreground" />
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">Settings</span>
                      <span className="text-xs text-muted-foreground">Account preferences</span>
                    </div>
                  </DropdownMenuItem>
                </div>
                
                <DropdownMenuSeparator />
                
                <div className="py-1">
                  <DropdownMenuItem 
                    onClick={handleLogout} 
                    className="flex items-center px-4 py-2 cursor-pointer text-destructive focus:text-destructive"
                  >
                    <LogOut className="w-4 h-4 mr-3" />
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">Sign out</span>
                      <span className="text-xs text-muted-foreground">Sign out of your account</span>
                    </div>
                  </DropdownMenuItem>
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </motion.div>

        {/* Page content */}
        <motion.main 
          className="flex-1 min-h-0"
          variants={fadeInRight}
          initial="initial"
          animate="animate"
          transition={{ delay: 0.1 }}
        >
          {children}
        </motion.main>
      </div>
    </div>
  )
}