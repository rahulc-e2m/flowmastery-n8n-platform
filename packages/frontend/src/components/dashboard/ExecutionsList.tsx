import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  Activity,
  Filter,
  RefreshCw,
  Calendar,
  Timer
} from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { formatDistanceToNow, format } from 'date-fns'

interface Execution {
  n8n_execution_id: string
  status: string
  mode?: string
  workflow_name: string
  workflow_id: string
  started_at?: string
  finished_at?: string
  execution_time_ms?: number
  execution_time_seconds?: number
  is_production: boolean
}

interface ExecutionsListProps {
  executions: Execution[]
  isLoading?: boolean
  onRefresh?: () => void
  title?: string
  description?: string
  onSelectionChange?: (selectedIds: string[]) => void
}

export function ExecutionsList({ 
  executions, 
  isLoading = false, 
  onRefresh,
  title = "Recent Executions",
  description = "Latest workflow execution results",
  onSelectionChange
}: ExecutionsListProps) {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [modeFilter, setModeFilter] = useState<string>('all')
  const [selectedExecutions, setSelectedExecutions] = useState<Set<string>>(new Set())

  // Filter executions
  const filteredExecutions = executions.filter(execution => {
    const matchesStatus = statusFilter === 'all' || execution.status.toLowerCase() === statusFilter.toLowerCase()
    const matchesMode = modeFilter === 'all' || 
      (modeFilter === 'production' && execution.is_production) ||
      (modeFilter === 'test' && !execution.is_production)
    
    return matchesStatus && matchesMode
  })

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error':
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'running':
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />
      default:
        return <Activity className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">Success</Badge>
      case 'error':
      case 'failed':
        return <Badge variant="destructive">Error</Badge>
      case 'running':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200">Running</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = new Set(filteredExecutions.map(e => e.n8n_execution_id))
      setSelectedExecutions(allIds)
      onSelectionChange?.(Array.from(allIds))
    } else {
      setSelectedExecutions(new Set())
      onSelectionChange?.([])
    }
  }

  const handleSelectExecution = (executionId: string, checked: boolean) => {
    const newSelected = new Set(selectedExecutions)
    if (checked) {
      newSelected.add(executionId)
    } else {
      newSelected.delete(executionId)
    }
    setSelectedExecutions(newSelected)
    onSelectionChange?.(Array.from(newSelected))
  }

  const isAllSelected = filteredExecutions.length > 0 && selectedExecutions.size === filteredExecutions.length
  const isIndeterminate = selectedExecutions.size > 0 && selectedExecutions.size < filteredExecutions.length

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="animate-pulse">
            <div className="h-6 bg-muted rounded w-48 mb-2" />
            <div className="h-4 bg-muted rounded w-64" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-muted rounded" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl font-semibold">{title}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          </div>
          <div className="flex items-center space-x-2">
            {selectedExecutions.size > 0 && (
              <Badge variant="default" className="px-3 py-1">
                {selectedExecutions.size} Selected
              </Badge>
            )}
            <Badge variant="outline" className="px-3 py-1">
              {executions.length} Total
            </Badge>
            {onRefresh && (
              <Button variant="outline" size="sm" onClick={onRefresh}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
        
        {/* Filters and Selection */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center space-x-4">
            {filteredExecutions.length > 0 && (
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={isAllSelected}
                  onCheckedChange={handleSelectAll}
                  aria-label="Select all executions"
                  className={isIndeterminate ? "data-[state=checked]:bg-primary/50" : ""}
                />
                <span className="text-sm text-muted-foreground">Select All</span>
              </div>
            )}
          </div>
          <div className="flex items-center space-x-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="error">Error</SelectItem>
              <SelectItem value="running">Running</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={modeFilter} onValueChange={setModeFilter}>
            <SelectTrigger className="w-40">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Modes</SelectItem>
              <SelectItem value="production">Production</SelectItem>
              <SelectItem value="test">Test</SelectItem>
            </SelectContent>
          </Select>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-3">
          <AnimatePresence>
            {filteredExecutions.map((execution, index) => (
              <motion.div
                key={execution.n8n_execution_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.05 }}
                className={`group p-4 rounded-lg border border-border/50 hover:border-border transition-all duration-200 hover:bg-accent/30 ${
                  selectedExecutions.has(execution.n8n_execution_id) ? 'bg-accent/50 border-primary/50' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <Checkbox
                      checked={selectedExecutions.has(execution.n8n_execution_id)}
                      onCheckedChange={(checked) => 
                        handleSelectExecution(execution.n8n_execution_id, checked as boolean)
                      }
                      aria-label={`Select execution ${execution.n8n_execution_id}`}
                    />
                    <div className="flex items-center space-x-4">
                      <motion.div 
                        className="w-10 h-10 bg-gradient-to-br from-primary/20 to-accent/20 rounded-lg flex items-center justify-center"
                        whileHover={{ scale: 1.1, rotate: 5 }}
                      >
                        {getStatusIcon(execution.status)}
                      </motion.div>
                    
                    <div>
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-medium text-foreground group-hover:text-primary transition-colors">
                          {execution.workflow_name}
                        </h4>
                        {execution.is_production && (
                          <Badge variant="outline" className="text-xs">PROD</Badge>
                        )}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span className="flex items-center space-x-1">
                          <Activity className="w-3 h-3" />
                          <span>ID: {execution.n8n_execution_id}</span>
                        </span>
                        {execution.started_at && (
                          <span className="flex items-center space-x-1">
                            <Calendar className="w-3 h-3" />
                            <span>{format(new Date(execution.started_at), 'MMM dd, HH:mm')}</span>
                          </span>
                        )}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {execution.execution_time_seconds && (
                      <div className="text-right">
                        <div className="flex items-center space-x-1 text-sm font-medium text-foreground">
                          <Timer className="w-3 h-3" />
                          <span>{execution.execution_time_seconds.toFixed(2)}s</span>
                        </div>
                        <p className="text-xs text-muted-foreground">Duration</p>
                      </div>
                    )}
                    
                    <div className="text-right">
                      {getStatusBadge(execution.status)}
                      <p className="text-xs text-muted-foreground mt-1">
                        {execution.started_at ? 
                          formatDistanceToNow(new Date(execution.started_at), { addSuffix: true }) : 
                          'Unknown time'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {filteredExecutions.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No executions found matching your criteria</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}