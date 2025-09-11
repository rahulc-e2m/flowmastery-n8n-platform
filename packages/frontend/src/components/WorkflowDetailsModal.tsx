import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { 
  Edit, 
  Save, 
  X, 
  ExternalLink, 
  FileText, 
  Zap, 
  Target, 
  BarChart3, 
  Clock,
  Calendar,
  TrendingUp
} from 'lucide-react'
import { VistaraWorkflow } from '@/services/vistaraWorkflowsApi'
import { VistaraIcon } from '@/components/VistaraIcon'

interface WorkflowDetailsModalProps {
  workflow: VistaraWorkflow | null
  open: boolean
  onOpenChange: (open: boolean) => void
  editingSummary: boolean
  editingDocumentation: boolean
  editingWorkflowName: boolean
  editingMetrics: boolean
  editingExecutionStats: boolean
  summaryValue: string
  documentationValue: string
  workflowNameValue: string
  metricsValues: {
    manualTimeMinutes: number
    avgExecutionTimeMs: number
  }
  executionStatsValues: {
    totalExecutions: number
    successfulExecutions: number
    failedExecutions: number
  }
  onEditSummary: () => void
  onEditDocumentation: () => void
  onEditWorkflowName: () => void
  onEditMetrics: () => void
  onEditExecutionStats: () => void
  onSaveSummary: () => void
  onSaveDocumentation: () => void
  onSaveWorkflowName: () => void
  onSaveMetrics: () => void
  onSaveExecutionStats: () => void
  onSummaryChange: (value: string) => void
  onDocumentationChange: (value: string) => void
  onWorkflowNameChange: (value: string) => void
  onMetricsChange: (field: string, value: number) => void
  onExecutionStatsChange: (field: string, value: number) => void
  onCancelEdit: () => void
  isUpdating: boolean
}

const formatTime = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const mins = Math.round((minutes % 60) * 100) / 100 // Round to 2 decimal places
  if (hours > 0) {
    return `${hours}h ${formatDecimal(mins)}m`
  }
  return `${formatDecimal(mins)}m`
}

const formatExecutionTime = (ms: number) => {
  if (ms < 1000) return `${formatDecimal(ms)}ms`
  if (ms < 60000) {
    const seconds = ms / 1000
    return `${formatDecimal(seconds)}s`
  }
  const minutes = ms / 60000
  return `${formatDecimal(minutes)}m`
}

const formatDate = (dateString?: string) => {
  if (!dateString) return 'Never'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Utility to format numbers with max 2 decimal places, but hide decimals if whole number
const formatDecimal = (value: number, maxDecimals: number = 2): string => {
  // If it's a whole number, return without decimals
  if (value % 1 === 0) {
    return value.toString()
  }
  // Otherwise, round to maxDecimals places
  return value.toFixed(Math.min(maxDecimals, 2))
}

// Utility functions for time parsing
const parseTimeToMinutes = (timeString: string): number => {
  const match = timeString.match(/(\d+(?:\.\d+)?)([hm])/i)
  if (!match) return 0
  const value = parseFloat(match[1])
  const unit = match[2].toLowerCase()
  return unit === 'h' ? value * 60 : value
}

const parseExecutionTimeToMs = (timeString: string): number => {
  if (timeString.includes('ms')) {
    return parseFloat(timeString)
  } else if (timeString.includes('s')) {
    return parseFloat(timeString) * 1000
  } else if (timeString.includes('m')) {
    return parseFloat(timeString) * 60000
  }
  return parseFloat(timeString)
}

export function WorkflowDetailsModal({ 
  workflow, 
  open, 
  onOpenChange,
  editingSummary,
  editingDocumentation,
  editingWorkflowName,
  editingMetrics,
  editingExecutionStats,
  summaryValue,
  documentationValue,
  workflowNameValue,
  metricsValues,
  executionStatsValues,
  onEditSummary,
  onEditDocumentation,
  onEditWorkflowName,
  onEditMetrics,
  onEditExecutionStats,
  onSaveSummary,
  onSaveDocumentation,
  onSaveWorkflowName,
  onSaveMetrics,
  onSaveExecutionStats,
  onSummaryChange,
  onDocumentationChange,
  onWorkflowNameChange,
  onMetricsChange,
  onExecutionStatsChange,
  onCancelEdit,
  isUpdating
}: WorkflowDetailsModalProps) {
  if (!workflow) return null

  const metrics = workflow.metrics
  
  // Calculate dynamic time saved per execution
  const calculateTimeSavedPerRun = (manualMinutes: number, executionMs: number): number => {
    const executionMinutes = executionMs / 60000 // Convert ms to minutes
    const savedMinutes = manualMinutes - executionMinutes
    return Math.max(0, savedMinutes) // Ensure it's never negative
  }
  
  // Use either the editing values or actual metrics values
  const currentManualTime = editingMetrics ? metricsValues.manualTimeMinutes : metrics.manual_time_minutes
  const currentExecutionTime = editingMetrics ? metricsValues.avgExecutionTimeMs : metrics.avg_execution_time_ms
  const currentTotalTimeSaved = editingMetrics ? metricsValues.totalTimeSavedHours : metrics.total_time_saved_hours
  const dynamicTimeSavedPerRun = calculateTimeSavedPerRun(currentManualTime, currentExecutionTime)
  
  // Calculate what the total time saved should be based on current metrics
  const calculatedTotalTimeSaved = (dynamicTimeSavedPerRun * metrics.total_executions) / 60

  // Animation variants
  const backdropVariants = {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  }

  const modalVariants = {
    initial: { opacity: 0, scale: 0.95, y: 20 },
    animate: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.95, y: 20 }
  }

  const contentVariants = {
    initial: { opacity: 0, y: 30 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 30 }
  }

  const staggerChildren = {
    initial: { opacity: 0 },
    animate: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const childVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 }
  }

  return (
    <AnimatePresence>
      {open && (
        <Dialog open={open} onOpenChange={() => {}}> {/* Disable default close to use only custom button */}
          <motion.div
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
          >
            <DialogContent className="max-w-7xl max-h-[95vh] overflow-hidden bg-white border-2 border-border/30 shadow-2xl rounded-2xl p-0 backdrop-blur-sm">
              
              <motion.div 
                variants={contentVariants}
                initial="initial"
                animate="animate"
                transition={{ delay: 0.1 }}
                className="relative"
              >
                {/* Custom Close Button */}
                <motion.button
                  onClick={() => onOpenChange(false)}
                  className="absolute top-4 right-4 z-10 w-8 h-8 rounded-full bg-white/90 hover:bg-white border border-border/20 hover:border-border/40 flex items-center justify-center text-muted-foreground hover:text-foreground transition-all duration-200 shadow-md hover:shadow-lg backdrop-blur-sm"
                  whileHover={{ scale: 1.1, rotate: 90 }}
                  whileTap={{ scale: 0.9 }}
                  title="Close"
                >
                  <X className="w-4 h-4" />
                </motion.button>

                <DialogHeader className="relative overflow-hidden">
                  {/* Beautiful gradient background */}
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-primary-600/5 to-transparent" />
                  <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-primary/5 to-primary-600/10" />
                  <motion.div 
                    className="absolute -top-20 -right-20 w-40 h-40 bg-primary/10 rounded-full blur-3xl"
                    animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
                    transition={{ duration: 4, repeat: Infinity }}
                  />
                  
                  <DialogTitle className="relative px-6 py-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        {editingWorkflowName ? (
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            <Input
                              value={workflowNameValue}
                              onChange={(e) => onWorkflowNameChange(e.target.value)}
                              className="text-xl font-bold border-2 border-primary/20 focus:border-primary/40 bg-white/90 shadow-sm"
                              disabled={isUpdating}
                              autoFocus
                            />
                            <div className="flex space-x-2 shrink-0">
                              <Button
                                size="sm"
                                onClick={onSaveWorkflowName}
                                disabled={isUpdating}
                                className="bg-gradient-to-r from-primary to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white shadow-md px-4"
                              >
                                <Save className="w-4 h-4 mr-2" />
                                Save
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={onCancelEdit}
                                className="border-border/50 text-muted-foreground hover:bg-muted/50 shadow-md px-4"
                              >
                                <X className="w-4 h-4 mr-2" />
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            <motion.h2 
                              className="text-2xl font-bold bg-gradient-to-r from-primary via-primary-600 to-primary bg-clip-text text-transparent cursor-pointer hover:opacity-90 transition-all truncate"
                              onDoubleClick={onEditWorkflowName}
                              whileHover={{ scale: 1.01 }}
                              whileTap={{ scale: 0.99 }}
                              title="Double-click to edit"
                            >
                              {workflow.workflow_name}
                            </motion.h2>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center space-x-3 flex-wrap">
                        {workflow.is_featured && (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.3 }}
                          >
                            <Badge className="bg-gradient-to-r from-amber-100 to-amber-200 text-amber-800 border-amber-300 px-3 py-1 text-sm font-medium">
                              ⭐ Featured
                            </Badge>
                          </motion.div>
                        )}
                        {workflow.category && (
                          <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.4 }}
                          >
                            <Badge 
                              className="text-white border-0 px-3 py-1 text-sm font-medium shadow-sm" 
                              style={{ backgroundColor: workflow.category.color }}
                            >
                              {workflow.category.name}
                            </Badge>
                          </motion.div>
                        )}
                      </div>
                    </div>
                  </DialogTitle>
                </DialogHeader>
              </motion.div>

              <motion.div 
                variants={staggerChildren}
                initial="initial"
                animate="animate"
                className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 h-[calc(100vh-160px)] overflow-hidden"
              >
                {/* Left Column - Summary and Documentation */}
                <div className="lg:col-span-1 flex flex-col gap-6 h-full overflow-y-auto pr-2 -mr-2">
                  {/* Summary Section */}
                  <motion.div variants={childVariants} className="flex-1">
                    <Card className="group relative border-2 border-transparent hover:border-primary/20 shadow-lg bg-white hover:shadow-xl transition-all duration-300 overflow-hidden h-full rounded-2xl">
                      <CardHeader className="relative pb-3 pt-4 bg-gray-50/60">
                        <div className="flex items-center justify-between">
                          <CardTitle className="flex items-center space-x-3 text-lg font-bold text-gray-800">
                            <FileText className="w-6 h-6 text-primary" />
                            <span onDoubleClick={onEditSummary} className="cursor-pointer" title="Double-click to edit">Summary</span>
                          </CardTitle>
                        {!editingSummary ? null : (
                          <motion.div 
                            className="flex space-x-2"
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ type: "spring", stiffness: 300, damping: 25 }}
                          >
                            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                              <Button
                                size="sm"
                                onClick={onSaveSummary}
                                disabled={isUpdating}
                                className="bg-primary hover:bg-primary-600 text-white shadow-md rounded-lg"
                              >
                                <Save className="w-4 h-4 mr-2" />
                                Save
                              </Button>
                            </motion.div>
                            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={onCancelEdit}
                                className="border-gray-300 text-gray-600 hover:bg-gray-100 shadow-md rounded-lg"
                              >
                                <X className="w-4 h-4 mr-2" />
                                Cancel
                              </Button>
                            </motion.div>
                          </motion.div>
                        )}
                        </div>
                      </CardHeader>
                      <CardContent className="p-5">
                        {editingSummary ? (
                          <div className="space-y-4">
                            <Textarea
                              value={summaryValue}
                              onChange={(e) => onSummaryChange(e.target.value)}
                              placeholder="Enter a detailed summary using Markdown formatting..."
                              className="min-h-48 border-gray-300 focus:border-primary bg-white text-base leading-relaxed font-mono rounded-lg"
                              disabled={isUpdating}
                            />
                            <p className="text-xs text-gray-500">
                              💡 You can use Markdown: **bold**, *italic*, ## headings, - lists, [links](url), etc.
                            </p>
                          </div>
                        ) : (
                          <div className="text-gray-800 leading-relaxed text-base">
                            {workflow.summary ? (
                              <div className="prose prose-base max-w-none prose-headings:text-gray-800 prose-headings:font-semibold prose-p:text-gray-700 prose-strong:text-gray-800 prose-em:text-gray-600 prose-a:text-primary hover:prose-a:text-primary-600 prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-1 prose-code:rounded-md prose-code:text-sm prose-ul:text-gray-700 prose-ol:text-gray-700 prose-li:text-gray-700">
                                <ReactMarkdown 
                                  remarkPlugins={[remarkGfm]}
                                  components={{
                                    h1: ({node, ...props}) => <h1 className="text-2xl font-bold text-gray-900 mb-4 mt-5 first:mt-0" {...props} />,
                                    h2: ({node, ...props}) => <h2 className="text-xl font-semibold text-gray-800 mb-3 mt-4 first:mt-0" {...props} />,
                                    h3: ({node, ...props}) => <h3 className="text-lg font-medium text-gray-800 mb-2 mt-3 first:mt-0" {...props} />,
                                    p: ({node, ...props}) => <p className="mb-4 last:mb-0 leading-relaxed" {...props} />,
                                    ul: ({node, ...props}) => <ul className="list-disc list-inside mb-4 space-y-1.5 ml-4" {...props} />,
                                    ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-4 space-y-1.5 ml-4" {...props} />,
                                    li: ({node, ...props}) => <li className="leading-relaxed" {...props} />,
                                    strong: ({node, ...props}) => <strong className="font-semibold text-gray-900" {...props} />,
                                    em: ({node, ...props}) => <em className="italic text-gray-600" {...props} />,
                                    a: ({node, ...props}) => <a className="text-primary hover:text-primary-600 hover:underline transition-colors" target="_blank" rel="noopener noreferrer" {...props} />,
                                    code: ({node, className, ...props}) => {
                                      const isInline = !className
                                      return isInline ? (
                                        <code className="bg-gray-100 px-2 py-1 rounded-md text-sm font-mono border border-gray-200" {...props} />
                                      ) : (
                                        <code className="block bg-gray-800 text-white p-4 rounded-lg text-sm font-mono border border-gray-700 leading-relaxed overflow-x-auto" {...props} />
                                      )
                                    },
                                    blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-primary/40 pl-5 py-2 bg-gray-50 rounded-r-lg italic my-4" {...props} />
                                  }}
                                >
                                  {workflow.summary}
                                </ReactMarkdown>
                              </div>
                            ) : (
                              <div className="text-center text-gray-500 bg-gray-50 p-8 rounded-lg border-2 border-dashed border-gray-300">
                                <FileText className="w-10 h-10 mx-auto mb-4 text-gray-400" />
                                <p className="font-semibold text-lg mb-2">No summary provided yet</p>
                                <p className="text-sm">Click the title to add a description using Markdown.</p>
                              </div>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>

                  {/* Documentation Link Section */}
                  <motion.div variants={childVariants}>
                    <Card className="group relative border-2 border-transparent hover:border-primary/20 shadow-lg bg-white hover:shadow-xl transition-all duration-300 overflow-hidden rounded-2xl">
                      <CardHeader className="relative pb-3 pt-4 bg-gray-50/60">
                        <div className="flex items-center justify-between">
                          <CardTitle className="flex items-center space-x-3 text-lg font-bold text-gray-800">
                            <ExternalLink className="w-6 h-6 text-primary" />
                            <span onDoubleClick={onEditDocumentation} className="cursor-pointer" title="Double-click to edit">Documentation</span>
                          </CardTitle>
                          {!editingDocumentation ? null : (
                            <motion.div 
                              className="flex space-x-2"
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ type: "spring", stiffness: 300, damping: 25 }}
                            >
                              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                <Button
                                  size="sm"
                                  onClick={onSaveDocumentation}
                                  disabled={isUpdating}
                                  className="bg-primary hover:bg-primary-600 text-white shadow-md rounded-lg"
                                >
                                  <Save className="w-4 h-4 mr-2" />
                                  Save
                                </Button>
                              </motion.div>
                              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={onCancelEdit}
                                  className="border-gray-300 text-gray-600 hover:bg-gray-100 shadow-md rounded-lg"
                                >
                                  <X className="w-4 h-4 mr-2" />
                                  Cancel
                                </Button>
                              </motion.div>
                            </motion.div>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent className="p-5">
                        {editingDocumentation ? (
                          <Input
                            value={documentationValue}
                            onChange={(e) => onDocumentationChange(e.target.value)}
                            placeholder="https://docs.example.com/workflow..."
                            className="border-gray-300 focus:border-primary bg-white text-base rounded-lg"
                            disabled={isUpdating}
                          />
                        ) : (
                          <div className="text-base">
                            {workflow.documentation_link ? (
                              <a
                                href={workflow.documentation_link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center justify-between space-x-3 text-primary hover:text-primary-600 bg-primary/5 hover:bg-primary/10 border border-primary/20 p-4 rounded-lg transition-all duration-200"
                              >
                                <span className="font-semibold truncate">{workflow.documentation_link}</span>
                                <ExternalLink className="w-5 h-5 shrink-0" />
                              </a>
                            ) : (
                              <div className="text-center text-gray-500 bg-gray-50 p-6 rounded-lg border-2 border-dashed border-gray-300">
                                No documentation link. Click the title to add a reference.
                              </div>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                </div>

                {/* Right Column - Metrics */}
                <div className="lg:col-span-1 flex flex-col gap-6 h-full overflow-y-auto pl-2 -ml-2">
                  {/* Time Metrics Card */}
                  <motion.div variants={childVariants}>
                    <Card className="group relative border-2 border-transparent hover:border-primary/20 shadow-lg bg-white hover:shadow-xl transition-all duration-300 overflow-hidden rounded-2xl">
                      <CardHeader className="relative pb-3 pt-4 bg-gray-50/60">
                        <div className="flex items-center justify-between">
                          <CardTitle className="flex items-center space-x-3 text-lg font-bold text-gray-800">
                            <Clock className="w-6 h-6 text-primary" />
                            <span onDoubleClick={onEditMetrics} className="cursor-pointer" title="Double-click to edit">Time Metrics</span>
                          </CardTitle>
                            {!editingMetrics ? null : (
                              <motion.div 
                                className="flex space-x-2"
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                              >
                                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                  <Button
                                    size="sm"
                                    onClick={onSaveMetrics}
                                    disabled={isUpdating}
                                    className="bg-primary hover:bg-primary-600 text-white shadow-md rounded-lg"
                                  >
                                    <Save className="w-4 h-4 mr-2" />
                                    Save
                                  </Button>
                                </motion.div>
                                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={onCancelEdit}
                                    className="border-gray-300 text-gray-600 hover:bg-gray-100 shadow-md rounded-lg"
                                  >
                                    <X className="w-4 h-4 mr-2" />
                                    Cancel
                                  </Button>
                                </motion.div>
                              </motion.div>
                            )}
                          </div>
                      </CardHeader>
                      <CardContent className="p-5 space-y-4">
                          {editingMetrics ? (
                            <div className="space-y-5">
                              {/* Inputs */}
                              <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                  <label className="text-sm font-medium text-gray-700">Manual Time (min)</label>
                                  <Input
                                    type="number"
                                    value={metricsValues.manualTimeMinutes}
                                    onChange={(e) => onMetricsChange('manualTimeMinutes', parseFloat(e.target.value) || 0)}
                                    className="border-gray-300 focus:border-primary bg-white rounded-lg"
                                    disabled={isUpdating}
                                    min="0"
                                    step="0.1"
                                  />
                                </div>
                                <div className="space-y-2">
                                  <label className="text-sm font-medium text-gray-700">Avg Runtime (ms)</label>
                                  <Input
                                    type="number"
                                    value={metricsValues.avgExecutionTimeMs}
                                    onChange={(e) => onMetricsChange('avgExecutionTimeMs', parseFloat(e.target.value) || 0)}
                                    className="border-gray-300 focus:border-primary bg-white rounded-lg"
                                    disabled={isUpdating}
                                    min="0"
                                    step="1"
                                  />
                                </div>
                              </div>
                              {/* Previews */}
                              <div className="space-y-3 pt-4 border-t border-gray-200">
                                <h4 className="text-sm font-semibold text-gray-800 mb-2">📊 Calculated Previews:</h4>
                                <div className="bg-purple-50 p-3.5 rounded-lg border border-purple-200">
                                  <div className="text-sm font-semibold text-purple-800">Time Saved Per Run</div>
                                  <div className="text-2xl font-bold text-purple-900 mt-1">{formatTime(dynamicTimeSavedPerRun)}</div>
                                  <div className="text-xs text-purple-700 mt-1">
                                    = {formatTime(currentManualTime)} - {formatExecutionTime(currentExecutionTime)}
                                  </div>
                                </div>
                                <div className="bg-green-50 p-3.5 rounded-lg border border-green-200">
                                  <div className="text-sm font-semibold text-green-800">Total Time Saved</div>
                                  <div className="text-2xl font-bold text-green-900 mt-1">{formatDecimal(calculatedTotalTimeSaved)}h</div>
                                  <div className="text-xs text-green-700 mt-1">
                                    = {formatTime(dynamicTimeSavedPerRun)} × {metrics.total_executions.toLocaleString()} runs
                                  </div>
                                </div>
                              </div>
                            </div>
                        ) : (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div className="text-center p-4 rounded-xl bg-blue-50 border border-blue-200">
                                <div className="text-3xl font-bold text-blue-800">{formatExecutionTime(metrics.avg_execution_time_ms)}</div>
                                <div className="text-sm text-blue-700 font-semibold mt-1">Avg Runtime</div>
                              </div>
                              <div className="text-center p-4 rounded-xl bg-orange-50 border border-orange-200">
                                <div className="text-3xl font-bold text-orange-800">{formatTime(metrics.manual_time_minutes)}</div>
                                <div className="text-sm text-orange-700 font-semibold mt-1">Manual Time</div>
                              </div>
                            </div>
                            <div className="text-center p-4 rounded-xl bg-green-50 border border-green-200">
                              <div className="text-4xl font-bold text-green-800">{formatDecimal(calculatedTotalTimeSaved)}h</div>
                              <div className="text-sm text-green-700 font-semibold mt-1">Total Time Saved</div>
                              <div className="text-xs text-green-600 mt-1">
                                based on {metrics.total_executions.toLocaleString()} runs
                              </div>
                            </div>
                            <div className="text-center bg-purple-50 p-3 rounded-xl border border-purple-200">
                              <div className="text-xl font-bold text-purple-800">{formatTime(dynamicTimeSavedPerRun)}</div>
                              <div className="text-sm text-purple-700 font-semibold">Saved Per Run</div>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                  
                  {/* Execution Stats Card */}
                  <motion.div variants={childVariants}>
                    <Card className="group relative border-2 border-transparent hover:border-primary/20 shadow-lg bg-white hover:shadow-xl transition-all duration-300 overflow-hidden rounded-2xl">
                      <CardHeader className="relative pb-3 pt-4 bg-gray-50/60">
                        <div className="flex items-center justify-between">
                          <CardTitle className="flex items-center space-x-3 text-lg font-bold text-gray-800">
                            <BarChart3 className="w-6 h-6 text-primary" />
                            <span onDoubleClick={onEditExecutionStats} className="cursor-pointer" title="Double-click to edit">Execution Stats</span>
                          </CardTitle>
                            {!editingExecutionStats ? null : (
                              <motion.div 
                                className="flex space-x-2"
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                              >
                                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                  <Button
                                    size="sm"
                                    onClick={onSaveExecutionStats}
                                    disabled={isUpdating}
                                    className="bg-primary hover:bg-primary-600 text-white shadow-md rounded-lg"
                                  >
                                    <Save className="w-4 h-4 mr-2" />
                                    Save
                                  </Button>
                                </motion.div>
                                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={onCancelEdit}
                                    className="border-gray-300 text-gray-600 hover:bg-gray-100 shadow-md rounded-lg"
                                  >
                                    <X className="w-4 h-4 mr-2" />
                                    Cancel
                                  </Button>
                                </motion.div>
                              </motion.div>
                            )}
                          </div>
                      </CardHeader>
                      <CardContent className="p-5 space-y-4">
                          {editingExecutionStats ? (
                            <div className="space-y-5">
                              {/* Inputs */}
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="space-y-2">
                                  <label className="text-sm font-medium text-gray-700">Total Runs</label>
                                  <Input
                                    type="number"
                                    value={executionStatsValues.totalExecutions}
                                    onChange={(e) => onExecutionStatsChange('totalExecutions', parseInt(e.target.value) || 0)}
                                    className="border-gray-300 focus:border-primary bg-white rounded-lg"
                                    disabled={isUpdating}
                                    min="0"
                                    step="1"
                                  />
                                </div>
                                <div className="space-y-2">
                                  <label className="text-sm font-medium text-gray-700">Successful</label>
                                  <Input
                                    type="number"
                                    value={executionStatsValues.successfulExecutions}
                                    onChange={(e) => onExecutionStatsChange('successfulExecutions', parseInt(e.target.value) || 0)}
                                    className="border-gray-300 focus:border-primary bg-white rounded-lg"
                                    disabled={isUpdating}
                                    min="0"
                                    step="1"
                                  />
                                </div>
                                <div className="space-y-2">
                                  <label className="text-sm font-medium text-gray-700">Failed</label>
                                  <Input
                                    type="number"
                                    value={executionStatsValues.failedExecutions}
                                    onChange={(e) => onExecutionStatsChange('failedExecutions', parseInt(e.target.value) || 0)}
                                    className="border-gray-300 focus:border-primary bg-white rounded-lg"
                                    disabled={isUpdating}
                                    min="0"
                                    step="1"
                                  />
                                </div>
                              </div>
                              {/* Previews */}
                              <div className="space-y-3 pt-4 border-t border-gray-200">
                                <h4 className="text-sm font-semibold text-gray-800 mb-2">📊 Calculated Previews:</h4>
                                <div className="bg-blue-50 p-3.5 rounded-lg border border-blue-200">
                                  <div className="text-sm font-semibold text-blue-800">Success Rate</div>
                                  <div className="text-2xl font-bold text-blue-900 mt-1">
                                    {executionStatsValues.totalExecutions > 0 
                                      ? formatDecimal((executionStatsValues.successfulExecutions / executionStatsValues.totalExecutions) * 100)
                                      : 0}%
                                  </div>
                                </div>
                                <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                                  <div className="font-semibold text-yellow-800">Check Total</div>
                                  <div className="text-sm text-yellow-900 mt-1">
                                    {executionStatsValues.successfulExecutions} + {executionStatsValues.failedExecutions} = {executionStatsValues.successfulExecutions + executionStatsValues.failedExecutions}
                                    (Should be {executionStatsValues.totalExecutions})
                                    {executionStatsValues.successfulExecutions + executionStatsValues.failedExecutions !== executionStatsValues.totalExecutions && 
                                      <span className="text-red-600 font-bold ml-2">⚠️ Mismatch!</span>
                                    }
                                  </div>
                                </div>
                              </div>
                            </div>
                        ) : (
                          <div className="space-y-4">
                            <div className="text-center p-4 rounded-xl bg-primary/10 border border-primary/20">
                              <div className="text-4xl font-bold text-primary">{metrics.total_executions.toLocaleString()}</div>
                              <div className="text-sm text-primary/80 font-semibold mt-1">Total Runs</div>
                            </div>
                            <div className="text-center p-4 rounded-xl bg-green-50 border border-green-200">
                              <div className="text-4xl font-bold text-green-800">{formatDecimal(metrics.success_rate)}%</div>
                              <div className="text-sm text-green-700 font-semibold mt-1">Success Rate</div>
                              <div className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-bold ${
                                metrics.success_rate >= 95 ? 'bg-green-200 text-green-800' :
                                metrics.success_rate >= 80 ? 'bg-yellow-200 text-yellow-800' :
                                'bg-red-200 text-red-800'
                              }`}>
                                {metrics.success_rate >= 95 ? 'EXCELLENT' :
                                 metrics.success_rate >= 80 ? 'GOOD' : 'NEEDS WORK'}
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-center">
                              <div className="bg-green-100/60 p-3 rounded-xl border border-green-200">
                                <div className="text-2xl font-bold text-green-800">{metrics.successful_executions.toLocaleString()}</div>
                                <div className="text-sm text-green-700 font-semibold">Success</div>
                              </div>
                              <div className="bg-red-100/60 p-3 rounded-xl border border-red-200">
                                <div className="text-2xl font-bold text-red-800">{metrics.failed_executions.toLocaleString()}</div>
                                <div className="text-sm text-red-700 font-semibold">Failed</div>
                              </div>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                </div>
              </motion.div>
            </DialogContent>
          </motion.div>
        </Dialog>
      )}
    </AnimatePresence>
  )
}
