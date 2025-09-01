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
  // Only fetch metrics if user has invitation token (suggesting they might be authenticated soon)
  const { data: metricsData, isLoading: metricsLoading } = useMetrics(true, hasInvitation)
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

  // Landing page metrics (for non-invitation users)
  const landingPageMetrics: MetricCard[] = [
    {
      label: "Enterprise Clients",
      value: "500+",
      trend: 25,
      icon: <Users className="h-4 w-4" />,
      isLoading: false,
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      label: "Workflows Automated",
      value: "50K+",
      trend: 40,
      icon: <Activity className="h-4 w-4" />,
      isLoading: false,
      gradient: "from-green-500 to-emerald-500"
    },
    {
      label: "Hours Saved Daily",
      value: "10K+",
      trend: 35,
      icon: <Clock className="h-4 w-4" />,
      isLoading: false,
      gradient: "from-purple-500 to-violet-500"
    },
    {
      label: "Uptime Guarantee",
      value: "99.9%",
      trend: 12,
      icon: <CheckCircle className="h-4 w-4" />,
      isLoading: false,
      gradient: "from-orange-500 to-red-500"
    }
  ]

  const metrics: MetricCard[] = hasInvitation 
    ? (metricsData ? [
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
      ] : demoMetrics)
    : landingPageMetrics

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

    return () => {
      clearInterval(interval)
      clearTimeout(timer)
    }
  }, [])

  // Separate effect for invitation scrolling to avoid conflicts
  useEffect(() => {
    if (hasInvitation && invitationSectionRef.current && animationsLoaded) {
      const scrollTimer = setTimeout(() => {
        invitationSectionRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
      }, 1500) // Reduced delay for better UX
      
      return () => clearTimeout(scrollTimer)
    }
  }, [hasInvitation, animationsLoaded])

  return (
    <div className={`min-h-screen transition-all duration-1000 ease-out ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
      {/* Enhanced animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div 
          className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-primary/12 to-blue-500/8 animate-morphing-blob animate-float-slow blur-3xl" 
          style={{
            animationDelay: '0s'
          }}
        />
        <div 
          className="absolute top-1/2 -left-40 w-96 h-96 bg-gradient-to-br from-purple-500/10 to-pink-500/8 animate-morphing-blob animate-float-slow blur-3xl" 
          style={{
            animationDelay: '3s',
            animationDirection: 'reverse'
          }}
        />
        <div 
          className="absolute -bottom-40 right-1/3 w-72 h-72 bg-gradient-to-br from-emerald-500/10 to-cyan-500/8 animate-morphing-blob animate-float-slow blur-3xl" 
          style={{
            animationDelay: '6s'
          }}
        />
        <div 
          className="absolute top-20 left-1/4 w-32 h-32 bg-gradient-to-br from-yellow-400/8 to-orange-500/6 animate-float blur-2xl" 
          style={{
            animationDelay: '1s'
          }}
        />
        <div 
          className="absolute bottom-1/4 right-20 w-24 h-24 bg-gradient-to-br from-indigo-500/8 to-purple-600/6 animate-breathe blur-2xl" 
          style={{
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
                <span className="bg-gradient-to-r from-primary via-blue-600 to-purple-600 to-secondary bg-clip-text text-transparent bg-[length:400%_400%] animate-gradient-shift">
                  Centralize
                </span>{" "}
                <span className="relative inline-block">
                  Your n8n Workflows
                  <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-primary/60 via-blue-500/60 to-purple-500/60 rounded-full animate-gradient-x" />
                  {/* Sparkle effects */}
                  <div className="absolute -top-2 -right-2 w-2 h-2 bg-yellow-400 rounded-full animate-sparkle" style={{ animationDelay: '0.5s' }} />
                  <div className="absolute top-1/2 -left-3 w-1 h-1 bg-blue-400 rounded-full animate-sparkle" style={{ animationDelay: '1.2s' }} />
                  <div className="absolute -bottom-1 right-1/4 w-1.5 h-1.5 bg-purple-400 rounded-full animate-sparkle" style={{ animationDelay: '2s' }} />
                </span>
              </h1>
              
              <p className={`text-xl text-muted-foreground leading-relaxed transition-all duration-1000 ease-out delay-500 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                One powerful platform to manage, execute, and monitor all your automation workflows. 
                From chatbots to SEO tools, everything in one place.
                <span className="inline-block ml-2 animate-wiggle text-primary hover:animate-bounce cursor-pointer">⚡</span>
              </p>
            </div>

            <div className={`flex flex-col sm:flex-row gap-4 transition-all duration-1000 ease-out delay-700 ${animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              {hasInvitation ? (
                <>
                  <Button 
                    size="lg" 
                    className="bg-gradient-to-r from-primary via-blue-600 to-purple-600 hover:from-primary/90 hover:via-blue-600/90 hover:to-purple-600/90 text-white shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 hover:scale-105 animate-pulse-glow group"
                    onClick={() => navigate(`/accept-invitation?token=${invitationToken}`)}
                  >
                    <Mail className="h-4 w-4 mr-2 group-hover:animate-wiggle" />
                    Accept Invitation & Join
                    <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform duration-300" />
                  </Button>
                  <Button 
                    size="lg" 
                    variant="outline"
                    className="border-2 border-primary/20 hover:border-primary/40 hover:bg-primary/5 transition-all duration-500 hover:-translate-y-2 hover:scale-105 group animate-card-hover"
                    onClick={() => invitationSectionRef.current?.scrollIntoView({ behavior: 'smooth' })}
                  >
                    Learn More
                    <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform duration-300" />
                  </Button>
                </>
              ) : (
                <>
                  <Button 
                    size="lg" 
                    className="bg-gradient-to-r from-primary via-blue-600 to-purple-600 hover:from-primary/90 hover:via-blue-600/90 hover:to-purple-600/90 text-white shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 hover:scale-105 animate-pulse-glow group"
                    onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
                  >
                    <Rocket className="h-4 w-4 mr-2 group-hover:animate-wiggle" />
                    Discover FlowMastery
                    <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform duration-300" />
                  </Button>
                  <Button 
                    size="lg" 
                    variant="outline"
                    className="border-2 border-primary/20 hover:border-primary/40 hover:bg-primary/5 transition-all duration-500 hover:-translate-y-2 hover:scale-105 group animate-card-hover"
                    onClick={() => navigate('/login')}
                  >
                    <Users className="h-4 w-4 mr-2 group-hover:animate-wiggle" />
                    Team Access
                    <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform duration-300" />
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
              ) : (
                <Badge className="flex items-center gap-2 w-fit bg-primary/10 text-primary border-primary/20 px-4 py-2">
                  <Sparkles className="h-3 w-3" />
                  Enterprise Workflow Automation Platform
                </Badge>
              )}
            </div>
          </div>

          {/* Hero Visual - Enhanced Workflow Showcase */}
          <div className={`relative h-[400px] flex items-center justify-center transition-all duration-1000 ease-out delay-400 ${animationsLoaded ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'}`}>
            {/* Enhanced Background glow effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-primary/12 via-purple-500/10 via-blue-500/12 to-primary/12 rounded-3xl blur-3xl animate-breathe" />
            <div className="absolute inset-0 bg-gradient-to-br from-transparent via-primary/5 to-transparent rounded-3xl animate-gradient-shift" />
            
            {/* Single Active Workflow Card with enhanced styling */}
            <div className="relative w-full max-w-[350px] h-[300px] group">
              <Card className="h-full shadow-2xl shadow-primary/20 border-primary/30 bg-gradient-to-br from-background/95 to-background/85 backdrop-blur-md transition-all duration-700 hover:shadow-3xl hover:shadow-primary/30 hover:-translate-y-2 hover:scale-105 animate-card-hover">
                {/* Animated border gradient */}
                <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-primary/20 via-blue-500/20 via-purple-500/20 to-primary/20 p-[1px] animate-gradient-shift">
                  <div className="h-full w-full rounded-lg bg-gradient-to-br from-background/95 to-background/85 backdrop-blur-md" />
                </div>
                
                <CardHeader className="relative p-6 h-full flex flex-col justify-center z-10">
                  {/* Enhanced Icon with multiple animation layers */}
                  <div className="mb-6 text-center relative">
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-blue-500/20 rounded-2xl blur-lg animate-pulse" />
                    <div className={`${workflows[activeWorkflow].color} p-4 rounded-2xl bg-gradient-to-br from-white/90 to-white/70 dark:from-white/15 dark:to-white/8 inline-block shadow-xl animate-float relative z-10 transition-all duration-500 group-hover:scale-110 group-hover:rotate-6`}>
                      {workflows[activeWorkflow].icon}
                    </div>
                    {/* Floating particles around icon */}
                    <div className="absolute -top-2 -right-2 w-2 h-2 bg-yellow-400/60 rounded-full animate-sparkle" style={{ animationDelay: '0.5s' }} />
                    <div className="absolute -bottom-1 -left-1 w-1 h-1 bg-blue-400/60 rounded-full animate-sparkle" style={{ animationDelay: '1.5s' }} />
                  </div>
                  
                  {/* Enhanced Content */}
                  <CardTitle className="text-2xl font-bold mb-3 text-center bg-gradient-to-r from-foreground via-primary to-foreground bg-clip-text text-transparent transition-all duration-500 group-hover:scale-105">
                    {workflows[activeWorkflow].title}
                  </CardTitle>
                  <CardDescription className="text-muted-foreground leading-relaxed text-base text-center transition-all duration-500 group-hover:text-foreground/90">
                    {workflows[activeWorkflow].description}
                  </CardDescription>
                  
                  {/* Enhanced Progress Indicator */}
                  <div className="mt-6 flex justify-center gap-2">
                    {workflows.map((_, i) => (
                      <button 
                        key={i}
                        className={`h-2 rounded-full transition-all duration-700 hover:scale-125 ${
                          i === activeWorkflow 
                            ? 'w-8 bg-gradient-to-r from-primary via-blue-500 to-purple-500 animate-gradient-x shadow-lg' 
                            : 'w-2 bg-muted hover:bg-gradient-to-r hover:from-primary/50 hover:to-blue-500/50'
                        }`}
                        onClick={() => setActiveWorkflow(i)}
                      />
                    ))}
                  </div>
                </CardHeader>
              </Card>
            </div>
            
            {/* Enhanced Floating decorative elements */}
            <div className="absolute top-8 right-8 w-3 h-3 bg-gradient-to-r from-primary/60 to-blue-500/60 rounded-full animate-ping shadow-lg" />
            <div className="absolute bottom-8 left-8 w-2 h-2 bg-gradient-to-r from-purple-500/60 to-pink-500/60 rounded-full animate-ping shadow-lg" style={{ animationDelay: '1s' }} />
            <div className="absolute top-1/2 right-0 w-4 h-4 bg-gradient-to-r from-emerald-500/50 to-cyan-500/50 rounded-full animate-ping shadow-lg" style={{ animationDelay: '2s' }} />
            <div className="absolute top-1/4 left-4 w-1 h-1 bg-yellow-400/70 rounded-full animate-sparkle" style={{ animationDelay: '0.8s' }} />
            <div className="absolute bottom-1/4 right-12 w-1.5 h-1.5 bg-indigo-400/70 rounded-full animate-sparkle" style={{ animationDelay: '2.3s' }} />
          </div>
        </div>
      </section>

      {/* Enhanced Stats Section - Show different content based on invitation */}
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
              {hasInvitation ? "Platform Performance" : "Proven Results"}
            </div>
            <h2 className="text-3xl lg:text-4xl font-bold mb-4 bg-gradient-to-r from-primary via-blue-600 to-secondary bg-clip-text text-transparent">
              {hasInvitation ? "Real-Time Metrics" : "Enterprise-Grade Performance"}
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto text-lg leading-relaxed">
              {hasInvitation 
                ? "Live performance data showcasing the power and efficiency of automated workflows"
                : "Trusted by teams worldwide to automate critical business processes with reliability and scale"
              }
            </p>
          </div>
          
          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {metrics.map((metric, index) => (
              <Card 
                key={index} 
                className={`group relative overflow-hidden text-center transition-all duration-700 ease-out hover:shadow-2xl hover:shadow-primary/15 hover:-translate-y-4 hover:scale-105 bg-gradient-to-br from-background/95 to-background/85 backdrop-blur-sm border-2 hover:border-primary/40 animate-card-hover ${
                  animationsLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
                }`}
                style={{
                  transitionDelay: `${(index * 150) + 400}ms`
                }}
              >
                {/* Enhanced Card Background Gradient */}
                <div className={`absolute inset-0 bg-gradient-to-br ${metric.gradient} opacity-0 group-hover:opacity-15 transition-all duration-700`} />
                
                {/* Animated Border with improved gradient */}
                <div className="absolute inset-0 rounded-lg p-[1px] bg-gradient-to-r from-transparent via-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-700 animate-gradient-shift">
                  <div className="h-full w-full rounded-lg bg-gradient-to-br from-background/95 to-background/85" />
                </div>
                
                {/* Floating particles */}
                <div className="absolute inset-0 overflow-hidden">
                  <div className="absolute top-4 right-4 w-1 h-1 bg-primary/40 rounded-full animate-sparkle opacity-0 group-hover:opacity-100" style={{ animationDelay: '0.5s' }} />
                  <div className="absolute bottom-6 left-6 w-1.5 h-1.5 bg-blue-400/40 rounded-full animate-sparkle opacity-0 group-hover:opacity-100" style={{ animationDelay: '1.2s' }} />
                </div>
                
                <CardContent className="relative p-6 z-10">
                  {metric.isLoading ? (
                    <div className="space-y-4">
                      <Skeleton className="h-12 w-16 mx-auto rounded-lg animate-pulse" />
                      <Skeleton className="h-6 w-24 mx-auto rounded-md animate-pulse" />
                      <Skeleton className="h-4 w-16 mx-auto rounded-full animate-pulse" />
                    </div>
                  ) : (
                    <>
                      {/* Enhanced Icon with multiple animation layers */}
                      <div className="flex items-center justify-center mb-6 relative">
                        <div className={`absolute inset-0 bg-gradient-to-br ${metric.gradient} rounded-2xl blur-lg opacity-0 group-hover:opacity-30 transition-all duration-500 animate-breathe`} />
                        <div className={`p-3 rounded-2xl bg-gradient-to-br ${metric.gradient} text-white shadow-lg transition-all duration-500 group-hover:scale-125 group-hover:rotate-12 relative z-10 animate-float`} style={{
                          animationDelay: `${index * 0.5}s`
                        }}>
                          {metric.icon}
                        </div>
                      </div>
                      
                      {/* Enhanced Value with improved gradient and animation */}
                      <div className={`text-4xl lg:text-5xl font-bold mb-4 bg-gradient-to-br ${metric.gradient} bg-clip-text text-transparent transition-all duration-500 group-hover:scale-115 animate-bounce-in`} style={{
                        animationDelay: `${index * 0.2}s`
                      }}>
                        {metric.value}
                      </div>
                      
                      {/* Enhanced Label */}
                      <div className="text-muted-foreground text-sm font-semibold mb-4 tracking-wide uppercase transition-all duration-500 group-hover:text-foreground/90">
                        {metric.label}
                      </div>
                      
                      {/* Enhanced Trend Indicator with better animations */}
                      <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-full text-xs font-bold transition-all duration-500 group-hover:scale-110 group-hover:shadow-lg ${
                        metric.trend > 0 
                          ? 'bg-green-100 text-green-700 border border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800/50 hover:bg-green-200 dark:hover:bg-green-900/50' 
                          : 'bg-red-100 text-red-700 border border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800/50 hover:bg-red-200 dark:hover:bg-red-900/50'
                      }`}>
                        <TrendingUp className={`h-3 w-3 transition-all duration-500 group-hover:scale-125 ${
                          metric.trend > 0 ? 'rotate-0 text-green-600' : 'rotate-180 text-red-600'
                        }`} />
                        <span className="font-bold">{metric.trend > 0 ? '+' : ''}{metric.trend}%</span>
                      </div>
                    </>
                  )}
                </CardContent>
                
                {/* Enhanced Shimmer Effect with improved timing */}
                <div className="absolute inset-0 rounded-lg overflow-hidden">
                  <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1200 ease-out bg-gradient-to-r from-transparent via-white/25 to-transparent" />
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

      {/* Conditional Section - Invitation or Contact */}
      {hasInvitation ? (
        <section ref={invitationSectionRef} id="invitation-section" className="relative py-20 bg-gradient-to-br from-primary/5 via-card/30 to-secondary/5 border-y border-border/30">
          {/* Background decoration */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-10 left-10 w-32 h-32 bg-primary/5 rounded-full blur-3xl animate-pulse" />
            <div className="absolute bottom-10 right-10 w-24 h-24 bg-secondary/5 rounded-full blur-2xl animate-pulse" style={{ animationDelay: '2s' }} />
          </div>
          
          <div className="container mx-auto px-4 relative z-10">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 border border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800/50 rounded-full text-sm font-medium mb-8">
                <Mail className="h-4 w-4" />
                You've Been Invited!
              </div>
              
              <h2 className="text-3xl lg:text-4xl font-bold mb-6 bg-gradient-to-r from-primary via-blue-600 to-secondary bg-clip-text text-transparent">
                Welcome to FlowMastery
              </h2>
              
              <p className="text-xl text-muted-foreground mb-8 leading-relaxed max-w-2xl mx-auto">
                You've been invited to join our powerful workflow automation platform. 
                Experience seamless n8n integration, real-time metrics, and enterprise-grade automation tools.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button 
                  size="lg" 
                  className="bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-600/90 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
                  onClick={() => navigate(`/accept-invitation?token=${invitationToken}`)}
                >
                  <Rocket className="h-4 w-4 mr-2" />
                  Complete Setup & Get Started
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
                
                <Button 
                  size="lg" 
                  variant="outline"
                  className="border-2 border-primary/20 hover:border-primary/40 hover:bg-primary/5 transition-all duration-300 hover:-translate-y-1"
                  onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                >
                  Learn More About Platform
                </Button>
              </div>
            </div>
          </div>
        </section>
      ) : (
        <section className="relative py-20 bg-gradient-to-br from-primary/5 via-card/30 to-secondary/5 border-y border-border/30">
          {/* Background decoration */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-10 left-10 w-32 h-32 bg-primary/5 rounded-full blur-3xl animate-pulse" />
            <div className="absolute bottom-10 right-10 w-24 h-24 bg-secondary/5 rounded-full blur-2xl animate-pulse" style={{ animationDelay: '2s' }} />
          </div>
          
          <div className="container mx-auto px-4 relative z-10">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium mb-8">
                <Users className="h-4 w-4" />
                Enterprise Solution
              </div>
              
              <h2 className="text-3xl lg:text-4xl font-bold mb-6 bg-gradient-to-r from-primary via-blue-600 to-secondary bg-clip-text text-transparent">
                Ready to Transform Your Workflows?
              </h2>
              
              <p className="text-xl text-muted-foreground mb-12 leading-relaxed max-w-2xl mx-auto">
                Join hundreds of teams already automating their processes with FlowMastery. 
                Get invited by your team administrator to start your automation journey.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
                <Card className="p-8 text-left border-2 hover:border-primary/30 transition-all duration-300 hover:shadow-lg">
                  <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-blue-500/20 rounded-lg flex items-center justify-center mb-6">
                    <Mail className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-4">Team Invitation Required</h3>
                  <p className="text-muted-foreground mb-4">
                    FlowMastery is an enterprise platform. Your team administrator will send you an invitation to join your organization's workspace.
                  </p>
                  <ul className="text-sm text-muted-foreground space-y-2">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Secure team-based access
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Role-based permissions
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Centralized workflow management
                    </li>
                  </ul>
                </Card>
                
                <Card className="p-8 text-left border-2 hover:border-primary/30 transition-all duration-300 hover:shadow-lg">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-lg flex items-center justify-center mb-6">
                    <Rocket className="h-6 w-6 text-green-600" />
                  </div>
                  <h3 className="text-xl font-semibold mb-4">Already Have Access?</h3>
                  <p className="text-muted-foreground mb-6">
                    If you're already part of a FlowMastery team, sign in to access your workflows and automation tools.
                  </p>
                  <Button 
                    className="w-full bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-600/90 text-white"
                    onClick={() => navigate('/login')}
                  >
                    <Users className="h-4 w-4 mr-2" />
                    Sign In to Your Team
                  </Button>
                </Card>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

export default HomePage
