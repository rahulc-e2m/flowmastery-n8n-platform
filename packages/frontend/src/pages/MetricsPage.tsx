import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MetricsApi } from '@/services/metricsApi'
import { ClientApi } from '@/services/clientApi'
import { useAuth } from '@/contexts/AuthContext'
import {
  BarChart3,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Building2,
  Zap,
  Timer,
  Target
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { formatDistanceToNow } from 'date-fns'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']

export function MetricsPage() {
  const { isAdmin, isClient } = useAuth()
  const [selectedClientId, setSelectedClientId] = useState<string>('')

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
    )
  }

  if (isClient) {
    return (
      <ClientMetricsView
        metrics={clientMetrics}
        workflows={clientWorkflows}
        isLoading={clientMetricsLoading || clientWorkflowsLoading}
      />
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
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Total Workflows',
      value: adminMetrics?.total_workflows || 0,
      icon: Activity,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Total Executions',
      value: adminMetrics?.total_executions || 0,
      icon: BarChart3,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Overall Success Rate',
      value: `${adminMetrics?.overall_success_rate || 0}%`,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
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
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Metrics Dashboard</h1>
        <p className="text-gray-600 mt-2">Overview of all clients and their performance</p>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="client-detail">Client Details</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Overall Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {overallStats.map((stat) => (
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

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Client Workflows & Executions</CardTitle>
                <CardDescription>Comparison across all clients</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="workflows" fill="#3B82F6" name="Workflows" />
                    <Bar dataKey="executions" fill="#10B981" name="Executions" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Execution Distribution</CardTitle>
                <CardDescription>Total executions by client</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Client List */}
          <Card>
            <CardHeader>
              <CardTitle>All Clients</CardTitle>
              <CardDescription>Detailed metrics for each client</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {adminMetrics?.clients?.map((client: any) => (
                  <div key={client.client_id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Building2 className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{client.client_name}</h3>
                        <p className="text-sm text-gray-500">
                          {client.total_workflows} workflows • {client.total_executions} executions
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Badge variant={client.success_rate >= 90 ? 'default' : client.success_rate >= 70 ? 'secondary' : 'destructive'}>
                        {client.success_rate}% success
                      </Badge>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">{client.active_workflows} active</p>
                        <p className="text-xs text-gray-500">
                          {client.last_activity ? formatDistanceToNow(new Date(client.last_activity), { addSuffix: true }) : 'No activity'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="client-detail" className="space-y-6">
          <div className="flex items-center space-x-4">
            <Select value={selectedClientId} onValueChange={setSelectedClientId}>
              <SelectTrigger className="w-64">
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

          {selectedClientId && (
            <ClientDetailView
              metrics={selectedClientMetrics}
              workflows={selectedClientWorkflows}
              isLoading={selectedClientLoading}
            />
          )}
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