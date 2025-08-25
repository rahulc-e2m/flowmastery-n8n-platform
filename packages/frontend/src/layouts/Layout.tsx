import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Zap, Bot, BarChart3, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Chatbots', href: '/chatbots', icon: Bot },
    { name: 'Metrics', href: '/metrics', icon: BarChart3 },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-[600px] h-[600px] bg-gradient-primary rounded-full filter blur-[80px] opacity-20 -top-[200px] -left-[200px] animate-float" />
        <div className="absolute w-[400px] h-[400px] bg-gradient-secondary rounded-full filter blur-[80px] opacity-20 top-1/2 -right-[100px] animate-float" style={{ animationDelay: '5s' }} />
        <div className="absolute w-[300px] h-[300px] bg-gradient-tertiary rounded-full filter blur-[80px] opacity-20 -bottom-[100px] left-[30%] animate-float" style={{ animationDelay: '10s' }} />
        
        {/* Grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px)',
            backgroundSize: '50px 50px'
          }}
        />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-border/40 backdrop-blur-sm bg-background/80">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2 text-xl font-bold">
              <Zap className="h-8 w-8 text-primary animate-pulse" />
              <span className="bg-gradient-primary bg-clip-text text-transparent">
                WorkflowHub
              </span>
            </Link>

            <div className="flex items-center space-x-1">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                
                return (
                  <Button
                    key={item.name}
                    asChild
                    variant={isActive ? "default" : "ghost"}
                    size="sm"
                    className={cn(
                      "transition-all duration-200",
                      isActive && "bg-primary/10 text-primary border border-primary/20"
                    )}
                  >
                    <Link to={item.href} className="flex items-center space-x-2">
                      <Icon className="h-4 w-4" />
                      <span>{item.name}</span>
                    </Link>
                  </Button>
                )
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10">
        {children}
      </main>
    </div>
  )
}

export default Layout