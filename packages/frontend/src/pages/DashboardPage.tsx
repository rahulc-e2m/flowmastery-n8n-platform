import React from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { MetricsApi } from '@/services/metricsApi'
import { ClientApi } from '@/services/clientApi'
import { motion } from 'framer-motion'
import { 
  BarChart3, 
  Building2, 
  Users, 
  Activity,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Zap,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { AnimatedCard } from '@/components/ui/animated-card'
import { DataSourceIndicator } from '@/components/ui/data-source-indicator'
import { ClientMetricsCard } from '@/components/dashboard/ClientMetricsCard'
import { formatDistanceToNow } from 'date-fns'
import { 
  fadeInUp, 
  staggerContainer, 
  staggerItem, 
  pageTransition 
} from '@/lib/animations'

export function DashboardPage() {
  const { user, isAdmin, isClient } = useAuth()
  const navigate = useNavigate()

  // Admin dashboard data
  const { data: adminMetrics, isLoading: adminLoading } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: MetricsApi.getAllClientsMetrics,
    enabled: isAdmin,
    refetchInterval: 30000,
  })

  const { data: clients, isLoading: clientsLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: ClientApi.getClients,
    enabled: isAdmin,
  })

  // Client dashboard data
  const { data: clientMetrics, isLoading: clientMetricsLoading } = useQuery({
    queryKey: ['my-metrics'],
    queryFn: MetricsApi.getMyMetrics,
    enabled: isClient,
    refetchInterval: 30000,
  })

  const { data: clientWorkflows, isLoading: clientWorkflowsLoading } = useQuery({
    queryKey: ['my-workflows'],
    queryFn: MetricsApi.getMyWorkflowMetrics,
    enabled: isClient,
    refetchInterval: 30000,
  })

  if (isAdmin) {
    return <AdminDashboard 
      metrics={adminMetrics} 
      clients={clients}
      isLoading={adminLoading || clientsLoading} 
    />
  }

  if (isClient) {
    return <ClientDashboard 
      metrics={clientMetrics}
      workflows={clientWorkflows}
      isLoading={clientMetricsLoading || clientWorkflowsLoading}
    />
  }

  return null
}

function AdminDashboard({ metrics, clients, isLoading }: any) {
  const navigate = useNavigate()

  if (isLoading) {
    return <DashboardSkeleton />
  }

  const stats = [
    {
      title: 'Total Clients',
      value: metrics?.total_clients || 0,
      icon: Building2,
      color: 'blue',
      trend: { value: 12, isPositive: true },
      description: 'Active organizations'
    },
    {
      title: 'Total Workflows',
      value: metrics?.total_workflows || 0,
      icon: Activity,
      color: 'green',
      trend: { value: 8, isPositive: true },
      description: 'Automated processes'
    },
    {
      title: 'Total Executions',
      value: (metrics?.total_executions || 0).toLocaleString(),
      icon: Zap,
      color: 'purple',
      trend: { value: 24, isPositive: true },
      description: 'Last 30 days'
    },
    {
      title: 'Success Rate',
      value: `${metrics?.overall_success_rate || 0}%`,
      icon: TrendingUp,
      color: 'green',
      trend: { value: 2, isPositive: true },
      description: 'System performance'
    },
  ]

  return (
    <motion.div 
      className="p-6 space-y-8"
      variants={pageTransition}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {/* Header */}
      <motion.div 
        variants={fadeInUp}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold text-gradient mb-2">Admin Dashboard</h1>
          <p className="text-muted-foreground text-lg">Complete overview of all clients and workflows</p>
        </div>
        <DataSourceIndicator 
          lastUpdated={metrics?.last_updated} 
          variant="full"
          debug={true}
        />
      </motion.div>

      {/* Stats Grid */}
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        {stats.map((stat, index) => (
          <motion.div key={stat.title} variants={staggerItem}>
            <MetricCard {...stat} />
          </motion.div>
        ))}
      </motion.div>

      {/* Clients Grid */}
      <motion.div variants={fadeInUp}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-2xl font-semibold text-foreground mb-1">Client Performance</h3>
            <p className="text-muted-foreground">Click on any client to view detailed analytics</p>
          </div>
          <Badge variant="outline" className="px-3 py-1">
            {metrics?.clients?.length || 0} Active
          </Badge>
        </div>
        
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          {metrics?.clients?.map((client: any, index: number) => (
            <motion.div key={client.client_id} variants={staggerItem}>
              <ClientMetricsCard
                client={client}
                index={index}
                onClick={() => navigate(`/client/${client.client_id}`)}
              />
            </motion.div>
          ))}
        </motion.div>
      </motion.div>
    </motion.div>
  )
}

// Metric Card Component
function MetricCard({ title, value, icon: Icon, color, trend, description }: any) {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-950/50',
    green: 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-950/50',
    purple: 'text-purple-600 bg-purple-100 dark:text-purple-400 dark:bg-purple-950/50',
    orange: 'text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-950/50'
  }

  return (
    <AnimatedCard className="p-6 relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <motion.p 
            className="text-sm font-medium text-muted-foreground mb-2"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            {title}
          </motion.p>
          <motion.p 
            className="text-3xl font-bold text-foreground mb-1"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          >
            {value}
          </motion.p>
          {description && (
            <motion.p 
              className="text-xs text-muted-foreground"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              {description}
            </motion.p>
          )}
          {trend && (
            <motion.div 
              className={`flex items-center mt-2 text-xs font-medium ${
                trend.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              }`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              {trend.isPositive ? (
                <ArrowUpRight className="w-3 h-3 mr-1" />
              ) : (
                <ArrowDownRight className="w-3 h-3 mr-1" />
              )}
              {Math.abs(trend.value)}%
            </motion.div>
          )}
        </div>
        <motion.div 
          className={`p-3 rounded-xl shadow-sm ${colorClasses[color] || colorClasses.blue}`}
          initial={{ opacity: 0, scale: 0, rotate: -45 }}
          animate={{ opacity: 1, scale: 1, rotate: 0 }}
          transition={{ delay: 0.15, type: 'spring', stiffness: 200 }}
          whileHover={{ scale: 1.1, rotate: 5 }}
        >
          <Icon className="w-6 h-6" />
        </motion.div>
      </div>
    </AnimatedCard>
  )
}

function ClientDashboard({ metrics, workflows, isLoading }: any) {
  if (isLoading) {
    return <DashboardSkeleton />
  }

  const stats = [
    {
      title: 'Total Workflows',
      value: metrics?.total_workflows || 0,
      icon: Activity,
      color: 'blue',
      trend: { value: 5, isPositive: true },
      description: 'Automated processes'
    },
    {
      title: 'Active Workflows',
      value: metrics?.active_workflows || 0,
      icon: CheckCircle,
      color: 'green',
      trend: { value: 2, isPositive: true },
      description: 'Currently running'
    },
    {
      title: 'Total Executions',
      value: (metrics?.total_executions || 0).toLocaleString(),
      icon: Zap,
      color: 'purple',
      trend: { value: 15, isPositive: true },
      description: 'Last 30 days'
    },
    {
      title: 'Success Rate',
      value: `${metrics?.success_rate || 0}%`,
      icon: TrendingUp,
      color: 'green',
      trend: { value: 3, isPositive: true },
      description: 'Performance metric'
    },
  ]

  return (
    <motion.div 
      className="p-6 space-y-8"
      variants={pageTransition}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {/* Header */}
      <motion.div variants={fadeInUp}>
        <h1 className="text-4xl font-bold text-gradient mb-2">Your Dashboard</h1>
        <p className="text-muted-foreground text-lg">Monitor your workflow performance and analytics</p>
      </motion.div>

      {/* Stats Grid */}
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        {stats.map((stat, index) => (
          <motion.div key={stat.title} variants={staggerItem}>
            <MetricCard {...stat} />
          </motion.div>
        ))}
      </motion.div>

      {/* Recent Workflows */}
      <motion.div variants={fadeInUp}>
        <AnimatedCard className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-semibold text-foreground mb-1">Recent Workflows</h3>
              <p className="text-muted-foreground">Latest execution status and performance</p>
            </div>
            <Badge variant="outline" className="px-3 py-1">
              {workflows?.length || 0} Total
            </Badge>
          </div>
          
          <div className="space-y-4">
            {workflows?.slice(0, 5).map((workflow: any, index: number) => (
              <motion.div 
                key={workflow.workflow_id}
                className="group flex items-center justify-between p-4 rounded-xl border border-border/50 hover:border-border transition-all duration-200 hover:bg-accent/30"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.01, x: 4 }}
              >
                <div className="flex items-center space-x-4">
                  <motion.div 
                    className="w-10 h-10 bg-gradient-to-br from-primary/20 to-accent/20 rounded-lg flex items-center justify-center"
                    whileHover={{ rotate: 5, scale: 1.1 }}
                  >
                    <Activity className="w-5 h-5 text-primary" />
                  </motion.div>
                  <div>
                    <h4 className="font-medium text-foreground group-hover:text-primary transition-colors">
                      {workflow.workflow_name}
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {workflow.total_executions} executions
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <Badge 
                    variant={workflow.success_rate >= 90 ? 'default' : workflow.success_rate >= 70 ? 'secondary' : 'destructive'}
                  >
                    {workflow.success_rate}%
                  </Badge>
                  <div className="text-right">
                    <p className="text-sm font-medium text-foreground">
                      {workflow.last_execution_status === 'success' ? (
                        <span className="flex items-center text-green-600">
                          <CheckCircle className="w-4 h-4 mr-1" />
                          Success
                        </span>
                      ) : (
                        <span className="flex items-center text-red-600">
                          <XCircle className="w-4 h-4 mr-1" />
                          Failed
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {workflow.last_execution_time ? 
                        formatDistanceToNow(new Date(workflow.last_execution_time), { addSuffix: true }) : 
                        'No recent runs'
                      }
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </AnimatedCard>
      </motion.div>
    </motion.div>
  )
}


function DashboardSkeleton() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96 mt-2" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-8 w-16" />
                </div>
                <Skeleton className="w-12 h-12 rounded-full" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-48" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <Skeleton className="w-10 h-10 rounded-lg" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-48" />
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <Skeleton className="h-6 w-16 rounded-full" />
                  <div className="space-y-1">
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}