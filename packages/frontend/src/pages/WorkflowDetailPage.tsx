import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import ReactMarkdown from 'react-markdown'
import { 
  Edit2, 
  Save, 
  X, 
  ArrowLeft,
  ExternalLink
} from 'lucide-react'
import { VistaraWorkflowsApi, type UpdateVistaraWorkflowData } from '@/services/vistaraWorkflowsApi'
import { 
  fadeInUp, 
  staggerContainer, 
  pageTransition
} from '@/lib/animations'
import { toast } from 'sonner'
import { formatDistanceToNow } from 'date-fns'


const formatExecutionTime = (ms: number) => {
  if (ms < 1000) return `${formatDecimal(ms)}ms`
  if (ms < 60000) {
    const seconds = ms / 1000
    return `${formatDecimal(seconds)}s`
  }
  const minutes = ms / 60000
  return `${formatDecimal(minutes)}m`
}


const formatDecimal = (value: number, maxDecimals: number = 2): string => {
  if (value % 1 === 0) {
    return value.toString()
  }
  return value.toFixed(Math.min(maxDecimals, 2))
}

export function WorkflowDetailPage() {
  const { workflowId } = useParams<{ workflowId: string }>()
  const queryClient = useQueryClient()

  // State for editing
  const [editingSummary, setEditingSummary] = React.useState(false)
  const [editingDocumentation, setEditingDocumentation] = React.useState(false)
  const [editingWorkflowName, setEditingWorkflowName] = React.useState(false)
  const [editingTimeMetrics, setEditingTimeMetrics] = React.useState(false)
  const [editingExecutionStats, setEditingExecutionStats] = React.useState(false)
  const [summaryValue, setSummaryValue] = React.useState('')
  const [documentationValue, setDocumentationValue] = React.useState('')
  const [workflowNameValue, setWorkflowNameValue] = React.useState('')
  const [timeMetricsValues, setTimeMetricsValues] = React.useState({
    manual_time_minutes: 0,
    avg_execution_time_ms: 0,
    time_saved_per_execution_minutes: 0,
    total_time_saved_hours: 0
  })
  const [executionStatsValues, setExecutionStatsValues] = React.useState({
    total_executions: 0,
    successful_executions: 0,
    failed_executions: 0,
    success_rate: 0
  })

  // Fetch workflow details
  const { data: workflow, isLoading, error } = useQuery({
    queryKey: ['vistara-workflow', workflowId],
    queryFn: () => workflowId ? VistaraWorkflowsApi.getVistaraWorkflowDetails(workflowId) : null,
    enabled: !!workflowId,
  })

  // Update workflow mutation
  const updateWorkflowMutation = useMutation({
    mutationFn: (data: { id: string; updates: UpdateVistaraWorkflowData }) =>
      VistaraWorkflowsApi.updateVistaraWorkflow(data.id, data.updates),
    onSuccess: (updatedWorkflow, variables) => {
      // Update the cache with the new data immediately
      queryClient.setQueryData(['vistara-workflow', workflowId], updatedWorkflow)
      
      // Force a refetch to ensure UI reflects the latest data
      queryClient.invalidateQueries({ 
        queryKey: ['vistara-workflow', workflowId],
        refetchType: 'active'
      })
      
      // Also invalidate the workflows list
      queryClient.invalidateQueries({ queryKey: ['vistara-workflows'] })
      
      toast.success('Workflow updated successfully')
      
      // Log for debugging
      console.log('Workflow updated:', updatedWorkflow)
      console.log('Variables sent:', variables)
    },
    onError: (error: any) => {
      toast.error('Failed to update workflow')
      console.error('Update error:', error)
      // Re-fetch the data to ensure consistency
      queryClient.invalidateQueries({ 
        queryKey: ['vistara-workflow', workflowId],
        refetchType: 'active'
      })
    },
  })

  // Computed values
  const metrics = workflow?.metrics || {
    total_executions: 0,
    successful_executions: 0,
    failed_executions: 0,
    success_rate: 0,
    avg_execution_time_ms: 0,
    manual_time_minutes: 0
  }
  
  const calculatedTotalTimeSaved = workflow?.metrics.total_time_saved_hours || 0

  // Initialize form values when workflow loads
  React.useEffect(() => {
    if (workflow) {
      setSummaryValue(workflow.summary || '')
      setDocumentationValue(workflow.documentation_link || '')
      setWorkflowNameValue(workflow.workflow_name)
      setTimeMetricsValues({
        manual_time_minutes: workflow.metrics.manual_time_minutes,
        avg_execution_time_ms: workflow.metrics.avg_execution_time_ms,
        time_saved_per_execution_minutes: workflow.metrics.time_saved_per_execution_minutes,
        total_time_saved_hours: workflow.metrics.total_time_saved_hours
      })
      setExecutionStatsValues({
        total_executions: workflow.metrics.total_executions,
        successful_executions: workflow.metrics.successful_executions,
        failed_executions: workflow.metrics.failed_executions,
        success_rate: workflow.metrics.success_rate
      })
    }
  }, [workflow])

  // Handle form submissions
  const handleSaveSummary = () => {
    if (workflow) {
      updateWorkflowMutation.mutate({
        id: workflow.id,
        updates: { summary: summaryValue }
      })
      setEditingSummary(false)
    }
  }

  const handleSaveDocumentation = () => {
    if (workflow) {
      updateWorkflowMutation.mutate({
        id: workflow.id,
        updates: { documentation_link: documentationValue }
      })
      setEditingDocumentation(false)
    }
  }

  const handleSaveWorkflowName = () => {
    if (workflow) {
      updateWorkflowMutation.mutate({
        id: workflow.id,
        updates: { workflow_name: workflowNameValue }
      })
      setEditingWorkflowName(false)
    }
  }

  const handleOpenInN8n = () => {
    if (workflow?.n8n_workflow_id && workflow?.client?.n8n_api_url) {
      try {
        // Convert API URL to web UI URL
        const apiUrl = workflow.client.n8n_api_url
        // Remove /api/v1 from the end and construct workflow URL
        const baseUrl = apiUrl.replace(/\/api\/v1\/?$/, '')
        const n8nUrl = `${baseUrl}/workflow/${workflow.n8n_workflow_id}`
        
        // Validate the URL
        new URL(n8nUrl)
        console.log('Opening n8n URL:', n8nUrl)
        window.open(n8nUrl, '_blank', 'noopener,noreferrer')
      } catch (error) {
        console.error('Invalid n8n URL:', error)
        toast.error('Invalid n8n URL configuration. Please contact your administrator.')
      }
    } else if (!workflow?.n8n_workflow_id) {
      toast.error('No n8n workflow ID available')
    } else if (!workflow?.client?.n8n_api_url) {
      toast.error('No n8n instance URL configured for this client')
    }
  }

  const handleSaveTimeMetrics = () => {
    if (workflow) {
      console.log('Saving time metrics:', timeMetricsValues)
      console.log('Workflow ID:', workflow.id)
      
      updateWorkflowMutation.mutate({
        id: workflow.id,
        updates: timeMetricsValues
      })
      setEditingTimeMetrics(false)
    }
  }

  const handleSaveExecutionStats = () => {
    if (workflow) {
      console.log('Saving execution stats:', executionStatsValues)
      console.log('Workflow ID:', workflow.id)
      
      updateWorkflowMutation.mutate({
        id: workflow.id,
        updates: executionStatsValues
      })
      setEditingExecutionStats(false)
    }
  }

  const handleTimeMetricsChange = (field: keyof typeof timeMetricsValues, value: number) => {
    setTimeMetricsValues(prev => {
      const newValues = {
        ...prev,
        [field]: value
      }
      
      // Auto-calculate derived values
      if (field === 'manual_time_minutes' || field === 'avg_execution_time_ms') {
        // Calculate time saved per execution: manual_time_minutes - (avg_execution_time_ms / 60000)
        const manualTimeMinutes = field === 'manual_time_minutes' ? value : prev.manual_time_minutes
        const avgExecutionTimeMs = field === 'avg_execution_time_ms' ? value : prev.avg_execution_time_ms
        const executionTimeMinutes = avgExecutionTimeMs / 60000
        const timeSavedPerRun = Math.max(0, manualTimeMinutes - executionTimeMinutes)
        
        newValues.time_saved_per_execution_minutes = timeSavedPerRun
        
        // Calculate total time saved: time_saved_per_execution_minutes * total_executions / 60 (convert to hours)
        const totalExecutions = executionStatsValues.total_executions || 0
        newValues.total_time_saved_hours = (timeSavedPerRun * totalExecutions) / 60
      }
      
      if (field === 'time_saved_per_execution_minutes') {
        // Calculate total time saved when time saved per run is directly changed
        const totalExecutions = executionStatsValues.total_executions || 0
        newValues.total_time_saved_hours = (value * totalExecutions) / 60
      }
      
      return newValues
    })
  }

  const handleExecutionStatsChange = (field: keyof typeof executionStatsValues, value: number) => {
    setExecutionStatsValues(prev => {
      const newValues = {
        ...prev,
        [field]: value
      }
      
      // Auto-calculate success rate and ensure consistency between execution counts
      if (field === 'successful_executions' || field === 'failed_executions') {
        const successfulExecutions = field === 'successful_executions' ? value : prev.successful_executions
        const failedExecutions = field === 'failed_executions' ? value : prev.failed_executions
        
        // Auto-update total executions
        newValues.total_executions = successfulExecutions + failedExecutions
        
        // Calculate success rate
        const totalExecutions = successfulExecutions + failedExecutions
        if (totalExecutions > 0) {
          newValues.success_rate = parseFloat(((successfulExecutions / totalExecutions) * 100).toFixed(2))
        } else {
          newValues.success_rate = 0
        }
      } else if (field === 'total_executions') {
        // When total executions is manually changed, recalculate success rate
        const successfulExecutions = prev.successful_executions
        if (value > 0) {
          newValues.success_rate = parseFloat(((successfulExecutions / value) * 100).toFixed(2))
        } else {
          newValues.success_rate = 0
        }
      } else if (field === 'success_rate') {
        // When success rate is manually changed, don't auto-calculate (allow manual override)
        // Just store the value as is
      }
      
      return newValues
    })
    
    // Also update total time saved in time metrics when total executions changes
    if (field === 'total_executions') {
      setTimeMetricsValues(prev => ({
        ...prev,
        total_time_saved_hours: (prev.time_saved_per_execution_minutes * value) / 60
      }))
    }
  }

  const handleCancelSummaryEdit = () => {
    setEditingSummary(false)
    setSummaryValue(workflow?.summary || '')
  }

  const handleCancelDocumentationEdit = () => {
    setEditingDocumentation(false)
    setDocumentationValue(workflow?.documentation_link || '')
  }

  const handleCancelTimeMetricsEdit = () => {
    setEditingTimeMetrics(false)
    if (workflow) {
      setTimeMetricsValues({
        manual_time_minutes: workflow.metrics.manual_time_minutes,
        avg_execution_time_ms: workflow.metrics.avg_execution_time_ms,
        time_saved_per_execution_minutes: workflow.metrics.time_saved_per_execution_minutes,
        total_time_saved_hours: workflow.metrics.total_time_saved_hours
      })
    }
  }

  const handleCancelExecutionStatsEdit = () => {
    setEditingExecutionStats(false)
    if (workflow) {
      setExecutionStatsValues({
        total_executions: workflow.metrics.total_executions,
        successful_executions: workflow.metrics.successful_executions,
        failed_executions: workflow.metrics.failed_executions,
        success_rate: workflow.metrics.success_rate
      })
    }
  }

  if (!workflowId) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Invalid Workflow</h1>
        <p className="text-gray-600 mb-6">No workflow ID provided.</p>
        <Link to="/vistara">
          <Button>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Vistara
          </Button>
        </Link>
      </div>
    </div>
  )
}

if (isLoading) {
  return (
    <div className="p-6">
      <div className="h-8 bg-muted animate-pulse rounded mb-6" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-64 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded" />
      </div>
    </div>
  )
}

if (error || !workflow) {
  return (
    <div className="p-6">
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-4">Workflow Not Found</h1>
        <p className="text-muted-foreground mb-6">The requested workflow could not be found.</p>
        <Link to="/vistara">
          <Button>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Vistara
          </Button>
        </Link>
      </div>
    </div>
  )
}

  return (
    <motion.div
    variants={pageTransition}
    initial="initial"
    animate="animate"
    exit="exit"
  >
    <div className="p-6 space-y-8">
      {/* Header */}
      <motion.div
        variants={fadeInUp}
        className="flex items-center justify-between"
      >
        <div>
          {editingWorkflowName ? (
            <div className="flex items-center gap-2">
              <Input
                value={workflowNameValue}
                onChange={(e) => setWorkflowNameValue(e.target.value)}
                className="text-4xl font-bold text-gradient h-auto border-none bg-transparent p-0 focus-visible:ring-0"
                disabled={updateWorkflowMutation.isPending}
              />
              <Button size="sm" onClick={handleSaveWorkflowName} disabled={updateWorkflowMutation.isPending}>
                <Save className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={() => { setEditingWorkflowName(false); setWorkflowNameValue(workflow.workflow_name); }}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <h1
              className="text-4xl font-bold text-gradient mb-2 cursor-pointer hover:opacity-80"
              onDoubleClick={() => setEditingWorkflowName(true)}
              title="Double-click to edit"
            >
              {workflow.workflow_name}
            </h1>
          )}
          <p className="text-muted-foreground">Updated {formatDistanceToNow(new Date(workflow.updated_at))} ago</p>
        </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleOpenInN8n}>
              <ExternalLink className="w-4 h-4 mr-2" /> Open in n8n
            </Button>
            <Link to="/vistara">
              <Button variant="outline" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back
              </Button>
            </Link>
          </div>
      </motion.div>

      {/* Top meta row */}
      <motion.div variants={fadeInUp} className="flex flex-wrap items-center gap-3">
        {workflow.category && (
          <Badge className="text-white border-0" style={{ backgroundColor: workflow.category.color }}>
            {workflow.category.name}
          </Badge>
        )}
        <Badge variant="outline">{workflow.metrics.total_executions.toLocaleString()} runs</Badge>
        <Badge variant="outline">Success {formatDecimal(workflow.metrics.success_rate)}%</Badge>
      </motion.div>

        {/* Main grid */}
        <motion.div 
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          {/* Left Column: Summary and Documentation */}
          <div className="space-y-6">
            {/* Summary Section */}
            <motion.div variants={fadeInUp}>
              <Card className="h-[700px]">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold">Summary</h2>
                    <Button variant="ghost" size="sm" onClick={() => setEditingSummary(!editingSummary)}>
                      <Edit2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="h-full">
                  {editingSummary ? (
                    <div className="space-y-4 h-full">
                      <Textarea
                        value={summaryValue}
                        onChange={(e) => setSummaryValue(e.target.value)}
                        rows={20}
                        placeholder="Enter workflow summary...\n\nYou can use markdown formatting:\n• **Bold text**\n• *Italic text*\n• - Bullet points\n• 1. Numbered lists\n\nDescribe what this workflow does, how it works, and any important details for users."
                        className="min-h-[500px] resize-none"
                        disabled={updateWorkflowMutation.isPending}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleSaveSummary} disabled={updateWorkflowMutation.isPending}>
                          <Save className="w-4 h-4 mr-2" /> Save
                        </Button>
                        <Button variant="outline" size="sm" onClick={handleCancelSummaryEdit}>
                          <X className="w-4 h-4 mr-2" /> Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="prose prose-sm max-w-none text-muted-foreground h-full overflow-y-auto">
                      {workflow.summary ? (
                        <ReactMarkdown
                          components={{
                            p: ({node, ...props}) => <p className="mb-4 last:mb-0" {...props} />,
                            ul: ({node, ...props}) => <ul className="list-disc list-inside space-y-1 ml-0" {...props} />,
                            ol: ({node, ...props}) => <ol className="list-decimal list-inside space-y-1 ml-0" {...props} />,
                            strong: ({node, ...props}) => <strong className="font-semibold text-foreground" {...props} />,
                          }}
                        >
                          {workflow.summary}
                        </ReactMarkdown>
                      ) : (
                        <div className="flex flex-col items-center justify-center h-full text-center">
                          <div className="mb-4">
                            <Edit2 className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                          </div>
                          <p className="text-muted-foreground italic mb-2">No summary available</p>
                          <p className="text-sm text-muted-foreground/70">Click the edit button above to add a detailed summary for this workflow</p>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

          </div>

          {/* Right Column: Detailed Performance Metrics */}
          <div className="space-y-6">
            {/* Time Metrics */}
            <motion.div variants={fadeInUp}>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold">Time Metrics</h2>
                    <Button variant="ghost" size="sm" onClick={() => setEditingTimeMetrics(!editingTimeMetrics)}>
                      <Edit2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {editingTimeMetrics ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 gap-4">
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Manual Time (minutes)</label>
                          <Input
                            type="number"
                            value={timeMetricsValues.manual_time_minutes}
                            onChange={(e) => handleTimeMetricsChange('manual_time_minutes', parseFloat(e.target.value) || 0)}
                            min="0"
                            step="0.1"
                            disabled={updateWorkflowMutation.isPending}
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Avg Runtime (ms)</label>
                          <Input
                            type="number"
                            value={timeMetricsValues.avg_execution_time_ms}
                            onChange={(e) => handleTimeMetricsChange('avg_execution_time_ms', parseFloat(e.target.value) || 0)}
                            min="0"
                            step="1"
                            disabled={updateWorkflowMutation.isPending}
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Time Saved Per Run (minutes)</label>
                          <Input
                            type="number"
                            value={timeMetricsValues.time_saved_per_execution_minutes}
                            onChange={(e) => handleTimeMetricsChange('time_saved_per_execution_minutes', parseFloat(e.target.value) || 0)}
                            min="0"
                            step="0.1"
                            disabled={updateWorkflowMutation.isPending}
                            className="bg-blue-50 border-blue-200"
                          />
                          <p className="text-xs text-blue-600 mt-1">✨ Auto-calculated from Manual Time - Runtime</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Total Time Saved (hours)</label>
                          <Input
                            type="number"
                            value={timeMetricsValues.total_time_saved_hours}
                            onChange={(e) => handleTimeMetricsChange('total_time_saved_hours', parseFloat(e.target.value) || 0)}
                            min="0"
                            step="0.1"
                            disabled={updateWorkflowMutation.isPending}
                            className="bg-green-50 border-green-200"
                          />
                          <p className="text-xs text-green-600 mt-1">✨ Auto-calculated from Time Saved Per Run × Total Executions</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleSaveTimeMetrics} disabled={updateWorkflowMutation.isPending}>
                          {updateWorkflowMutation.isPending ? (
                            <div className="w-4 h-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                          ) : (
                            <Save className="w-4 h-4 mr-2" />
                          )}
                          {updateWorkflowMutation.isPending ? 'Saving...' : 'Save'}
                        </Button>
                        <Button variant="outline" size="sm" onClick={handleCancelTimeMetricsEdit}>
                          <X className="w-4 h-4 mr-2" /> Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 gap-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Manual Time:</span>
                        <span className="font-medium">{formatDecimal(metrics.manual_time_minutes)}m</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Avg Runtime:</span>
                        <span className="font-medium">{formatExecutionTime(metrics.avg_execution_time_ms)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Time Saved Per Run:</span>
                        <span className="font-medium text-green-600">{formatDecimal(metrics.time_saved_per_execution_minutes)}m</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Total Time Saved:</span>
                        <span className="font-bold text-green-600">{formatDecimal(metrics.total_time_saved_hours)}h</span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Execution Stats */}
            <motion.div variants={fadeInUp}>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold">Execution Statistics</h2>
                    <Button variant="ghost" size="sm" onClick={() => setEditingExecutionStats(!editingExecutionStats)}>
                      <Edit2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {editingExecutionStats ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 gap-4">
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Total Executions</label>
                          <Input
                            type="number"
                            value={executionStatsValues.total_executions}
                            onChange={(e) => handleExecutionStatsChange('total_executions', parseInt(e.target.value) || 0)}
                            min="0"
                            step="1"
                            disabled={updateWorkflowMutation.isPending}
                          />
                          <p className="text-xs text-muted-foreground mt-1">May auto-update when Successful + Failed change</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Successful Executions</label>
                          <Input
                            type="number"
                            value={executionStatsValues.successful_executions}
                            onChange={(e) => handleExecutionStatsChange('successful_executions', parseInt(e.target.value) || 0)}
                            min="0"
                            step="1"
                            disabled={updateWorkflowMutation.isPending}
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Failed Executions</label>
                          <Input
                            type="number"
                            value={executionStatsValues.failed_executions}
                            onChange={(e) => handleExecutionStatsChange('failed_executions', parseInt(e.target.value) || 0)}
                            min="0"
                            step="1"
                            disabled={updateWorkflowMutation.isPending}
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Success Rate (%)</label>
                          <Input
                            type="number"
                            value={executionStatsValues.success_rate}
                            onChange={(e) => handleExecutionStatsChange('success_rate', parseFloat(e.target.value) || 0)}
                            min="0"
                            max="100"
                            step="0.1"
                            disabled={updateWorkflowMutation.isPending}
                            className="bg-yellow-50 border-yellow-200"
                          />
                          <p className="text-xs text-yellow-600 mt-1">✨ Auto-calculated from Successful ÷ Total Executions</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleSaveExecutionStats} disabled={updateWorkflowMutation.isPending}>
                          {updateWorkflowMutation.isPending ? (
                            <div className="w-4 h-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                          ) : (
                            <Save className="w-4 h-4 mr-2" />
                          )}
                          {updateWorkflowMutation.isPending ? 'Saving...' : 'Save'}
                        </Button>
                        <Button variant="outline" size="sm" onClick={handleCancelExecutionStatsEdit}>
                          <X className="w-4 h-4 mr-2" /> Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div className="p-3 bg-muted/50 rounded-lg">
                          <div className="text-lg font-bold text-blue-600">
                            {metrics.total_executions.toLocaleString()}
                          </div>
                          <div className="text-xs text-muted-foreground">Total</div>
                        </div>
                        <div className="p-3 bg-green-50 rounded-lg">
                          <div className="text-lg font-bold text-green-600">
                            {metrics.successful_executions.toLocaleString()}
                          </div>
                          <div className="text-xs text-green-700">Success</div>
                        </div>
                        <div className="p-3 bg-red-50 rounded-lg">
                          <div className="text-lg font-bold text-red-600">
                            {metrics.failed_executions.toLocaleString()}
                          </div>
                          <div className="text-xs text-red-700">Failed</div>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
                          metrics.success_rate >= 95 ? 'bg-green-100 text-green-800' :
                          metrics.success_rate >= 80 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {formatDecimal(metrics.success_rate)}% Success Rate
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Documentation Section */}
            <motion.div variants={fadeInUp}>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold">Documentation</h2>
                    <Button variant="ghost" size="sm" onClick={() => setEditingDocumentation(!editingDocumentation)}>
                      <Edit2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {editingDocumentation ? (
                    <div className="space-y-4">
                      <Input
                        value={documentationValue}
                        onChange={(e) => setDocumentationValue(e.target.value)}
                        placeholder="https://docs.example.com/workflow..."
                        disabled={updateWorkflowMutation.isPending}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleSaveDocumentation} disabled={updateWorkflowMutation.isPending}>
                          <Save className="w-4 h-4 mr-2" /> Save
                        </Button>
                        <Button variant="outline" size="sm" onClick={handleCancelDocumentationEdit}>
                          <X className="w-4 h-4 mr-2" /> Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      {workflow.documentation_link ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            try {
                              new URL(workflow.documentation_link!)
                              window.open(workflow.documentation_link, '_blank', 'noopener,noreferrer')
                            } catch (error) {
                              console.error('Invalid documentation URL:', workflow.documentation_link)
                              toast.error('Invalid documentation link. Please contact your administrator.')
                            }
                          }}
                          className="w-full justify-start text-left h-auto p-3 bg-purple-50 hover:bg-purple-100 dark:bg-purple-900/20 dark:hover:bg-purple-900/30"
                        >
                          <ExternalLink className="h-4 w-4 mr-2 flex-shrink-0" />
                          <span className="text-sm font-medium text-purple-700 dark:text-purple-300 truncate">
                            {workflow.workflow_name} - Docs
                          </span>
                        </Button>
                      ) : (
                        <p className="text-muted-foreground italic">No documentation link available. Click edit to add one.</p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default WorkflowDetailPage
