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
  Eye
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

import { Skeleton } from '@/components/ui/skeleton'
import { AnimatedCard } from '@/components/ui/animated-card'
import { DataSourceIndicator } from '@/components/ui/data-source-indicator'
import { TrendIndicator } from '@/components/ui/trend-indicator'
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
          isLoading={adminLoading}
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
  isLoading
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
      trend: { value: Math.abs(adminMetrics?.trends?.execution_trend || 0), isPositive: (adminMetrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Active organizations'
    },
    {
      title: 'Total Workflows',
      value: adminMetrics?.total_workflows || 0,
      icon: Activity,
      color: 'green',
      trend: { value: Math.abs(adminMetrics?.trends?.execution_trend || 0), isPositive: (adminMetrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Automated processes'
    },
    {
      title: 'Total Executions',
      value: (adminMetrics?.total_executions || 0).toLocaleString(),
      icon: Zap,
      color: 'purple',
      trend: { value: Math.abs(adminMetrics?.trends?.execution_trend || 0), isPositive: (adminMetrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Last 30 days'
    },
    {
      title: 'Hours Saved',
      value: adminMetrics?.total_time_saved_hours ? `${adminMetrics.total_time_saved_hours}h` : '0h',
      icon: Timer,
      color: 'orange',
      trend: { value: Math.abs(adminMetrics?.trends?.execution_trend || 0), isPositive: (adminMetrics?.trends?.execution_trend || 0) >= 0 },
      description: 'Time saved by automation'
    },
    {
      title: 'Overall Success Rate',
      value: `${adminMetrics?.overall_success_rate?.toFixed(1) || '0.0'}%`,
      icon: TrendingUp,
      color: 'green',
      trend: { value: Math.abs(adminMetrics?.trends?.success_rate_trend || 0), isPositive: (adminMetrics?.trends?.success_rate_trend || 0) >= 0 },
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
        <DataSourceIndicator 
          lastUpdated={adminMetrics?.last_updated} 
          variant="full"
        />
      </motion.div>

      <Tabs defaultValue="overview" className="space-y-6">
        <motion.div variants={scaleIn}>
          <TabsList className="grid w-full grid-cols-1 lg:w-48">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Overview
            </TabsTrigger>
          </TabsList>
        </motion.div>

        <TabsContent value="overview" className="space-y-6">
          {/* Overall Stats */}
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6"
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
                          <TrendIndicator value={stat.trend.value} isPositive={stat.trend.isPositive} />
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

          {/* Client Quick Access */}
          <motion.div variants={fadeInUp}>
            <AnimatedCard className="p-6">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-foreground mb-1">Client Details</h3>
                <p className="text-sm text-muted-foreground">Access detailed analytics for individual clients</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {adminMetrics?.clients?.map((client: any) => (
                  <motion.div
                    key={client.client_id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Card 
                      className="cursor-pointer hover:shadow-md transition-all duration-200 border-2 hover:border-primary/20"
                      onClick={() => window.location.href = `/client/${client.client_id}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <div className="p-2 rounded-lg bg-primary/10">
                              <Building2 className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <h4 className="font-semibold text-foreground">{client.client_name}</h4>
                              <p className="text-xs text-muted-foreground">
                                {client.total_workflows} workflows
                              </p>
                            </div>
                          </div>
                          <Eye className="w-4 h-4 text-muted-foreground" />
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <p className="text-muted-foreground">Executions</p>
                            <p className="font-semibold">{client.total_executions.toLocaleString()}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Success Rate</p>
                            <p className="font-semibold text-green-600">{client.success_rate?.toFixed(1) || '0.0'}%</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
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
      icon: Timer,
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
    <div className="p-6 space-y-8">
      {/* Header */}
      <motion.div 
        variants={fadeInUp}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold text-gradient mb-2">My Analytics</h1>
          <p className="text-muted-foreground text-lg">Your workflow performance and analytics</p>
        </div>
        <DataSourceIndicator 
          lastUpdated={metrics?.last_updated || workflows?.last_updated} 
          variant="compact"
        />
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
            <AnimatedCard key={stat.title} className="overflow-hidden">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                    <p className="text-3xl font-bold tracking-tight">{stat.value}</p>
                    {stat.trend && (
                      <TrendIndicator value={stat.trend.value} isPositive={stat.trend.isPositive} />
                    )}
                  </div>
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${
                    stat.color === 'blue' ? 'from-blue-500 to-blue-600' :
                    stat.color === 'green' ? 'from-green-500 to-green-600' :
                    stat.color === 'purple' ? 'from-purple-500 to-purple-600' :
                    stat.color === 'orange' ? 'from-orange-500 to-orange-600' :
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

      <ClientDetailView metrics={metrics} workflows={workflows} sortedWorkflows={sortedWorkflows} isLoading={false} />
    </div>
  )
}

function ClientDetailView({ metrics, workflows, sortedWorkflows, isLoading }: any) {
  if (isLoading) {
    return <MetricsSkeleton />
  }

  if (!metrics) {
    return (
      <motion.div 
        className="text-center py-12"
        variants={fadeInUp}
      >
        <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">No metrics available</p>
      </motion.div>
    )
  }

  return (
    <motion.div 
      className="space-y-6"
      variants={fadeInUp}
    >
      {/* Recent Workflows */}
      <AnimatedCard className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-semibold text-foreground mb-1">Workflow Performance</h3>
            <p className="text-muted-foreground">Individual workflow metrics and status</p>
          </div>
          <Badge variant="outline" className="px-3 py-1">
            {workflows?.workflows?.length || 0} Total
          </Badge>
        </div>
        
        <div className="space-y-4">
          {sortedWorkflows.map((workflow: any, index: number) => {
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
                        ? 'bg-green-100 dark:bg-green-950/50' 
                        : workflow.status === 'error' 
                        ? 'bg-red-100 dark:bg-red-950/50' 
                        : 'bg-gray-100 dark:bg-gray-950/50'
                    }`}
                    whileHover={{ rotate: 5, scale: 1.1 }}
                  >
                    {isRecentlyActive ? (
                      <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                    ) : workflow.status === 'error' ? (
                      <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                    ) : (
                      <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    )}
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
                      {workflow.total_executions} executions • {workflow.success_rate?.toFixed(1) || '0.0'}% success
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <p className="text-sm font-medium text-foreground">{workflow.successful_executions}</p>
                    <p className="text-xs text-green-600 dark:text-green-400">Success</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-foreground">{workflow.failed_executions}</p>
                    <p className="text-xs text-red-600 dark:text-red-400">Failed</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-foreground">
                      {workflow.avg_execution_time ? `${workflow.avg_execution_time}s` : 'N/A'}
                    </p>
                    <p className="text-xs text-muted-foreground">Avg Time</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-foreground">
                      {workflow.time_saved_hours ? `${workflow.time_saved_hours}h` : '0h'}
                    </p>
                    <p className="text-xs text-orange-600 dark:text-orange-400">Time Saved</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-muted-foreground">Last run</p>
                    <p className="text-sm font-medium text-foreground">
                      {workflow.last_execution ? 
                        formatDistanceToNow(new Date(workflow.last_execution), { addSuffix: true }) : 
                        'Never'
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
  )
}

function MetricsSkeleton() {
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