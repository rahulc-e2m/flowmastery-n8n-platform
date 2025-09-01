import React from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { MetricsApi } from '@/services/metricsApi'
import { ClientApi } from '@/services/clientApi'
import { motion } from 'framer-motion'
import { 
  Building2, 
  Activity,
  TrendingUp,
  Clock,
  CheckCircle,
  Zap,
  RefreshCw
} from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { AnimatedCard } from '@/components/ui/animated-card'
import { DataSourceIndicator } from '@/components/ui/data-source-indicator'
import { TrendIndicator } from '@/components/ui/trend-indicator'
import { ClientMetricsCard } from '@/components/dashboard/ClientMetricsCard'
import { formatDistanceToNow } from 'date-fns'
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'
import { 
  fadeInUp, 
  staggerContainer, 
  staggerItem, 
  pageTransition 
} from '@/lib/animations'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']

export function DashboardPage() {
  const { isAdmin, isClient } = useAuth()

  // Admin dashboard data
  const { data: adminMetrics, isLoading: adminLoading } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: MetricsApi.getAllClientsMetrics,
    enabled: isAdmin,
    refetchInterval: 30000, // 30 seconds
    staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
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
    refetchInterval: 30000, // 30 seconds
    staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
  })

  const { data: clientWorkflows, isLoading: clientWorkflowsLoading } = useQuery({
    queryKey: ['my-workflows'],
    queryFn: MetricsApi.getMyWorkflowMetrics,
    enabled: isClient,
    refetchInterval: 30000,
    staleTime: 5 * 60 * 1000,
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

function AdminDashboard({ metrics, isLoading }: any) {
  const navigate = useNavigate()
  const [isRefreshing, setIsRefreshing] = React.useState(false)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await MetricsApi.refreshCache()
      toast.success('Dashboard data refreshed successfully')
      // Trigger a refetch of the data
      window.location.reload()
    } catch (error) {
      toast.error('Failed to refresh dashboard data')
      console.error('Refresh error:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  if (isLoading) {
    return <DashboardSkeleton />
  }

  const stats = [
    {
      title: 'Total Clients',
      value: metrics?.total_clients || 0,
      icon: Building2,
      color: 'blue',
      trend: { value: Math.abs(metrics?.trends?.execution_trend || 0), isPositive: (metrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Active organizations'
    },
    {
      title: 'Total Workflows',
      value: metrics?.total_workflows || 0,
      icon: Activity,
      color: 'green',
      trend: { value: Math.abs(metrics?.trends?.execution_trend || 0), isPositive: (metrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Automated processes'
    },
    {
      title: 'Total Executions',
      value: (metrics?.total_executions || 0).toLocaleString(),
      icon: Zap,
      color: 'purple',
      trend: { value: Math.abs(metrics?.trends?.execution_trend || 0), isPositive: (metrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Last 30 days'
    },
    {
      title: 'Avg Hours Saved',
      value: metrics?.total_time_saved_hours ? `${metrics.total_time_saved_hours}h` : '0h',
      icon: Clock,
      color: 'orange',
      trend: { value: Math.abs(metrics?.trends?.execution_trend || 0), isPositive: (metrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Average time saved per client'
    },
    {
      title: 'Success Rate',
      value: `${metrics?.overall_success_rate?.toFixed(1) || '0.0'}%`,
      icon: TrendingUp,
      color: 'green',
      trend: { value: Math.abs(metrics?.trends?.success_rate_trend || 0), isPositive: (metrics?.trends?.success_rate_trend || 0) >= 0 },
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
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
          </Button>
          <DataSourceIndicator 
            lastUpdated={metrics?.last_updated} 
            variant="full"
            debug={true}
          />
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6"
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        {stats.map((stat) => (
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
            <TrendIndicator value={trend.value} isPositive={trend.isPositive} />
          )}
        </div>
        <motion.div 
          className={`p-3 rounded-xl shadow-sm ${colorClasses[color as keyof typeof colorClasses] || colorClasses.blue}`}
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
  const [isRefreshing, setIsRefreshing] = React.useState(false)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      // For client users, we can't refresh cache directly, so just reload
      window.location.reload()
      toast.success('Dashboard refreshed')
    } catch (error) {
      toast.error('Failed to refresh dashboard')
    } finally {
      setIsRefreshing(false)
    }
  }

  if (isLoading) {
    return <DashboardSkeleton />
  }

  const stats = [
    {
      title: 'Total Workflows',
      value: metrics?.total_workflows || 0,
      icon: Activity,
      color: 'blue',
      trend: { value: Math.abs(metrics?.trends?.execution_trend || 0), isPositive: (metrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Automated processes'
    },
    {
      title: 'Active Workflows',
      value: metrics?.active_workflows || 0,
      icon: CheckCircle,
      color: 'green',
      trend: { value: Math.abs(metrics?.trends?.execution_trend || 0), isPositive: (metrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Currently running'
    },
    {
      title: 'Total Executions',
      value: (metrics?.total_executions || 0).toLocaleString(),
      icon: Zap,
      color: 'purple',
      trend: { value: Math.abs(metrics?.trends?.execution_trend || 0), isPositive: (metrics?.trends?.execution_trend || 0) >= 0 },
      description: 'All time'
    },
    {
      title: 'Hours Saved',
      value: metrics?.time_saved_hours ? `${metrics.time_saved_hours}h` : '0h',
      icon: Clock,
      color: 'orange',
      trend: { value: Math.abs(metrics?.trends?.execution_trend || 0), isPositive: (metrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Time saved by automation'
    },
    {
      title: 'Success Rate',
      value: `${metrics?.success_rate?.toFixed(1) || '0.0'}%`,
      icon: TrendingUp,
      color: 'green',
      trend: { value: Math.abs(metrics?.trends?.success_rate_trend || 0), isPositive: (metrics?.trends?.success_rate_trend || 0) >= 0 },
      description: 'Performance metric'
    },
  ]

  // Sort workflows by most recent activity first, then by total executions
  const sortedWorkflows = workflows?.workflows?.sort((a: any, b: any) => {
    // First sort by last execution time (most recent first)
    const aTime = a.last_execution ? new Date(a.last_execution).getTime() : 0
    const bTime = b.last_execution ? new Date(b.last_execution).getTime() : 0
    if (aTime !== bTime) return bTime - aTime
    
    // Then by total executions (highest first)
    return b.total_executions - a.total_executions
  }) || []

  // Prepare chart data from sorted workflows
  const chartData = sortedWorkflows.slice(0, 8).map((workflow: any) => ({
    name: workflow.workflow_name.length > 15 ? 
      workflow.workflow_name.substring(0, 15) + '...' : 
      workflow.workflow_name,
    executions: workflow.total_executions,
    success_rate: workflow.success_rate,
    successful: workflow.successful_executions,
    failed: workflow.failed_executions,
    last_execution: workflow.last_execution
  })) || []

  const pieData = sortedWorkflows.slice(0, 6).map((workflow: any, index: number) => ({
    name: workflow.workflow_name.length > 20 ? 
      workflow.workflow_name.substring(0, 20) + '...' : 
      workflow.workflow_name,
    value: workflow.total_executions,
    color: COLORS[index % COLORS.length],
  })) || []

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
          <h1 className="text-4xl font-bold text-gradient mb-2">Your Dashboard</h1>
          <p className="text-muted-foreground text-lg">Monitor your workflow performance and analytics</p>
        </div>
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
          </Button>
          <DataSourceIndicator 
            lastUpdated={metrics?.last_updated || workflows?.last_updated} 
            variant="compact"
          />
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6"
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        {stats.map((stat) => (
          <motion.div key={stat.title} variants={staggerItem}>
            <MetricCard {...stat} />
          </motion.div>
        ))}
      </motion.div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={fadeInUp}>
          <AnimatedCard className="p-6">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-foreground mb-1">Workflow Executions</h3>
              <p className="text-sm text-muted-foreground">Total executions by workflow</p>
            </div>
            <div className="h-80 chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="name" 
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Bar dataKey="executions" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </AnimatedCard>
        </motion.div>

        <motion.div variants={fadeInUp}>
          <AnimatedCard className="p-6">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-foreground mb-1">Execution Distribution</h3>
              <p className="text-sm text-muted-foreground">Workflow execution breakdown</p>
            </div>
            <div className="h-80 chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={120}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </AnimatedCard>
        </motion.div>
      </div>

      {/* Recent Workflows */}
      <motion.div variants={fadeInUp}>
        <AnimatedCard className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-semibold text-foreground mb-1">Recent Workflows</h3>
              <p className="text-muted-foreground">Latest execution status and performance</p>
            </div>
            <Badge variant="outline" className="px-3 py-1">
              {workflows?.workflows?.length || 0} Total
            </Badge>
          </div>
          
          <div className="space-y-4">
            {sortedWorkflows.slice(0, 5).map((workflow: any, index: number) => {
              const isRecentlyActive = workflow.last_execution && 
                new Date(workflow.last_execution).getTime() > Date.now() - (24 * 60 * 60 * 1000) // Last 24 hours
              
              return (
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
                      className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        isRecentlyActive 
                          ? 'bg-gradient-to-br from-green-500/20 to-emerald-500/20' 
                          : 'bg-gradient-to-br from-primary/20 to-accent/20'
                      }`}
                      whileHover={{ rotate: 5, scale: 1.1 }}
                    >
                      <Activity className={`w-5 h-5 ${isRecentlyActive ? 'text-green-600' : 'text-primary'}`} />
                    </motion.div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-foreground group-hover:text-primary transition-colors">
                          {workflow.workflow_name}
                        </h4>
                        {isRecentlyActive && (
                          <Badge variant="outline" className="text-xs px-2 py-0 text-green-600 border-green-200">
                            Active
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {workflow.total_executions} executions • {workflow.success_rate?.toFixed(1) || '0.0'}% success • {workflow.time_saved_hours ? `${workflow.time_saved_hours}h saved` : '0h saved'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm font-medium text-foreground">
                        {workflow.last_execution ? (
                          <span className="flex items-center text-green-600">
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Last run
                          </span>
                        ) : (
                          <span className="flex items-center text-muted-foreground">
                            <Clock className="w-4 h-4 mr-1" />
                            No runs
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {workflow.last_execution ? 
                          formatDistanceToNow(new Date(workflow.last_execution), { addSuffix: true }) : 
                          'Never executed'
                        }
                      </p>
                    </div>
                  </div>
                </motion.div>
              )
            })}
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {Array.from({ length: 5 }).map((_, i) => (
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