import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart3,
  Building2,
  LogOut,
  Menu,
  Settings,
  Users,
  X,
  UserPlus,
  Home,
  ChevronDown,
  Activity,
  Zap,
  ChevronLeft,
  ChevronRight
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
  const { user, logout, isAdmin, isClient } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

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
      description: 'Manage workflows'
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
    <motion.div 
      className="flex flex-col h-full dashboard-sidebar backdrop-blur-md"
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      style={{ width: sidebarCollapsed ? '80px' : '320px' }}
    >
      {/* Logo */}
      <motion.div 
        variants={staggerItem}
        className="flex items-center h-16 px-6 border-b border-border/50 justify-between"
      >
        <div className={`flex items-center ${sidebarCollapsed ? 'justify-center w-full' : 'space-x-3'}`}>
          <motion.div 
            className="w-10 h-10 bg-gradient-to-br from-primary to-primary/80 rounded-xl flex items-center justify-center shadow-lg"
            whileHover={{ scale: 1.05, rotate: 5 }}
            whileTap={{ scale: 0.95 }}
          >
            <Zap className="w-6 h-6 text-primary-foreground" />
          </motion.div>
          {!sidebarCollapsed && (
            <div>
              <h1 className="text-xl font-bold text-gradient">FlowMastery</h1>
              <p className="text-xs text-muted-foreground">Workflow Analytics</p>
            </div>
          )}
        </div>
        
        {/* Collapse button - only on desktop */}
        <motion.button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="hidden lg:flex items-center justify-center w-8 h-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
          variants={buttonTap}
          whileTap="tap"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </motion.button>
      </motion.div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.filter(item => item.show).map((item, index) => {
          const isItemActive = isActive(item.href)
          return (
            <motion.div
              key={item.name}
              variants={staggerItem}
              custom={index}
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
                      <div className="font-medium">{item.name}</div>
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
            </motion.div>
          )
        })}
      </nav>


    </motion.div>
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
            <div className="hidden sm:block text-sm text-muted-foreground">
              Welcome back, 
              <span className="font-semibold text-foreground">
                {user?.email?.split('@')[0]}
              </span>
            </div>
            
            <ThemeToggle />
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <motion.div
                  variants={buttonTap}
                  whileTap="tap"
                >
                  <Button variant="ghost" size="sm" className="flex items-center space-x-2 rounded-xl">
                    <div className="w-8 h-8 bg-gradient-to-br from-primary/20 to-accent/20 rounded-lg flex items-center justify-center">
                      <span className="text-sm font-semibold text-foreground">
                        {user?.email?.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <ChevronDown className="w-4 h-4" />
                  </Button>
                </motion.div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  {user?.email}
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/settings')}>
                  <Settings className="w-4 h-4 mr-3" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                  <LogOut className="w-4 h-4 mr-3" />
                  Sign out
                </DropdownMenuItem>
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