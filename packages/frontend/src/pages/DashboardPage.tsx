import React from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { MetricsApi } from '@/services/metricsApi'
import { ClientApi } from '@/services/clientApi'
import { 
  BarChart3, 
  Building2, 
  Users, 
  Activity,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDistanceToNow } from 'date-fns'

export function DashboardPage() {
  const { user, isAdmin, isClient } = useAuth()

  // Admin dashboard data
  const { data: adminMetrics, isLoading: adminLoading } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: MetricsApi.getAllClientsMetrics,
    enabled: isAdmin,
    refetchInterval: 30000, // Refresh every 30 seconds
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
  if (isLoading) {
    return <DashboardSkeleton />
  }

  const stats = [
    {
      title: 'Total Clients',
      value: metrics?.total_clients || 0,
      icon: Building2,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Total Workflows',
      value: metrics?.total_workflows || 0,
      icon: Activity,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Total Executions',
      value: metrics?.total_executions || 0,
      icon: BarChart3,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Success Rate',
      value: `${metrics?.overall_success_rate || 0}%`,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600 mt-2">Overview of all clients and their metrics</p>
      </div>

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

      {/* Clients Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Clients Overview</CardTitle>
          <CardDescription>Performance metrics for all clients</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {metrics?.clients?.map((client: any) => (
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
    </div>
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
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Active Workflows',
      value: metrics?.active_workflows || 0,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Total Executions',
      value: metrics?.total_executions || 0,
      icon: BarChart3,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Success Rate',
      value: `${metrics?.success_rate || 0}%`,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Your workflow metrics and performance</p>
      </div>

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

      {/* Workflows Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Workflows Overview</CardTitle>
          <CardDescription>Performance of your individual workflows</CardDescription>
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
                <div className="flex items-center space-x-4">
                  <Badge variant={workflow.status === 'active' ? 'default' : workflow.status === 'error' ? 'destructive' : 'secondary'}>
                    {workflow.status}
                  </Badge>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {workflow.avg_execution_time ? `${workflow.avg_execution_time}s avg` : 'N/A'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {workflow.last_execution ? formatDistanceToNow(new Date(workflow.last_execution), { addSuffix: true }) : 'No executions'}
                    </p>
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