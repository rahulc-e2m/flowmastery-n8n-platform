import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MetricsApi } from '@/services/metricsApi'
import { ClientApi } from '@/services/clientApi'
import { useAuth } from '@/contexts/AuthContext'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart3,
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  Building2,
  Zap,
  Timer,
  Target,
  Eye,
  Filter
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { AnimatedCard } from '@/components/ui/animated-card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Area, AreaChart } from 'recharts'
import { formatDistanceToNow } from 'date-fns'
import { 
  fadeInUp, 
  staggerContainer, 
  staggerItem, 
  pageTransition,
  scaleIn
} from '@/lib/animations'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']

export function MetricsPage() {
  const { isAdmin, isClient } = useAuth()
  const [selectedClientId, setSelectedClientId] = useState<string>('')
  const [selectedTab, setSelectedTab] = useState('overview')

  // Admin queries
  const { data: adminMetrics, isLoading: adminLoading } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: MetricsApi.getAllClientsMetrics,
    enabled: isAdmin,
    refetchInterval: 30000,
  })

  const { data: clients } = useQuery({
    queryKey: ['clients'],
    queryFn: ClientApi.getClients,
    enabled: isAdmin,
  })

  const { data: selectedClientMetrics, isLoading: selectedClientLoading } = useQuery({
    queryKey: ['client-metrics', selectedClientId],
    queryFn: () => MetricsApi.getClientMetrics(parseInt(selectedClientId)),
    enabled: isAdmin && !!selectedClientId,
    refetchInterval: 30000,
  })

  const { data: selectedClientWorkflows, isLoading: selectedClientWorkflowsLoading } = useQuery({
    queryKey: ['client-workflows', selectedClientId],
    queryFn: () => MetricsApi.getClientWorkflowMetrics(parseInt(selectedClientId)),
    enabled: isAdmin && !!selectedClientId,
    refetchInterval: 30000,
  })

  // Client queries
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
    return (
      <motion.div
        variants={pageTransition}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        <AdminMetricsView
          adminMetrics={adminMetrics}
          clients={clients}
          selectedClientId={selectedClientId}
          setSelectedClientId={setSelectedClientId}
          selectedClientMetrics={selectedClientMetrics}
          selectedClientWorkflows={selectedClientWorkflows}
          isLoading={adminLoading}
          selectedClientLoading={selectedClientLoading || selectedClientWorkflowsLoading}
        />
      </motion.div>
    )
  }

  if (isClient) {
    return (
      <motion.div
        variants={pageTransition}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        <ClientMetricsView
          metrics={clientMetrics}
          workflows={clientWorkflows}
          isLoading={clientMetricsLoading || clientWorkflowsLoading}
        />
      </motion.div>
    )
  }

  return null
}

function AdminMetricsView({
  adminMetrics,
  clients,
  selectedClientId,
  setSelectedClientId,
  selectedClientMetrics,
  selectedClientWorkflows,
  isLoading,
  selectedClientLoading
}: any) {
  if (isLoading) {
    return <MetricsSkeleton />
  }

  const overallStats = [
    {
      title: 'Total Clients',
      value: adminMetrics?.total_clients || 0,
      icon: Building2,
      color: 'blue',
      trend: { value: 12, isPositive: true },
      description: 'Active organizations'
    },
    {
      title: 'Total Workflows',
      value: adminMetrics?.total_workflows || 0,
      icon: Activity,
      color: 'green',
      trend: { value: 8, isPositive: true },
      description: 'Automated processes'
    },
    {
      title: 'Total Executions',
      value: (adminMetrics?.total_executions || 0).toLocaleString(),
      icon: Zap,
      color: 'purple',
      trend: { value: 24, isPositive: true },
      description: 'Last 30 days'
    },
    {
      title: 'Overall Success Rate',
      value: `${adminMetrics?.overall_success_rate || 0}%`,
      icon: TrendingUp,
      color: 'green',
      trend: { value: 2, isPositive: true },
      description: 'System performance'
    },
  ]

  const chartData = adminMetrics?.clients?.map((client: any) => ({
    name: client.client_name,
    workflows: client.total_workflows,
    executions: client.total_executions,
    successRate: client.success_rate,
  })) || []

  const pieData = adminMetrics?.clients?.map((client: any, index: number) => ({
    name: client.client_name,
    value: client.total_executions,
    color: COLORS[index % COLORS.length],
  })) || []

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <motion.div 
        variants={fadeInUp}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold text-gradient mb-2">Analytics Dashboard</h1>
          <p className="text-muted-foreground text-lg">Comprehensive workflow analytics across all clients</p>
        </div>
        <motion.div 
          className="flex items-center space-x-3"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3, type: 'spring' }}
        >
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800/30">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-green-700 dark:text-green-400">Real-time</span>
          </div>
          <Badge variant="outline" className="px-3 py-1">
            <Eye className="w-3 h-3 mr-1" />
            Live Analytics
          </Badge>
        </motion.div>
      </motion.div>

      <Tabs defaultValue="overview" className="space-y-6">
        <motion.div variants={scaleIn}>
          <TabsList className="grid w-full grid-cols-2 lg:w-96">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="client-detail" className="flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              Client Analysis
            </TabsTrigger>
          </TabsList>
        </motion.div>

        <TabsContent value="overview" className="space-y-6">
          {/* Overall Stats */}
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            variants={staggerContainer}
            initial="initial"
            animate="animate"
          >
            {overallStats.map((stat, index) => (
              <motion.div key={stat.title} variants={staggerItem}>
                <AnimatedCard key={stat.title} className="overflow-hidden">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                        <p className="text-3xl font-bold tracking-tight">{stat.value}</p>
                        {stat.trend && (
                          <div className={`flex items-center space-x-1 text-sm ${
                            stat.trend.isPositive ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {stat.trend.isPositive ? (
                              <TrendingUp className="w-3 h-3" />
                            ) : (
                              <TrendingDown className="w-3 h-3" />
                            )}
                            <span>{stat.trend.value}%</span>
                          </div>
                        )}
                      </div>
                      <div className={`p-3 rounded-xl bg-gradient-to-br ${
                        stat.color === 'blue' ? 'from-blue-500 to-blue-600' :
                        stat.color === 'green' ? 'from-green-500 to-green-600' :
                        stat.color === 'purple' ? 'from-purple-500 to-purple-600' :
                        'from-gray-500 to-gray-600'
                      }`}>
                        <stat.icon className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="mt-4">
                      <p className="text-xs text-muted-foreground">{stat.description}</p>
                    </div>
                  </CardContent>
                </AnimatedCard>
              </motion.div>
            ))}
          </motion.div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <motion.div variants={fadeInUp}>
              <AnimatedCard className="p-6">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-foreground mb-1">Client Performance</h3>
                  <p className="text-sm text-muted-foreground">Workflows and executions by client</p>
                </div>
                <div className="h-80 chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorExecutions" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis 
                        dataKey="name" 
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
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
                      <Area 
                        type="monotone" 
                        dataKey="executions" 
                        stroke="#3B82F6" 
                        fillOpacity={1} 
                        fill="url(#colorExecutions)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </AnimatedCard>
            </motion.div>

            <motion.div variants={fadeInUp}>
              <AnimatedCard className="p-6">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-foreground mb-1">Execution Distribution</h3>
                  <p className="text-sm text-muted-foreground">Total executions by client</p>
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
                        {pieData.map((entry, index) => (
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
        </TabsContent>

        <TabsContent value="client-detail" className="space-y-6">
          <motion.div variants={fadeInUp}>
            <AnimatedCard className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-1">Client Analysis</h3>
                  <p className="text-sm text-muted-foreground">Detailed metrics for individual clients</p>
                </div>
                <Select value={selectedClientId} onValueChange={setSelectedClientId}>
                  <SelectTrigger className="w-64">
                    <Filter className="w-4 h-4 mr-2" />
                    <SelectValue placeholder="Select a client" />
                  </SelectTrigger>
                  <SelectContent>
                    {clients?.map((client: any) => (
                      <SelectItem key={client.id} value={client.id.toString()}>
                        {client.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <AnimatePresence mode="wait">
                {selectedClientLoading ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {Array.from({ length: 4 }).map((_, i) => (
                          <div key={i} className="animate-pulse">
                            <div className="bg-muted/50 h-24 rounded-lg" />
                          </div>
                        ))}
                      </div>
                      <div className="bg-muted/50 h-64 rounded-lg animate-pulse" />
                    </div>
                  </motion.div>
                ) : selectedClientMetrics ? (
                  <motion.div
                    key="data"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <ClientDetailView 
                      metrics={selectedClientMetrics}
                      workflows={selectedClientWorkflows}
                    />
                  </motion.div>
                ) : (
                  <motion.div
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-center py-12 text-muted-foreground"
                  >
                    <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Select a client to view detailed analytics</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </AnimatedCard>
          </motion.div>
        </TabsContent>
      </Tabs>
    </div>
  )
}


function ClientMetricsView({ metrics, workflows, isLoading }: any) {
  if (isLoading) {
    return <MetricsSkeleton />
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Metrics</h1>
        <p className="text-gray-600 mt-2">Your workflow performance and analytics</p>
      </div>

      <ClientDetailView metrics={metrics} workflows={workflows} isLoading={false} />
    </div>
  )
}

function ClientDetailView({ metrics, workflows, isLoading }: any) {
  if (isLoading) {
    return <MetricsSkeleton />
  }

  if (!metrics) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <p className="text-gray-500">No metrics available</p>
      </div>
    )
  }

  const stats = [
    {
      title: 'Total Workflows',
      value: metrics.total_workflows || 0,
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Active Workflows',
      value: metrics.active_workflows || 0,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Total Executions',
      value: metrics.total_executions || 0,
      icon: BarChart3,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Success Rate',
      value: `${metrics.success_rate || 0}%`,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-full ${stat.bgColor}`}>
                  <stat.icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Workflows Detail */}
      <Card>
        <CardHeader>
          <CardTitle>Workflow Details</CardTitle>
          <CardDescription>Individual workflow performance metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {workflows?.workflows?.map((workflow: any) => (
              <div key={workflow.workflow_id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    workflow.status === 'active' ? 'bg-green-100' : 
                    workflow.status === 'error' ? 'bg-red-100' : 'bg-gray-100'
                  }`}>
                    {workflow.status === 'active' ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : workflow.status === 'error' ? (
                      <XCircle className="w-5 h-5 text-red-600" />
                    ) : (
                      <Clock className="w-5 h-5 text-gray-600" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{workflow.workflow_name}</h3>
                    <p className="text-sm text-gray-500">
                      {workflow.total_executions} executions • {workflow.success_rate}% success
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <p className="text-sm font-medium text-gray-900">{workflow.successful_executions}</p>
                    <p className="text-xs text-green-600">Success</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-gray-900">{workflow.failed_executions}</p>
                    <p className="text-xs text-red-600">Failed</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-gray-900">
                      {workflow.avg_execution_time ? `${workflow.avg_execution_time}s` : 'N/A'}
                    </p>
                    <p className="text-xs text-gray-500">Avg Time</p>
                  </div>
                  <Badge variant={workflow.status === 'active' ? 'default' : workflow.status === 'error' ? 'destructive' : 'secondary'}>
                    {workflow.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function MetricsSkeleton() {
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