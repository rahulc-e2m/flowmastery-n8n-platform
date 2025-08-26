import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { MetricsApi } from '@/services/metricsApi'
import { ClientApi } from '@/services/clientApi'
import { useAuth } from '@/contexts/AuthContext'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  Timer,
  Calendar,
  RefreshCw,
  Building2,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { WorkflowMetricsTable } from '@/components/dashboard/WorkflowMetricsTable'
import { ExecutionsList } from '@/components/dashboard/ExecutionsList'
import { AnimatedCard } from '@/components/ui/animated-card'
import { DataSourceIndicator } from '@/components/ui/data-source-indicator'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { formatDistanceToNow } from 'date-fns'
import { 
  fadeInUp, 
  staggerContainer, 
  staggerItem, 
  pageTransition 
} from '@/lib/animations'

export function ClientDashboardPage() {
  const { clientId } = useParams<{ clientId: string }>()
  const navigate = useNavigate()
  const { isAdmin } = useAuth()
  const [refreshKey, setRefreshKey] = useState(0)
  const [selectedWorkflows, setSelectedWorkflows] = useState<string[]>([])
  const [selectedExecutions, setSelectedExecutions] = useState<string[]>([])
  const [activeTab, setActiveTab] = useState('workflows')

  const clientIdNum = clientId ? parseInt(clientId) : 0

  // Client basic info
  const { data: client } = useQuery({
    queryKey: ['client', clientIdNum],
    queryFn: () => ClientApi.getClient(clientIdNum),
    enabled: !!clientIdNum && isAdmin,
  })

  // Client metrics
  const { data: clientMetrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['client-metrics', clientIdNum, refreshKey],
    queryFn: () => MetricsApi.getClientMetrics(clientIdNum),
    enabled: !!clientIdNum,
    refetchInterval: 30000,
  })

  // Workflow stats
  const { data: workflowStats, isLoading: workflowStatsLoading, refetch: refetchWorkflowStats } = useQuery({
    queryKey: ['client-execution-stats', clientIdNum, refreshKey],
    queryFn: () => MetricsApi.getClientExecutionStats(clientIdNum),
    enabled: !!clientIdNum,
    refetchInterval: 30000,
  })

  // Recent executions
  const { data: recentExecutions, isLoading: executionsLoading, refetch: refetchExecutions } = useQuery({
    queryKey: ['client-executions', clientIdNum, refreshKey],
    queryFn: () => MetricsApi.getClientExecutions(clientIdNum, 20),
    enabled: !!clientIdNum,
    refetchInterval: 30000,
  })

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
    refetchMetrics()
    refetchWorkflowStats()
    refetchExecutions()
  }

  const handleWorkflowSelection = (selectedIds: string[]) => {
    setSelectedWorkflows(selectedIds)
  }

  const handleExecutionSelection = (selectedIds: string[]) => {
    setSelectedExecutions(selectedIds)
  }

  const clearSelections = () => {
    setSelectedWorkflows([])
    setSelectedExecutions([])
  }

  if (!clientIdNum) {
    return (
      <div className="p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">Invalid Client ID</h1>
          <Button onClick={() => navigate('/dashboard')} className="mt-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    )
  }

  const isLoading = metricsLoading || workflowStatsLoading || executionsLoading

  if (isLoading) {
    return <ClientDashboardSkeleton />
  }

  const stats = [
    {
      title: 'Total Workflows',
      value: clientMetrics?.total_workflows || 0,
      icon: Activity,
      color: 'blue',
      trend: { value: 5, isPositive: true },
      description: 'Automated processes'
    },
    {
      title: 'Active Workflows',
      value: clientMetrics?.active_workflows || 0,
      icon: CheckCircle,
      color: 'green',
      trend: { value: 2, isPositive: true },
      description: 'Currently running'
    },
    {
      title: 'Total Executions',
      value: (clientMetrics?.total_executions || 0).toLocaleString(),
      icon: Zap,
      color: 'purple',
      trend: { value: 15, isPositive: true },
      description: 'All time'
    },
    {
      title: 'Hours Saved',
      value: clientMetrics?.time_saved_hours ? `${clientMetrics.time_saved_hours}h` : '0h',
      icon: Timer,
      color: 'orange',
      trend: { value: 18, isPositive: true },
      description: 'Time saved by automation'
    },
    {
      title: 'Success Rate',
      value: `${clientMetrics?.success_rate || 0}%`,
      icon: TrendingUp,
      color: 'green',
      trend: { value: 3, isPositive: true },
      description: 'Performance metric'
    },
  ]

  // Prepare chart data
  const chartData = workflowStats?.workflow_stats?.slice(0, 10).map((workflow: any) => ({
    name: workflow.workflow_name.length > 20 ? 
      workflow.workflow_name.substring(0, 20) + '...' : 
      workflow.workflow_name,
    executions: workflow.total_executions,
    success_rate: workflow.success_rate,
    avg_time: workflow.avg_execution_time_seconds
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
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => navigate('/dashboard')}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Dashboard</span>
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => navigate('/metrics')}
              className="flex items-center space-x-2"
            >
              <BarChart3 className="w-4 h-4" />
              <span>Metrics</span>
            </Button>
          </div>
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <Building2 className="w-8 h-8 text-primary" />
              <h1 className="text-4xl font-bold text-gradient">
                {client?.name || `Client ${clientId}`}
              </h1>
            </div>
            <p className="text-muted-foreground text-lg">
              Comprehensive workflow analytics and performance metrics
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {(selectedWorkflows.length > 0 || selectedExecutions.length > 0) && (
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="px-3 py-1">
                {selectedWorkflows.length + selectedExecutions.length} Selected
              </Badge>
              <Button onClick={clearSelections} variant="outline" size="sm">
                Clear Selection
              </Button>
            </div>
          )}
          <DataSourceIndicator 
            lastUpdated={clientMetrics?.last_updated} 
            variant="compact"
          />
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6"
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
              <h3 className="text-lg font-semibold text-foreground mb-1">Success Rate Trends</h3>
              <p className="text-sm text-muted-foreground">Performance by workflow</p>
            </div>
            <div className="h-80 chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorSuccessRate" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="name" 
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis 
                    stroke="hsl(var(--muted-foreground))" 
                    fontSize={12}
                    domain={[0, 100]}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                    formatter={(value: any) => [`${value}%`, 'Success Rate']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="success_rate" 
                    stroke="#10B981" 
                    fillOpacity={1} 
                    fill="url(#colorSuccessRate)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </AnimatedCard>
        </motion.div>
      </div>

      {/* Detailed Tables */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <motion.div variants={fadeInUp}>
          <TabsList className="grid w-full grid-cols-2 lg:w-96">
            <TabsTrigger value="workflows" className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Workflows
              {selectedWorkflows.length > 0 && (
                <Badge variant="secondary" className="ml-2 text-xs">
                  {selectedWorkflows.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="executions" className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Executions
              {selectedExecutions.length > 0 && (
                <Badge variant="secondary" className="ml-2 text-xs">
                  {selectedExecutions.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
        </motion.div>

        <TabsContent value="workflows">
          <motion.div variants={fadeInUp}>
            <WorkflowMetricsTable 
              workflows={workflowStats?.workflow_stats || []}
              isLoading={workflowStatsLoading}
              title="Workflow Performance Analysis"
              description="Detailed metrics and performance data for each workflow"
              onSelectionChange={handleWorkflowSelection}
            />
          </motion.div>
        </TabsContent>

        <TabsContent value="executions">
          <motion.div variants={fadeInUp}>
            <ExecutionsList 
              executions={recentExecutions?.executions || []}
              isLoading={executionsLoading}
              onRefresh={handleRefresh}
              title="Recent Execution History"
              description="Latest workflow execution results and status"
              onSelectionChange={handleExecutionSelection}
            />
          </motion.div>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}

// Metric Card Component (same as in DashboardPage but extracted for reuse)
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
                <TrendingUp className="w-3 h-3 mr-1" />
              ) : (
                <TrendingDown className="w-3 h-3 mr-1" />
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

function ClientDashboardSkeleton() {
  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Skeleton className="w-20 h-8" />
          <div>
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <Skeleton className="w-32 h-8" />
          <Skeleton className="w-20 h-8" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-8 w-16" />
                  <Skeleton className="h-3 w-24" />
                </div>
                <Skeleton className="w-12 h-12 rounded-xl" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-80 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tables */}
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-96" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-96 w-full" />
        </CardContent>
      </Card>
    </div>
  )
}