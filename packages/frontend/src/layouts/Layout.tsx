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
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Enhanced Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Primary floating orbs with enhanced animations */}
        <div className="absolute w-[500px] h-[500px] bg-gradient-to-r from-primary/20 to-purple-500/15 rounded-full filter blur-[100px] opacity-30 -top-[200px] -left-[200px] animate-float-slow" />
        <div className="absolute w-[350px] h-[350px] bg-gradient-to-r from-blue-500/15 to-primary/20 rounded-full filter blur-[80px] opacity-25 top-1/2 -right-[100px] animate-float" style={{ animationDelay: '3s' }} />
        <div className="absolute w-[400px] h-[400px] bg-gradient-to-r from-purple-500/10 to-pink-500/15 rounded-full filter blur-[90px] opacity-20 -bottom-[150px] left-[20%] animate-float-slow" style={{ animationDelay: '7s' }} />
        
        {/* Secondary smaller orbs for depth */}
        <div className="absolute w-[250px] h-[250px] bg-gradient-to-r from-cyan-500/10 to-blue-500/15 rounded-full filter blur-[60px] opacity-25 top-[20%] left-[60%] animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute w-[200px] h-[200px] bg-gradient-to-r from-indigo-500/10 to-purple-500/15 rounded-full filter blur-[50px] opacity-20 bottom-[30%] right-[70%] animate-float-slow" style={{ animationDelay: '5s' }} />
        
        {/* Animated mesh gradient overlay */}
        <div className="absolute inset-0 opacity-[0.03] bg-gradient-to-br from-primary/20 via-transparent to-purple-500/20 animate-gradient-shift" />
        
        {/* Subtle grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px)',
            backgroundSize: '60px 60px'
          }}
        />
        
        {/* Floating particles */}
        <div className="absolute top-[20%] left-[10%] w-2 h-2 bg-primary/30 rounded-full animate-float" style={{ animationDelay: '1s' }} />
        <div className="absolute top-[60%] right-[20%] w-1.5 h-1.5 bg-purple-500/40 rounded-full animate-float-slow" style={{ animationDelay: '4s' }} />
        <div className="absolute bottom-[40%] left-[70%] w-1 h-1 bg-blue-500/50 rounded-full animate-float" style={{ animationDelay: '6s' }} />
        
        {/* Animated geometric shapes */}
        <div className="absolute top-[30%] right-[30%] w-3 h-3 border border-primary/20 rotate-45 animate-gentle-wave" style={{ animationDelay: '2s' }} />
        <div className="absolute bottom-[60%] left-[40%] w-2 h-2 border border-purple-500/20 animate-breathe" style={{ animationDelay: '8s' }} />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-border/20 backdrop-blur-md bg-background/60 shadow-sm">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2 text-xl font-bold group">
              <Zap className="h-8 w-8 text-primary animate-pulse group-hover:animate-bounce transition-all duration-300" />
              <span className="bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent hover:from-purple-600 hover:to-primary transition-all duration-500">
                FlowMastery
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
      <main className="relative z-10 backdrop-blur-[0.5px]">
        {children}
      </main>
    </div>
  )
}

export default Layout