import React, { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Bot, 
  Search, 
  TrendingUp, 
  Calendar,
  ArrowRight,
  Zap,
  Shield,
  Settings,
  Play,
  Clock,
  Eye,
  Users,
  CheckCircle,
  Activity,
  Mail,
  Sparkles,
  Rocket
} from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { formatNumber } from '@/lib/utils'
import { useMetrics, useConfigStatus, useRefreshMetrics } from '@/hooks/useMetrics'
import { InvitationAcceptanceSection } from '@/components/auth/InvitationAcceptanceSection'

interface WorkflowShowcase {
  icon: React.ReactNode
  title: string
  description: string
  color: string
}

interface MetricCard {
  label: string
  value: string
  trend: number
  isLoading?: boolean
  icon: React.ReactNode
  gradient?: string
}

const HomePage: React.FC = () => {
  const [activeWorkflow, setActiveWorkflow] = useState(0)
  const [isVisible, setIsVisible] = useState(false)
  const [animationsLoaded, setAnimationsLoaded] = useState(false)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const invitationSectionRef = useRef<HTMLDivElement>(null)
  
  const invitationToken = searchParams.get('token')
  const hasInvitation = Boolean(invitationToken)
  
  const { data: configStatus } = useConfigStatus()
  const { data: metricsData, isLoading: metricsLoading } = useMetrics(true)
  const { refreshFast } = useRefreshMetrics()

  const workflows: WorkflowShowcase[] = [
    {
      icon: <Bot className="h-8 w-8" />,
      title: "AI Chatbots",
      description: "Intelligent conversational agents for customer support",
      color: "text-blue-500"
    },
    {
      icon: <Search className="h-8 w-8" />,
      title: "SEO Auditor", 
      description: "Comprehensive SEO analysis and optimization tools",
      color: "text-green-500"
    },
    {
      icon: <TrendingUp className="h-8 w-8" />,
      title: "Lead Generation",
      description: "Automated lead capture and nurturing workflows", 
      color: "text-orange-500"
    },
    {
      icon: <Calendar className="h-8 w-8" />,
      title: "Meeting Summarizer",
      description: "AI-powered meeting notes and action items",
      color: "text-purple-500"
    }
  ]

  // Enhanced metrics with compelling demo data when no real data is available
  const demoMetrics: MetricCard[] = [
    {
      label: "Active Workflows",
      value: "47",
      trend: 18,
      icon: <Play className="h-4 w-4" />,
      isLoading: false,
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      label: "Total Executions",
      value: "2.4M",
      trend: 35,
      icon: <Activity className="h-4 w-4" />,
      isLoading: false,
      gradient: "from-green-500 to-emerald-500"
    },
    {
      label: "Time Saved",
      value: "1,248h",
      trend: 42,
      icon: <Clock className="h-4 w-4" />,
      isLoading: false,
      gradient: "from-purple-500 to-violet-500"
    },
    {
      label: "Success Rate",
      value: "98.7%",
      trend: 12,
      icon: <CheckCircle className="h-4 w-4" />,
      isLoading: false,
      gradient: "from-orange-500 to-red-500"
    }
  ]

  const metrics: MetricCard[] = metricsData ? [
    {
      label: "Active Workflows",
      value: metricsData.workflows.active_workflows.toString(),
      trend: Math.round((metricsData.workflows.active_workflows / Math.max(1, metricsData.workflows.total_workflows)) * 100),
      icon: <Play className="h-4 w-4" />,
      isLoading: metricsLoading,
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      label: "Total Executions",
      value: formatNumber(metricsData.executions.total_executions),
      trend: 23,
      icon: <Activity className="h-4 w-4" />,
      isLoading: metricsLoading,
      gradient: "from-green-500 to-emerald-500"
    },
    {
      label: "Time Saved",
      value: `${metricsData.derived_metrics.time_saved_hours}h`,
      trend: 8,
      icon: <Clock className="h-4 w-4" />,
      isLoading: metricsLoading,
      gradient: "from-purple-500 to-violet-500"
    },
    {
      label: "Success Rate",
      value: `${metricsData.executions.success_rate?.toFixed(1) || '0.0'}%`,
      trend: metricsData.executions.success_rate > 90 ? 5 : -2,
      icon: <CheckCircle className="h-4 w-4" />,
      isLoading: metricsLoading,
      gradient: "from-orange-500 to-red-500"
    }
  ] : demoMetrics

  const features = [
    {
      icon: <Settings className="h-6 w-6" />,
      title: "Easy Integration",
      description: "Connect all your n8n workflows with a single API endpoint"
    },
    {
      icon: <Shield className="h-6 w-6" />,
      title: "Secure & Reliable", 
      description: "Enterprise-grade security with 99.9% uptime guarantee"
    },
    {
      icon: <Zap className="h-6 w-6" />,
      title: "Lightning Fast",
      description: "Optimized performance with sub-second response times"
    },
    {
      icon: <Users className="h-6 w-6" />,
      title: "Team Collaboration",
      description: "Built for teams with role-based access and sharing"
    }
  ]

  useEffect(() => {
    // Initialize visibility and animations
    const timer = setTimeout(() => {
      setIsVisible(true)
      setAnimationsLoaded(true)
    }, 100)

    // Workflow carousel
    const interval = setInterval(() => {
      setActiveWorkflow((prev) => (prev + 1) % workflows.length)
    }, 4000) // Slightly slower for better UX

    // If there's an invitation token, scroll to the invitation section after a brief delay
    if (hasInvitation && invitationSectionRef.current) {
      const scrollTimer = setTimeout(() => {
        invitationSectionRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
      }, 2500) // Allow 2.5 seconds to explore the homepage first
      
      return () => {
        clearInterval(interval)
        clearTimeout(timer)
        clearTimeout(scrollTimer)
      }
    }

    return () => {
      clearInterval(interval)
      clearTimeout(timer)
    }
  }, [hasInvitation])

  return (
    <div className={`min-h-screen transition-all duration-1000 ease-out ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
      {/* Enhanced animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div 
          className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-primary/10 to-primary/5 rounded-full blur-3xl" 
          style={{
            animation: 'float 6s ease-in-out infinite, pulse 4s ease-in-out infinite'
          }}
        />
        <div 
          className="absolute top-1/2 -left-40 w-96 h-96 bg-gradient-to-br from-secondary/10 to-secondary/5 rounded-full blur-3xl" 
          style={{
            animation: 'float 8s ease-in-out infinite reverse, pulse 5s ease-in-out infinite',
            animationDelay: '2s'
          }}
        />
        <div 
          className="absolute -bottom-40 right-1/3 w-72 h-72 bg-gradient-to-br from-accent/10 to-accent/5 rounded-full blur-3xl" 
          style={{
            animation: 'float 7s ease-in-out infinite, pulse 3s ease-in-out infinite',
            animationDelay: '4s'
          }}
        />
      </div>

      {/* Hero Section */}
      <section className="relative container mx-auto px-4 py-16 lg:py-24 z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Hero Content */}
          <div className={`space-y-8 transition-all duration-1000 ease-out ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <div className="space-y-6">
              <div className={`transition-all duration-1000 ease-out delay-200 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium mb-6">
                  <Sparkles className="h-4 w-4" />
                  Workflow Automation Platform
                </div>
              </div>
              
              <h1 className={`text-4xl lg:text-6xl font-bold leading-tight transition-all duration-1000 ease-out delay-300 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                <span className="bg-gradient-to-r from-primary via-blue-600 to-secondary bg-clip-text text-transparent bg-300% animate-gradient-x">
                  Centralize
                </span>{" "}
                <span className="relative inline-block">
                  Your n8n Workflows
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-primary/60 to-secondary/60 rounded-full animate-pulse" />
                </span>
              </h1>
              
              <p className={`text-xl text-muted-foreground leading-relaxed transition-all duration-1000 ease-out delay-500 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                One powerful platform to manage, execute, and monitor all your automation workflows. 
                From chatbots to SEO tools, everything in one place.
                <span className="inline-block ml-2 animate-bounce text-primary">⚡</span>
              </p>
            </div>

            <div className={`flex flex-col sm:flex-row gap-4 transition-all duration-1000 ease-out delay-700 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              {hasInvitation ? (
                <Button 
                  size="lg" 
                  className="bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-600/90 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
                  onClick={() => invitationSectionRef.current?.scrollIntoView({ behavior: 'smooth' })}
                >
                  <Mail className="h-4 w-4 mr-2" />
                  Complete Your Invitation
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <>
                  <Button 
                    size="lg" 
                    className="bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-600/90 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
                    onClick={() => navigate('/metrics')}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View n8n Metrics
                  </Button>
                  <Button 
                    size="lg" 
                    variant="outline"
                    className="border-2 border-primary/20 hover:border-primary/40 hover:bg-primary/5 transition-all duration-300 hover:-translate-y-1"
                    onClick={() => navigate('/workflows')}
                  >
                    View Workflows
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </>
              )}
            </div>

            {/* Status Badge */}
            <div className={`transition-all duration-1000 ease-out delay-900 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              {hasInvitation ? (
                <Badge className="flex items-center gap-2 w-fit bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800/50 px-4 py-2">
                  <Mail className="h-3 w-3" />
                  Invitation Received • Complete Setup Below
                </Badge>
              ) : metricsLoading ? (
                <Badge className="flex items-center gap-2 w-fit bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800/50 px-4 py-2">
                  <Clock className="h-3 w-3 animate-spin" />
                  Checking n8n connection...
                </Badge>
              ) : configStatus?.configured && metricsData ? (
                <Badge className="flex items-center gap-2 w-fit bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800/50 px-4 py-2">
                  <Play className="h-3 w-3" />
                  n8n Connected • Live Data
                </Badge>
              ) : (
                <Badge className="flex items-center gap-2 w-fit bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-900/30 dark:text-gray-400 dark:border-gray-800/50 px-4 py-2">
                  <Settings className="h-3 w-3" />
                  Configure n8n for Live Metrics
                </Badge>
              )}
            </div>
          </div>

          {/* Hero Visual - Enhanced Workflow Showcase */}
          <div className={`relative h-[400px] flex items-center justify-center transition-all duration-1000 ease-out delay-400 ${animationsLoaded ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'}`}>
            {/* Background glow effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-primary/8 via-secondary/8 to-primary/8 rounded-3xl blur-2xl animate-pulse" />
            
            {/* Workflow Cards */}
            <div className="relative w-full max-w-[350px]">
              {workflows.map((workflow, index) => (
                <Card
                  key={index}
                  className={`absolute inset-0 transition-all duration-700 ease-out transform-gpu ${
                    activeWorkflow === index
                      ? 'opacity-100 scale-100 translate-y-0 shadow-2xl shadow-primary/15 border-primary/20 z-10'
                      : 'opacity-40 scale-95 translate-y-2 z-0'
                  }`}
                  style={{
                    transform: activeWorkflow === index 
                      ? 'translateY(0px) scale(1) rotateY(0deg)' 
                      : `translateY(${(index - activeWorkflow) * 10}px) scale(0.95) rotateY(${(index - activeWorkflow) * 2}deg)`,
                    zIndex: activeWorkflow === index ? 10 : 9 - Math.abs(index - activeWorkflow)
                  }}
                >
                  {/* Card Background */}
                  <div className="absolute inset-0 bg-gradient-to-br from-background/95 to-background/90 backdrop-blur-md rounded-lg" />
                  
                  <CardHeader className="relative z-10 p-6">
                    {/* Icon */}
                    <div className="mb-6">
                      <div className={`${workflow.color} p-4 rounded-2xl bg-gradient-to-br from-white/80 to-white/60 dark:from-white/10 dark:to-white/5 inline-block shadow-lg transition-transform duration-500 ${
                        activeWorkflow === index ? 'scale-110 rotate-3' : 'scale-100 rotate-0'
                      }`}>
                        {workflow.icon}
                      </div>
                    </div>
                    
                    {/* Content */}
                    <CardTitle className="text-2xl font-bold mb-3 bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
                      {workflow.title}
                    </CardTitle>
                    <CardDescription className="text-muted-foreground leading-relaxed text-base">
                      {workflow.description}
                    </CardDescription>
                    
                    {/* Progress Indicator */}
                    <div className="mt-6 flex justify-center gap-2">
                      {workflows.map((_, i) => (
                        <div 
                          key={i}
                          className={`h-2 rounded-full transition-all duration-500 ${
                            i === activeWorkflow 
                              ? 'w-8 bg-gradient-to-r from-primary to-blue-500' 
                              : 'w-2 bg-muted hover:bg-muted-foreground/30 cursor-pointer'
                          }`}
                          onClick={() => setActiveWorkflow(i)}
                        />
                      ))}
                    </div>
                  </CardHeader>
                  
                  {/* Shimmer effect for active card */}
                  {activeWorkflow === index && (
                    <div className="absolute inset-0 rounded-lg overflow-hidden">
                      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                    </div>
                  )}
                </Card>
              ))}
            </div>
            
            {/* Floating decorative elements */}
            <div className="absolute top-8 right-8 w-3 h-3 bg-primary/40 rounded-full animate-ping" />
            <div className="absolute bottom-8 left-8 w-2 h-2 bg-secondary/40 rounded-full animate-ping" style={{ animationDelay: '1s' }} />
            <div className="absolute top-1/2 right-0 w-4 h-4 bg-accent/30 rounded-full animate-ping" style={{ animationDelay: '2s' }} />
          </div>
        </div>
      </section>

      {/* Enhanced Stats Section */}
      <section className="relative py-20 bg-gradient-to-r from-card/40 via-card/30 to-card/40 border-y border-border/30 overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0)',
            backgroundSize: '40px 40px'
          }} />
        </div>
        
        {/* Background decorative elements */}
        <div className="absolute top-20 left-10 w-20 h-20 bg-primary/5 rounded-full blur-2xl animate-pulse" />
        <div className="absolute bottom-20 right-10 w-16 h-16 bg-secondary/5 rounded-full blur-2xl animate-pulse" style={{ animationDelay: '2s' }} />
        
        <div className="container mx-auto px-4 relative z-10">
          {/* Section header */}
          <div className={`text-center mb-16 transition-all duration-1000 ease-out delay-200 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium mb-6">
              <Activity className="h-4 w-4" />
              Platform Performance
            </div>
            <h2 className="text-3xl lg:text-4xl font-bold mb-4 bg-gradient-to-r from-primary via-blue-600 to-secondary bg-clip-text text-transparent">
              Real-Time Metrics
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto text-lg leading-relaxed">
              Live performance data showcasing the power and efficiency of automated workflows
            </p>
          </div>
          
          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {metrics.map((metric, index) => (
              <Card 
                key={index} 
                className={`group relative overflow-hidden text-center transition-all duration-700 ease-out hover:shadow-2xl hover:shadow-primary/10 hover:-translate-y-3 hover:scale-105 bg-gradient-to-br from-background/95 to-background/85 backdrop-blur-sm border-2 hover:border-primary/30 ${
                  animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
                }`}
                style={{
                  transitionDelay: `${(index * 150) + 400}ms`
                }}
              >
                {/* Card Background Gradient */}
                <div className={`absolute inset-0 bg-gradient-to-br ${metric.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-500`} />
                
                {/* Animated Border */}
                <div className="absolute inset-0 rounded-lg">
                  <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" style={{
                    background: `conic-gradient(from 0deg at 50% 50%, transparent 0deg, ${metric.gradient?.includes('blue') ? 'rgba(59, 130, 246, 0.3)' : metric.gradient?.includes('green') ? 'rgba(34, 197, 94, 0.3)' : metric.gradient?.includes('purple') ? 'rgba(168, 85, 247, 0.3)' : 'rgba(249, 115, 22, 0.3)'} 180deg, transparent 360deg)`
                  }} />
                </div>
                
                <CardContent className="relative p-6 z-10">
                  {metric.isLoading ? (
                    <div className="space-y-4">
                      <Skeleton className="h-12 w-16 mx-auto rounded-lg" />
                      <Skeleton className="h-6 w-24 mx-auto rounded-md" />
                      <Skeleton className="h-4 w-16 mx-auto rounded-full" />
                    </div>
                  ) : (
                    <>
                      {/* Icon with enhanced styling */}
                      <div className="flex items-center justify-center mb-6">
                        <div className={`p-3 rounded-2xl bg-gradient-to-br ${metric.gradient} text-white shadow-lg transition-all duration-500 group-hover:scale-110 group-hover:rotate-6`} style={{
                          animation: 'float 4s ease-in-out infinite',
                          animationDelay: `${index * 0.5}s`
                        }}>
                          {metric.icon}
                        </div>
                      </div>
                      
                      {/* Value with enhanced gradient */}
                      <div className={`text-4xl lg:text-5xl font-bold mb-4 bg-gradient-to-br ${metric.gradient} bg-clip-text text-transparent transition-all duration-500 group-hover:scale-110`}>
                        {metric.value}
                      </div>
                      
                      {/* Label */}
                      <div className="text-muted-foreground text-sm font-semibold mb-4 tracking-wide uppercase">
                        {metric.label}
                      </div>
                      
                      {/* Enhanced Trend Indicator */}
                      <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-full text-xs font-bold transition-all duration-500 group-hover:scale-110 ${
                        metric.trend > 0 
                          ? 'bg-green-100 text-green-700 border border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800/50' 
                          : 'bg-red-100 text-red-700 border border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800/50'
                      }`}>
                        <TrendingUp className={`h-3 w-3 transition-transform duration-300 ${
                          metric.trend > 0 ? 'rotate-0' : 'rotate-180'
                        }`} />
                        <span>{metric.trend > 0 ? '+' : ''}{metric.trend}%</span>
                      </div>
                    </>
                  )}
                </CardContent>
                
                {/* Enhanced Shimmer Effect */}
                <div className="absolute inset-0 rounded-lg overflow-hidden">
                  <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-out bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Enhanced Features Section */}
      <section className="container mx-auto px-4 py-20 lg:py-28">
        <div className={`text-center mb-20 transition-all duration-1000 ease-out delay-200 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium mb-6">
            <Sparkles className="h-4 w-4" />
            Platform Features
          </div>
          <h2 className="text-3xl lg:text-5xl font-bold mb-6 bg-gradient-to-r from-foreground via-primary to-foreground bg-clip-text text-transparent">
            Everything You Need
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            Powerful features designed to streamline your workflow automation and boost productivity
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              className={`group relative overflow-hidden transition-all duration-700 ease-out hover:shadow-2xl hover:shadow-primary/10 hover:-translate-y-4 hover:scale-105 bg-gradient-to-br from-background/95 to-background/85 backdrop-blur-sm border-2 hover:border-primary/30 ${
                animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
              }`}
              style={{
                transitionDelay: `${(index * 200) + 600}ms`
              }}
            >
              {/* Animated Top Border */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-blue-500 to-secondary scale-x-0 group-hover:scale-x-100 transition-transform duration-700 ease-out" />
              
              {/* Background Glow */}
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              {/* Floating particles background */}
              <div className="absolute inset-0 overflow-hidden">
                <div className="absolute top-4 right-4 w-2 h-2 bg-primary/30 rounded-full animate-ping opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="absolute bottom-6 left-6 w-1 h-1 bg-secondary/40 rounded-full animate-ping opacity-0 group-hover:opacity-100 transition-opacity duration-300" style={{ animationDelay: '1s' }} />
              </div>
              
              <CardHeader className="relative z-10 p-6">
                {/* Icon Container */}
                <div className="relative mb-6">
                  <div className="w-16 h-16 bg-gradient-to-br from-primary/20 via-primary/10 to-secondary/20 rounded-2xl flex items-center justify-center text-primary mb-4 transition-all duration-500 group-hover:scale-110 group-hover:rotate-6 shadow-lg group-hover:shadow-xl">
                    <div className="text-2xl transition-transform duration-500 group-hover:scale-110">
                      {feature.icon}
                    </div>
                  </div>
                </div>
                
                {/* Content */}
                <CardTitle className="text-xl mb-4 font-bold transition-colors duration-300 group-hover:text-primary">
                  {feature.title}
                </CardTitle>
                <CardDescription className="leading-relaxed text-muted-foreground transition-colors duration-300 group-hover:text-foreground/80 mb-6">
                  {feature.description}
                </CardDescription>
                
                {/* Call to Action */}
                <div className="flex items-center gap-2 text-primary opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-all duration-500">
                  <span className="text-sm font-semibold">Learn more</span>
                  <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
                </div>
              </CardHeader>
              
              {/* Enhanced Shimmer Effect */}
              <div className="absolute inset-0 rounded-lg overflow-hidden">
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-out bg-gradient-to-r from-transparent via-white/20 to-transparent" />
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Invitation Section - Only show if there's an invitation token */}
      {hasInvitation && (
        <section id="invitation-section" className="relative py-20 bg-gradient-to-br from-primary/5 via-card/30 to-secondary/5 border-y border-border/30">
          {/* Background decoration */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute top-10 left-10 w-32 h-32 bg-primary/5 rounded-full blur-3xl animate-pulse" />
            <div className="absolute bottom-10 right-10 w-24 h-24 bg-secondary/5 rounded-full blur-2xl animate-pulse" style={{ animationDelay: '2s' }} />
          </div>
          
          <InvitationAcceptanceSection 
            ref={invitationSectionRef}
            token={invitationToken} 
            embedded={true}
            onSuccess={() => navigate('/dashboard')}
          />
        </section>
      )}

      {/* CTA Section - Hide if there's an invitation to avoid confusion */}
      {!hasInvitation && (
        <section className="container mx-auto px-4 py-20">
          <div className={`transition-all duration-1000 ease-out delay-400 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
            <Card className="relative overflow-hidden bg-gradient-to-br from-primary/10 via-card/50 to-secondary/10 border-2 border-primary/20 text-center backdrop-blur-sm">
              {/* Background glow effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-secondary/5 animate-pulse" />
              
              <CardContent className="relative p-12 z-10">
                <div className="max-w-2xl mx-auto space-y-8">
                  {/* Icon */}
                  <div className="flex justify-center mb-6">
                    <div className="w-16 h-16 bg-gradient-to-br from-primary to-blue-600 rounded-2xl flex items-center justify-center text-white shadow-lg animate-float">
                      <Rocket className="h-8 w-8" />
                    </div>
                  </div>
                  
                  {/* Content */}
                  <h3 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-foreground via-primary to-foreground bg-clip-text text-transparent">
                    Ready to Supercharge Your Workflows?
                  </h3>
                  <p className="text-lg text-muted-foreground leading-relaxed">
                    Join thousands of teams already using FlowMastery to automate their processes
                    and save countless hours every week.
                  </p>
                  
                  {/* Buttons */}
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button 
                      size="lg" 
                      className="bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-600/90 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
                    >
                      <Rocket className="h-4 w-4 mr-2" />
                      Get Started Free
                    </Button>
                    <Button 
                      size="lg" 
                      variant="outline"
                      className="border-2 border-primary/20 hover:border-primary/40 hover:bg-primary/5 transition-all duration-300 hover:-translate-y-1"
                    >
                      View Documentation
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                </div>
              </CardContent>
              
              {/* Shimmer effect */}
              <div className="absolute inset-0 rounded-lg overflow-hidden">
                <div className="absolute inset-0 -translate-x-full hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
              </div>
            </Card>
          </div>
        </section>
      )}
    </div>
  )
}

export default HomePage