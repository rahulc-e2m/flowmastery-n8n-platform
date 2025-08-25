import React, { useState, useEffect } from 'react'
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
  Activity
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
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
}

const HomePage: React.FC = () => {
  const [activeWorkflow, setActiveWorkflow] = useState(0)
  const [isVisible, setIsVisible] = useState(false)
  const navigate = useNavigate()
  
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

  const metrics: MetricCard[] = metricsData ? [
    {
      label: "Active Workflows",
      value: metricsData.workflows.active_workflows.toString(),
      trend: Math.round((metricsData.workflows.active_workflows / Math.max(1, metricsData.workflows.total_workflows)) * 100),
      icon: <Play className="h-4 w-4" />,
      isLoading: metricsLoading
    },
    {
      label: "Total Executions",
      value: formatNumber(metricsData.executions.total_executions),
      trend: 23,
      icon: <Activity className="h-4 w-4" />,
      isLoading: metricsLoading
    },
    {
      label: "Time Saved",
      value: `${metricsData.derived_metrics.time_saved_hours}h`,
      trend: 8,
      icon: <Clock className="h-4 w-4" />,
      isLoading: metricsLoading
    },
    {
      label: "Success Rate",
      value: `${metricsData.executions.success_rate}%`,
      trend: metricsData.executions.success_rate > 90 ? 5 : -2,
      icon: <CheckCircle className="h-4 w-4" />,
      isLoading: metricsLoading
    }
  ] : [
    {
      label: "Active Workflows",
      value: "--",
      trend: 0,
      icon: <Play className="h-4 w-4" />,
      isLoading: metricsLoading
    },
    {
      label: "Total Executions", 
      value: "--",
      trend: 0,
      icon: <Activity className="h-4 w-4" />,
      isLoading: metricsLoading
    },
    {
      label: "Time Saved",
      value: "--",
      trend: 0,
      icon: <Clock className="h-4 w-4" />,
      isLoading: metricsLoading
    },
    {
      label: "Success Rate",
      value: "--",
      trend: 0,
      icon: <CheckCircle className="h-4 w-4" />,
      isLoading: metricsLoading
    }
  ]

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
    setIsVisible(true)

    // Workflow carousel
    const interval = setInterval(() => {
      setActiveWorkflow((prev) => (prev + 1) % workflows.length)
    }, 3000)

    return () => {
      clearInterval(interval)
    }
  }, [])

  return (
    <div className={`transition-opacity duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Hero Content */}
          <div className="space-y-8 animate-fade-in-left">
            <div className="space-y-4">
              <h1 className="text-4xl lg:text-6xl font-bold leading-tight">
                <span className="bg-gradient-primary bg-clip-text text-transparent">
                  Centralize
                </span>{" "}
                Your n8n Workflows
              </h1>
              <p className="text-xl text-muted-foreground leading-relaxed">
                One powerful platform to manage, execute, and monitor all your automation workflows. 
                From chatbots to SEO tools, everything in one place.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button 
                size="lg" 
                variant="gradient"
                onClick={() => navigate('/metrics')}
                className="flex items-center gap-2"
              >
                <Eye className="h-4 w-4" />
                View n8n Metrics
              </Button>
              <Button 
                size="lg" 
                variant="outline"
                onClick={() => navigate('/chatbots')}
                className="flex items-center gap-2"
              >
                View Workflows
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>

            {/* Status Badge */}
            <div className="animate-fade-in-left" style={{ animationDelay: '0.5s' }}>
              {metricsLoading ? (
                <Badge variant="warning" className="flex items-center gap-2 w-fit">
                  <Clock className="h-3 w-3" />
                  Checking n8n connection...
                </Badge>
              ) : configStatus?.configured && metricsData ? (
                <Badge variant="success" className="flex items-center gap-2 w-fit">
                  <Play className="h-3 w-3" />
                  n8n Connected • Live Data
                </Badge>
              ) : (
                <Badge variant="secondary" className="flex items-center gap-2 w-fit">
                  <Settings className="h-3 w-3" />
                  Configure n8n for Live Metrics
                </Badge>
              )}
            </div>
          </div>

          {/* Hero Visual - Workflow Showcase */}
          <div className="relative h-[400px] flex items-center justify-center animate-fade-in-right">
            {workflows.map((workflow, index) => (
              <Card
                key={index}
                className={`absolute w-[320px] transition-all duration-500 ${
                  activeWorkflow === index
                    ? 'opacity-100 scale-100 translate-y-0 shadow-glow'
                    : 'opacity-0 scale-90 translate-y-5'
                }`}
              >
                <CardHeader>
                  <div className={`${workflow.color} mb-4`}>
                    {workflow.icon}
                  </div>
                  <CardTitle className="text-xl">{workflow.title}</CardTitle>
                  <CardDescription>{workflow.description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="border-y border-border/40 bg-card/20 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-12">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {metrics.map((metric, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <CardContent className="p-6">
                  {metric.isLoading ? (
                    <div className="space-y-3">
                      <Skeleton className="h-8 w-16 mx-auto" />
                      <Skeleton className="h-4 w-24 mx-auto" />
                      <Skeleton className="h-3 w-12 mx-auto" />
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <div className="text-primary">{metric.icon}</div>
                        <div className="text-3xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                          {metric.value}
                        </div>
                      </div>
                      <div className="text-muted-foreground text-sm mb-2">
                        {metric.label}
                      </div>
                      <div className={`text-xs font-semibold flex items-center justify-center gap-1 ${
                        metric.trend > 0 ? 'text-success-500' : 'text-error-500'
                      }`}>
                        <TrendingUp className="h-3 w-3" />
                        {metric.trend > 0 ? '+' : ''}{metric.trend}%
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16 lg:py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl lg:text-5xl font-bold mb-4">
            Everything You Need
          </h2>
          <p className="text-xl text-muted-foreground">
            Powerful features to streamline your workflow automation
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-2 relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-primary scale-x-0 group-hover:scale-x-100 transition-transform duration-300" />
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center text-primary mb-4">
                  {feature.icon}
                </div>
                <CardTitle className="text-xl mb-3">{feature.title}</CardTitle>
                <CardDescription className="leading-relaxed">
                  {feature.description}
                </CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16">
        <Card className="bg-gradient-primary/10 border-primary/20 text-center">
          <CardContent className="p-12">
            <div className="max-w-2xl mx-auto space-y-6">
              <h3 className="text-3xl font-bold">
                Ready to Supercharge Your Workflows?
              </h3>
              <p className="text-lg text-muted-foreground">
                Join thousands of teams already using WorkflowHub to automate their processes
                and save countless hours every week.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" variant="gradient">
                  Get Started Free
                </Button>
                <Button size="lg" variant="outline">
                  View Documentation
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

export default HomePage