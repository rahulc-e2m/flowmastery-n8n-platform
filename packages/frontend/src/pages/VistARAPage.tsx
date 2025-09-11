import React from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Search, 
  Filter, 
  ChevronUp, 
  ChevronDown, 
  Clock, 
  Zap, 
  Target, 
  BarChart3,
  X,
  Plus,
  RefreshCw
} from 'lucide-react'
import { VistaraIcon } from '@/components/VistaraIcon'
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations'
import { VistaraWorkflowsApi, type VistaraWorkflow, type CreateVistaraWorkflowData, type AvailableWorkflow } from '@/services/vistaraWorkflowsApi'
import { VistaraCategoriesApi, type VistaraCategory, type CreateVistaraCategoryData } from '@/services/vistaraCategoriesApi'
import { AddWorkflowModal } from '@/components/AddWorkflowModal'
import { toast } from 'sonner'

type SortField = 'workflow_name' | 'category' | 'total_executions' | 'success_rate' | 'manual_time' | 'execution_time' | 'total_time_saved'
type SortOrder = 'asc' | 'desc'

const formatTime = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const mins = Math.round((minutes % 60) * 100) / 100 // Round to 2 decimal places
  if (hours > 0) {
    return `${hours}h ${mins.toFixed(mins % 1 === 0 ? 0 : 2)}m`
  }
  return `${mins.toFixed(mins % 1 === 0 ? 0 : 2)}m`
}

const formatExecutionTime = (ms: number) => {
  if (ms < 1000) return `${ms.toFixed(ms % 1 === 0 ? 0 : 2)}ms`
  if (ms < 60000) {
    const seconds = ms / 1000
    return `${seconds.toFixed(seconds % 1 === 0 ? 0 : 2)}s`
  }
  const minutes = ms / 60000
  return `${minutes.toFixed(minutes % 1 === 0 ? 0 : 2)}m`
}

const getCategoryColor = (color: string) => {
  return `text-white border-0`
}

const getCategoryBgColor = (color: string) => {
  return color
}

export function VistARAPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [sortField, setSortField] = React.useState<SortField>('total_executions')
  const [sortOrder, setSortOrder] = React.useState<SortOrder>('desc')
  const [categoryFilter, setCategoryFilter] = React.useState('all')
  const [successRateFilter, setSuccessRateFilter] = React.useState('all')
  const [executionFilter, setExecutionFilter] = React.useState('all')
  const [searchQuery, setSearchQuery] = React.useState('')
  const [showAddWorkflow, setShowAddWorkflow] = React.useState(false)

  // Fetch vistara workflows
  const { data: vistaraWorkflows = [], isLoading: isLoadingWorkflows } = useQuery({
    queryKey: ['vistara-workflows'],
    queryFn: () => VistaraWorkflowsApi.getVistaraWorkflows(),
  })

  // Fetch categories
  const { data: categories = [] } = useQuery({
    queryKey: ['vistara-categories'],
    queryFn: () => VistaraCategoriesApi.getCategories(),
  })

  // Fetch available workflows when add modal is open
  const { data: availableWorkflows = [], isLoading: isLoadingAvailableWorkflows, error: availableWorkflowsError } = useQuery({
    queryKey: ['available-workflows'],
    queryFn: async () => {
      console.log('React Query: Starting getAvailableWorkflows API call')
      try {
        const result = await VistaraWorkflowsApi.getAvailableWorkflows()
        console.log('React Query: API call successful, result:', result)
        return result
      } catch (error) {
        console.error('React Query: API call failed:', error)
        throw error
      }
    },
    enabled: showAddWorkflow,
  })

  // Debug: Log available workflows
  React.useEffect(() => {
    if (showAddWorkflow) {
      console.log('Available workflows:', availableWorkflows)
      console.log('Available workflows count:', availableWorkflows.length)
      console.log('Is loading available workflows:', isLoadingAvailableWorkflows)
      console.log('Available workflows error:', availableWorkflowsError)
    }
  }, [showAddWorkflow, availableWorkflows, isLoadingAvailableWorkflows, availableWorkflowsError])

  // Mutations

  const createWorkflowMutation = useMutation({
    mutationFn: (data: CreateVistaraWorkflowData) => VistaraWorkflowsApi.createVistaraWorkflow(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vistara-workflows'] })
      queryClient.invalidateQueries({ queryKey: ['available-workflows'] })
      setShowAddWorkflow(false)
      toast.success('Workflow curated! You can now customize its summary and documentation.')
    },
    onError: (error: any) => {
      toast.error('Failed to add workflow')
      console.error('Create error:', error)
    },
  })

  const deleteWorkflowMutation = useMutation({
    mutationFn: (id: string) => VistaraWorkflowsApi.deleteVistaraWorkflow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vistara-workflows'] })
      queryClient.invalidateQueries({ queryKey: ['available-workflows'] })
      toast.success('Workflow removed from Vistara successfully')
    },
    onError: (error: any) => {
      toast.error('Failed to remove workflow from Vistara')
      console.error('Delete error:', error)
    },
  })

  const syncMetricsMutation = useMutation({
    mutationFn: (workflowId?: string) => VistaraWorkflowsApi.syncVistaraMetrics(workflowId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['vistara-workflows'] })
      if (data.sync_type === 'bulk') {
        toast.success(`Synced ${data.results.synced_successfully} workflows successfully`)
      } else {
        toast.success('Workflow metrics synced successfully')
      }
    },
    onError: (error: any) => {
      toast.error('Failed to sync metrics')
      console.error('Sync error:', error)
    },
  })

  const createCategoryMutation = useMutation({
    mutationFn: (data: CreateVistaraCategoryData) => VistaraCategoriesApi.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vistara-categories'] })
      toast.success('Category created successfully')
    },
    onError: (error: any) => {
      toast.error('Failed to create category')
      console.error('Create category error:', error)
    },
  })


  // Handlers
  const handleWorkflowClick = (workflow: VistaraWorkflow) => {
    navigate(`/vistara/workflow/${workflow.id}`)
  }


  const handleAddWorkflow = (availableWorkflow: AvailableWorkflow, categoryId?: string) => {
    createWorkflowMutation.mutate({
      workflow_name: availableWorkflow.name,
      original_workflow_id: availableWorkflow.id,
      summary: availableWorkflow.description || '',
      category_id: categoryId,
    })
  }

  const handleCreateCategory = async (data: CreateVistaraCategoryData): Promise<VistaraCategory> => {
    return createCategoryMutation.mutateAsync(data)
  }

  const handleDeleteWorkflow = (workflow: VistaraWorkflow) => {
    if (workflow) {
      deleteWorkflowMutation.mutate(workflow.id)
    }
  }

  // Sorting and filtering
  const sortedAndFilteredWorkflows = React.useMemo(() => {
    let filtered = vistaraWorkflows.filter(wf => {
      // Search filter
      if (searchQuery && !wf.workflow_name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      
      // Category filter
      if (categoryFilter !== 'all') {
        if (!wf.category || wf.category.id !== categoryFilter) {
          return false
        }
      }
      
      // Success rate filter
      if (successRateFilter !== 'all') {
        const rate = wf.metrics.success_rate
        if (successRateFilter === 'excellent' && rate < 95) return false
        if (successRateFilter === 'good' && (rate < 80 || rate >= 95)) return false
        if (successRateFilter === 'needs-improvement' && rate >= 80) return false
      }
      
      // Execution filter
      if (executionFilter !== 'all') {
        const executions = wf.metrics.total_executions
        if (executionFilter === 'high' && executions < 50) return false
        if (executionFilter === 'medium' && (executions < 10 || executions >= 50)) return false
        if (executionFilter === 'low' && executions >= 10) return false
      }
      
      return true
    })

    // Sorting
    filtered.sort((a, b) => {
      let aVal: any, bVal: any
      
      switch (sortField) {
        case 'workflow_name':
          aVal = a.workflow_name.toLowerCase()
          bVal = b.workflow_name.toLowerCase()
          break
        case 'category':
          aVal = a.category?.name || ''
          bVal = b.category?.name || ''
          break
        case 'total_executions':
          aVal = a.metrics.total_executions
          bVal = b.metrics.total_executions
          break
        case 'success_rate':
          aVal = a.metrics.success_rate
          bVal = b.metrics.success_rate
          break
        case 'manual_time':
          aVal = a.metrics.manual_time_minutes
          bVal = b.metrics.manual_time_minutes
          break
        case 'execution_time':
          aVal = a.metrics.avg_execution_time_ms
          bVal = b.metrics.avg_execution_time_ms
          break
        case 'total_time_saved':
          aVal = a.metrics.total_time_saved_hours || 0
          bVal = b.metrics.total_time_saved_hours || 0
          break
        default:
          return 0
      }
      
      if (typeof aVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
      
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
    })

    return filtered
  }, [vistaraWorkflows, sortField, sortOrder, categoryFilter, successRateFilter, executionFilter, searchQuery])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('desc')
    }
  }

  const clearFilters = () => {
    setSearchQuery('')
    setCategoryFilter('all')
    setSuccessRateFilter('all')
    setExecutionFilter('all')
  }

  const SortButton = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center gap-1 hover:text-primary transition-colors group"
    >
      {children}
      <div className="flex flex-col">
        <ChevronUp 
          className={`w-3 h-3 ${sortField === field && sortOrder === 'asc' ? 'text-primary' : 'text-gray-400'} group-hover:text-primary`}
        />
        <ChevronDown 
          className={`w-3 h-3 -mt-1 ${sortField === field && sortOrder === 'desc' ? 'text-primary' : 'text-gray-400'} group-hover:text-primary`}
        />
      </div>
    </button>
  )

  return (
    <motion.div 
      className="p-6 space-y-6"
      variants={staggerContainer}
      initial="initial"
      animate="animate"
    >
      {/* Header with Vistara Branding */}
      <motion.div variants={fadeInUp} className="flex items-center justify-between">
        <div>
          <motion.h1 
            className="text-4xl font-bold bg-gradient-to-r from-primary via-primary-600 to-primary bg-clip-text text-transparent cursor-pointer inline-block hover:scale-105 transition-transform"
            onClick={() => setShowAddWorkflow(true)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            title="Click to curate workflows"
          >
            Vistara Insights
          </motion.h1>
          <p className="text-muted-foreground mt-2">Smarter Workflows. Clearer Insights.</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            onClick={() => syncMetricsMutation.mutate()}
            disabled={syncMetricsMutation.isPending}
            variant="outline"
            size="sm"
            className="border-primary/20 text-primary hover:bg-primary/5"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${syncMetricsMutation.isPending ? 'animate-spin' : ''}`} />
            {syncMetricsMutation.isPending ? 'Syncing...' : 'Sync Metrics'}
          </Button>
        </div>
      </motion.div>

      {/* Filters Section */}
      <motion.div variants={staggerItem}>
        <Card className="border-border/50 shadow-sm">
          <CardContent className="p-6">
            <div className="flex flex-wrap items-center gap-4">
              {/* Search */}
              <div className="relative min-w-64">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Search workflows..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 border-border/50 focus:border-primary"
                />
              </div>

              {/* Category Filter */}
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-48 border-border/50">
                  <Filter className="w-4 h-4 mr-2 text-muted-foreground" />
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(cat => (
                    <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Success Rate Filter */}
              <Select value={successRateFilter} onValueChange={setSuccessRateFilter}>
                <SelectTrigger className="w-48 border-border/50">
                  <Target className="w-4 h-4 mr-2 text-muted-foreground" />
                  <SelectValue placeholder="Success Rate" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Success Rates</SelectItem>
                  <SelectItem value="excellent">Excellent (≥95%)</SelectItem>
                  <SelectItem value="good">Good (80-94%)</SelectItem>
                  <SelectItem value="needs-improvement">Needs Improvement (&lt;80%)</SelectItem>
                </SelectContent>
              </Select>

              {/* Execution Volume Filter */}
              <Select value={executionFilter} onValueChange={setExecutionFilter}>
                <SelectTrigger className="w-48 border-border/50">
                  <BarChart3 className="w-4 h-4 mr-2 text-muted-foreground" />
                  <SelectValue placeholder="Volume" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">No. of Executions</SelectItem>
                  <SelectItem value="high">High (≥50)</SelectItem>
                  <SelectItem value="medium">Medium (10-49)</SelectItem>
                  <SelectItem value="low">Low (&lt;10)</SelectItem>
                </SelectContent>
              </Select>

              {/* Clear Filters */}
              <Button 
                variant="outline" 
                size="sm"
                onClick={clearFilters}
                className="border-border/50 text-muted-foreground hover:bg-muted/50"
              >
                <X className="w-4 h-4 mr-1" />
                Clear All
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Results Summary */}
      <motion.div variants={staggerItem} className="text-sm text-muted-foreground">
        Showing {sortedAndFilteredWorkflows.length} of {vistaraWorkflows.length} workflows
      </motion.div>

      {/* Main Data Table */}
      <motion.div variants={staggerItem}>
        <Card className="border-border/50 shadow-sm overflow-hidden">
          <Table>
            <TableHeader className="bg-primary/5">
              <TableRow>
                <TableHead className="font-semibold text-foreground">
                  <SortButton field="workflow_name">Workflow Name</SortButton>
                </TableHead>
                <TableHead className="font-semibold text-foreground">
                  <SortButton field="category">Category</SortButton>
                </TableHead>
                <TableHead className="font-semibold text-foreground text-right">
                  <SortButton field="total_executions">No. of Executions</SortButton>
                </TableHead>
                <TableHead className="font-semibold text-foreground text-right">
                  <SortButton field="success_rate">Success Rate</SortButton>
                </TableHead>
                <TableHead className="font-semibold text-foreground text-right">
                  <SortButton field="manual_time">Manual Time Taken</SortButton>
                </TableHead>
                <TableHead className="font-semibold text-foreground text-right">
                  <SortButton field="execution_time">Workflow Execution Time</SortButton>
                </TableHead>
                <TableHead className="font-semibold text-foreground text-right">
                  <SortButton field="total_time_saved">Total Time Saved</SortButton>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedAndFilteredWorkflows.map((wf, index) => (
                <motion.tr
                  key={wf.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-primary/5 transition-colors cursor-pointer"
                  onClick={() => handleWorkflowClick(wf)}
                >
                  <TableCell className="font-semibold text-foreground">
                    <div className="flex items-center space-x-2">
                      <VistaraIcon className="text-primary" width={16} height={16} />
                      <span>{wf.workflow_name}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {wf.category ? (
                      <Badge 
                        className={`${getCategoryColor(wf.category.color)} border-0`} 
                        style={{ backgroundColor: wf.category.color }}
                      >
                        {wf.category.name}
                      </Badge>
                    ) : (
                      <span className="text-gray-400 italic">No category</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      wf.metrics.total_executions >= 50 ? 'bg-green-100 text-green-800' :
                      wf.metrics.total_executions >= 10 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {wf.metrics.total_executions.toLocaleString()}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      wf.metrics.success_rate >= 95 ? 'bg-green-100 text-green-800' :
                      wf.metrics.success_rate >= 80 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {wf.metrics.success_rate.toFixed(wf.metrics.success_rate % 1 === 0 ? 0 : 2)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end space-x-1">
                      <Clock className="w-4 h-4 text-orange-500" />
                      <span className="font-medium text-orange-700">
                        {formatTime(wf.metrics.manual_time_minutes)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end space-x-1">
                      <Clock className="w-4 h-4 text-blue-500" />
                      <span className="font-medium text-blue-700">
                        {formatExecutionTime(wf.metrics.avg_execution_time_ms)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="px-3 py-1 rounded-full text-sm font-bold bg-purple-100 text-purple-800 border border-purple-200">
                      {wf.metrics.total_time_saved_hours ? `${wf.metrics.total_time_saved_hours.toFixed(wf.metrics.total_time_saved_hours % 1 === 0 ? 0 : 2)}h` : '0h'}
                    </span>
                  </TableCell>
                </motion.tr>
              ))}
              
              {sortedAndFilteredWorkflows.length === 0 && !isLoadingWorkflows && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-12">
                    <div className="flex flex-col items-center space-y-4">
                      <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center">
                        <BarChart3 className="w-8 h-8 text-purple-500" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900 mb-1">No workflows found</h3>
                        <p className="text-gray-500 text-center">
                          {vistaraWorkflows.length === 0 ? 
                            'No workflows have been curated for Vistara yet. Select workflows from your collection to create customizable analytics entries.' : 
                            'Try adjusting your filters'
                          }
                        </p>
                      </div>
                      {vistaraWorkflows.length === 0 && (
                        <Button 
                          onClick={() => setShowAddWorkflow(true)}
                          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Curate Your First Workflow
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Card>
      </motion.div>

      {/* Add Workflow Modal */}
      <AddWorkflowModal 
        open={showAddWorkflow} 
        onOpenChange={setShowAddWorkflow}
        availableWorkflows={availableWorkflows}
        curatedWorkflows={vistaraWorkflows}
        categories={categories}
        onAddFromExisting={handleAddWorkflow}
        onRemoveFromVistara={handleDeleteWorkflow}
        onCreateCategory={handleCreateCategory}
        isLoading={createWorkflowMutation.isPending}
        isRemoving={deleteWorkflowMutation.isPending}
        isCreatingCategory={createCategoryMutation.isPending}
      />

    </motion.div>
  )
}

export default VistARAPage
