import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Activity, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Timer,
  TrendingUp,
  Filter,
  Search,
  ArrowUpDown,
  Play,
  Pause
} from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatDistanceToNow } from 'date-fns'

interface WorkflowMetric {
  workflow_name: string
  workflow_id: string
  active: boolean
  total_executions: number
  successful_executions: number
  failed_executions: number
  success_rate: number
  avg_execution_time_seconds: number
  last_execution?: string
  time_saved_per_execution_minutes?: number
  time_saved_hours?: number
}

interface WorkflowMetricsTableProps {
  workflows: WorkflowMetric[]
  isLoading?: boolean
  title?: string
  description?: string
  onSelectionChange?: (selectedIds: string[]) => void
}

type SortField = 'name' | 'executions' | 'success_rate' | 'avg_time' | 'last_execution'
type SortDirection = 'asc' | 'desc'

export function WorkflowMetricsTable({ 
  workflows, 
  isLoading = false, 
  title = "Workflow Performance",
  description = "Detailed metrics for each workflow",
  onSelectionChange
}: WorkflowMetricsTableProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [sortField, setSortField] = useState<SortField>('executions')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [selectedWorkflows, setSelectedWorkflows] = useState<Set<string>>(new Set())

  // Filter workflows
  const filteredWorkflows = workflows.filter(workflow => {
    const matchesSearch = workflow.workflow_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'active' && workflow.active) ||
      (statusFilter === 'inactive' && !workflow.active)
    
    return matchesSearch && matchesStatus
  })

  // Sort workflows
  const sortedWorkflows = [...filteredWorkflows].sort((a, b) => {
    let aValue: any, bValue: any
    
    switch (sortField) {
      case 'name':
        aValue = a.workflow_name.toLowerCase()
        bValue = b.workflow_name.toLowerCase()
        break
      case 'executions':
        aValue = a.total_executions
        bValue = b.total_executions
        break
      case 'success_rate':
        aValue = a.success_rate
        bValue = b.success_rate
        break
      case 'avg_time':
        aValue = a.avg_execution_time_seconds
        bValue = b.avg_execution_time_seconds
        break
      case 'last_execution':
        aValue = a.last_execution ? new Date(a.last_execution).getTime() : 0
        bValue = b.last_execution ? new Date(b.last_execution).getTime() : 0
        break
      default:
        aValue = a.total_executions
        bValue = b.total_executions
    }

    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  })

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return <ArrowUpDown className="w-4 h-4 opacity-50" />
    return <ArrowUpDown className={`w-4 h-4 ${sortDirection === 'asc' ? 'rotate-180' : ''}`} />
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = new Set(sortedWorkflows.map(w => w.workflow_id))
      setSelectedWorkflows(allIds)
      onSelectionChange?.(Array.from(allIds))
    } else {
      setSelectedWorkflows(new Set())
      onSelectionChange?.([])
    }
  }

  const handleSelectWorkflow = (workflowId: string, checked: boolean) => {
    const newSelected = new Set(selectedWorkflows)
    if (checked) {
      newSelected.add(workflowId)
    } else {
      newSelected.delete(workflowId)
    }
    setSelectedWorkflows(newSelected)
    onSelectionChange?.(Array.from(newSelected))
  }

  const isAllSelected = sortedWorkflows.length > 0 && selectedWorkflows.size === sortedWorkflows.length
  const isIndeterminate = selectedWorkflows.size > 0 && selectedWorkflows.size < sortedWorkflows.length

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
                <div className="h-12 bg-muted rounded" />
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
            {selectedWorkflows.size > 0 && (
              <Badge variant="default" className="px-3 py-1">
                {selectedWorkflows.size} Selected
              </Badge>
            )}
            <Badge variant="outline" className="px-3 py-1">
              {workflows.length} Total
            </Badge>
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex items-center space-x-4 mt-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search workflows..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active Only</SelectItem>
              <SelectItem value="inactive">Inactive Only</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={isAllSelected}
                    onCheckedChange={handleSelectAll}
                    aria-label="Select all workflows"
                    className={isIndeterminate ? "data-[state=checked]:bg-primary/50" : ""}
                  />
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => handleSort('name')}
                >
                  <div className="flex items-center space-x-2">
                    <span>Workflow</span>
                    {getSortIcon('name')}
                  </div>
                </TableHead>
                <TableHead className="text-center">Status</TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-muted/50 transition-colors text-center"
                  onClick={() => handleSort('executions')}
                >
                  <div className="flex items-center justify-center space-x-2">
                    <span>Executions</span>
                    {getSortIcon('executions')}
                  </div>
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-muted/50 transition-colors text-center"
                  onClick={() => handleSort('success_rate')}
                >
                  <div className="flex items-center justify-center space-x-2">
                    <span>Success Rate</span>
                    {getSortIcon('success_rate')}
                  </div>
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-muted/50 transition-colors text-center"
                  onClick={() => handleSort('avg_time')}
                >
                  <div className="flex items-center justify-center space-x-2">
                    <span>Avg Time</span>
                    {getSortIcon('avg_time')}
                  </div>
                </TableHead>
                <TableHead className="text-center">
                  <div className="flex items-center justify-center space-x-2">
                    <span>Time Saved</span>
                  </div>
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-muted/50 transition-colors text-center"
                  onClick={() => handleSort('last_execution')}
                >
                  <div className="flex items-center justify-center space-x-2">
                    <span>Last Run</span>
                    {getSortIcon('last_execution')}
                  </div>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <AnimatePresence>
                {sortedWorkflows.map((workflow, index) => (
                  <motion.tr
                    key={workflow.workflow_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ delay: index * 0.05 }}
                    className={`group hover:bg-muted/30 transition-colors ${
                      selectedWorkflows.has(workflow.workflow_id) ? 'bg-muted/50' : ''
                    }`}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selectedWorkflows.has(workflow.workflow_id)}
                        onCheckedChange={(checked) => 
                          handleSelectWorkflow(workflow.workflow_id, checked as boolean)
                        }
                        aria-label={`Select ${workflow.workflow_name}`}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        <motion.div 
                          className="w-8 h-8 bg-gradient-to-br from-primary/20 to-accent/20 rounded-lg flex items-center justify-center"
                          whileHover={{ scale: 1.1, rotate: 5 }}
                        >
                          <Activity className="w-4 h-4 text-primary" />
                        </motion.div>
                        <div>
                          <p className="font-medium text-foreground group-hover:text-primary transition-colors">
                            {workflow.workflow_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            ID: {workflow.workflow_id}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center">
                        {workflow.active ? (
                          <Badge variant="default" className="flex items-center space-x-1">
                            <Play className="w-3 h-3" />
                            <span>Active</span>
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="flex items-center space-x-1">
                            <Pause className="w-3 h-3" />
                            <span>Inactive</span>
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell className="text-center">
                      <div className="space-y-1">
                        <p className="font-semibold text-foreground">
                          {workflow.total_executions.toLocaleString()}
                        </p>
                        <div className="flex items-center justify-center space-x-2 text-xs">
                          <span className="flex items-center text-green-600">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            {workflow.successful_executions}
                          </span>
                          <span className="flex items-center text-red-600">
                            <XCircle className="w-3 h-3 mr-1" />
                            {workflow.failed_executions}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    
                    <TableCell className="text-center">
                      <Badge 
                        variant={
                          workflow.success_rate >= 90 ? 'default' : 
                          workflow.success_rate >= 70 ? 'secondary' : 'destructive'
                        }
                        className="font-medium"
                      >
                        {workflow.success_rate.toFixed(1)}%
                      </Badge>
                    </TableCell>
                    
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center space-x-1">
                        <Clock className="w-3 h-3 text-muted-foreground" />
                        <span className="font-medium">
                          {workflow.avg_execution_time_seconds.toFixed(2)}s
                        </span>
                      </div>
                    </TableCell>
                    
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center space-x-1">
                        <Timer className="w-3 h-3 text-orange-600" />
                        <span className="font-medium text-orange-600">
                          {workflow.time_saved_hours ? `${workflow.time_saved_hours}h` : '0h'}
                        </span>
                      </div>
                    </TableCell>
                    
                    <TableCell className="text-center">
                      <p className="text-sm text-muted-foreground">
                        {workflow.last_execution ? 
                          formatDistanceToNow(new Date(workflow.last_execution), { addSuffix: true }) : 
                          'Never'
                        }
                      </p>
                    </TableCell>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </TableBody>
          </Table>
          
          {sortedWorkflows.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No workflows found matching your criteria</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}