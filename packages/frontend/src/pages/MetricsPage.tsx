import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Bot, 
  RefreshCw, 
  Settings, 
  Play, 
  Pause, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Users, 
  TrendingUp,
  Activity,
  Zap,
  Database
} from 'lucide-react'
import { useMetrics, useConfigStatus, useRefreshMetrics } from '@/hooks/useMetrics'

interface MetricsData {
  status: string
  timestamp: string
  response_time: number
  connection_healthy: boolean
  workflows: {
    total_workflows: number
    active_workflows: number
    inactive_workflows: number
  }
  executions: {
    total_executions: number
    success_executions: number
    error_executions: number
    success_rate: number
    today_executions: number
  }
  users: {
    total_users: number
    admin_users: number
    member_users: number
  }
  system: {
    total_variables: number
    total_tags: number
  }
  derived_metrics: {
    time_saved_hours: number
    activity_score: number
    automation_efficiency: number
    workflows_per_user: number
    executions_per_workflow: number
  }
}

const MetricsPage: React.FC = () => {
  const { data: configStatus } = useConfigStatus()
  const { data: metrics, isLoading: loading, error, refetch } = useMetrics(false)
  const [refreshing, setRefreshing] = useState(false)
  const { refreshFull } = useRefreshMetrics()

  // Mock data for demonstration
  const mockMetrics: MetricsData = {
    status: 'success',
    timestamp: new Date().toISOString(),
    response_time: 0.45,
    connection_healthy: true,
    workflows: {
      total_workflows: 24,
      active_workflows: 18,
      inactive_workflows: 6
    },
    executions: {
      total_executions: 15847,
      success_executions: 14923,
      error_executions: 924,
      success_rate: 94.2,
      today_executions: 156
    },
    users: {
      total_users: 8,
      admin_users: 2,
      member_users: 6
    },
    system: {
      total_variables: 45,
      total_tags: 12
    },
    derived_metrics: {
      time_saved_hours: 342,
      activity_score: 87,
      automation_efficiency: 94.2,
      workflows_per_user: 3.0,
      executions_per_workflow: 660.3
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await refetch()
    setRefreshing(false)
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center space-y-4">
            <RefreshCw className="h-8 w-8 animate-spin text-primary mx-auto" />
            <p className="text-muted-foreground">Loading n8n metrics...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!configStatus?.configured) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <Settings className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">n8n Configuration Required</h3>
          <p className="text-muted-foreground mb-4">
            Configure your n8n instance to view metrics and analytics
          </p>
          <Button variant="gradient">
            Configure n8n Instance
          </Button>
        </div>
      </div>
    )
  }

  if (error || !metrics) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <XCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Failed to Load Metrics</h3>
          <p className="text-muted-foreground mb-4">
            {error instanceof Error ? error.message : 'Unknown error occurred'}
          </p>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Bot className="h-8 w-8 text-primary" />
            n8n Instance Metrics
          </h1>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-muted-foreground">
              {configStatus?.instance_name || 'My n8n Instance'}
            </span>
            <Badge 
              variant={metrics.connection_healthy ? 'success' : 'destructive'}
              className="flex items-center gap-1"
            >
              <div className="w-2 h-2 rounded-full bg-current animate-pulse" />
              {metrics.connection_healthy ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
        </div>
        
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </Button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Workflows</p>
                <p className="text-3xl font-bold">{metrics.workflows.total_workflows}</p>
              </div>
              <div className="p-3 bg-primary/10 rounded-lg">
                <Bot className="h-6 w-6 text-primary" />
              </div>
            </div>
            <div className="flex items-center gap-4 mt-4 text-sm">
              <div className="flex items-center gap-1 text-success-500">
                <Play className="h-3 w-3" />
                {metrics.workflows.active_workflows} Active
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <Pause className="h-3 w-3" />
                {metrics.workflows.inactive_workflows} Inactive
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Today's Executions</p>
                <p className="text-3xl font-bold">{metrics.executions.today_executions}</p>
              </div>
              <div className="p-3 bg-success-500/10 rounded-lg">
                <Activity className="h-6 w-6 text-success-500" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-4 text-sm text-success-500">
              <CheckCircle className="h-3 w-3" />
              {metrics.executions.success_rate}% Success Rate
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Time Saved</p>
                <p className="text-3xl font-bold">{metrics.derived_metrics.time_saved_hours}h</p>
              </div>
              <div className="p-3 bg-warning-500/10 rounded-lg">
                <Clock className="h-6 w-6 text-warning-500" />
              </div>
            </div>
            <p className="text-sm text-muted-foreground mt-4">Last 7 days</p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Users</p>
                <p className="text-3xl font-bold">{metrics.users.total_users}</p>
              </div>
              <div className="p-3 bg-blue-500/10 rounded-lg">
                <Users className="h-6 w-6 text-blue-500" />
              </div>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              {metrics.users.admin_users} Admins, {metrics.users.member_users} Members
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Execution Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Execution Breakdown
            </CardTitle>
            <CardDescription>Last 7 days execution statistics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-success-500" />
                  Successful
                </span>
                <span className="font-medium">{metrics.executions.success_executions.toLocaleString()}</span>
              </div>
              <Progress 
                value={(metrics.executions.success_executions / metrics.executions.total_executions) * 100} 
                className="h-2"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-destructive" />
                  Failed
                </span>
                <span className="font-medium">{metrics.executions.error_executions.toLocaleString()}</span>
              </div>
              <Progress 
                value={(metrics.executions.error_executions / metrics.executions.total_executions) * 100} 
                className="h-2"
              />
            </div>

            <div className="pt-2 border-t text-sm text-muted-foreground">
              Total: {metrics.executions.total_executions.toLocaleString()} executions
            </div>
          </CardContent>
        </Card>

        {/* System Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              System Performance
            </CardTitle>
            <CardDescription>Activity score: {metrics.derived_metrics.activity_score}/100</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Variables</p>
                <p className="text-2xl font-bold">{metrics.system.total_variables}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Tags</p>
                <p className="text-2xl font-bold">{metrics.system.total_tags}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Workflows/User</p>
                <p className="text-2xl font-bold">{metrics.derived_metrics.workflows_per_user}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Efficiency</p>
                <p className="text-2xl font-bold">{metrics.derived_metrics.automation_efficiency}%</p>
              </div>
            </div>
            
            <div className="pt-2 border-t text-sm text-muted-foreground">
              Response time: {metrics.response_time}s
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Time Saved Highlight */}
      <Card className="bg-gradient-primary/10 border-primary/20">
        <CardContent className="p-8">
          <div className="flex items-center justify-center gap-8">
            <div className="p-6 bg-primary/20 rounded-full">
              <Clock className="h-12 w-12 text-primary" />
            </div>
            <div className="text-center">
              <h3 className="text-2xl font-bold mb-2">Time Saved This Week</h3>
              <div className="text-5xl font-bold bg-gradient-primary bg-clip-text text-transparent mb-2">
                {metrics.derived_metrics.time_saved_hours} Hours
              </div>
              <p className="text-muted-foreground">
                Your automation workflows have saved significant time this week
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="mt-8 text-center text-sm text-muted-foreground">
        Last updated: {new Date(metrics.timestamp).toLocaleString()} • 
        Data refreshed automatically every 5 minutes
      </div>
    </div>
  )
}

export default MetricsPage