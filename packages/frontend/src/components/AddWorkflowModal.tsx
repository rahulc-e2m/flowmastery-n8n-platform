import React from 'react'
import { motion } from 'framer-motion'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, Plus, Zap, Target, BarChart3, Trash2 } from 'lucide-react'
import { AvailableWorkflow, VistaraWorkflow } from '@/services/vistaraWorkflowsApi'
import { VistaraCategory, CreateVistaraCategoryData } from '@/services/vistaraCategoriesApi'
import { CategorySelect } from '@/components/CategorySelect'
import { VistaraIcon } from '@/components/VistaraIcon'

interface AddWorkflowModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  availableWorkflows: AvailableWorkflow[]
  curatedWorkflows: VistaraWorkflow[]
  categories: VistaraCategory[]
  onAddFromExisting: (workflow: AvailableWorkflow, categoryId?: string) => void
  onRemoveFromVistara: (workflow: VistaraWorkflow) => void
  onCreateCategory: (data: CreateVistaraCategoryData) => Promise<VistaraCategory>
  isLoading: boolean
  isRemoving: boolean
  isCreatingCategory?: boolean
}

export function AddWorkflowModal({ 
  open, 
  onOpenChange, 
  availableWorkflows, 
  curatedWorkflows,
  categories,
  onAddFromExisting,
  onRemoveFromVistara,
  onCreateCategory,
  isLoading,
  isRemoving,
  isCreatingCategory = false
}: AddWorkflowModalProps) {
  const [searchQuery, setSearchQuery] = React.useState('')
  const [selectedCategoryId, setSelectedCategoryId] = React.useState<string | undefined>()

  // Create a combined list of all workflows with their curation status
  const allWorkflows = React.useMemo(() => {
    const curatedMap = new Map(curatedWorkflows.filter(w => w.original_workflow_id)
      .map(w => [w.original_workflow_id!, w]))
    
    // Get all unique workflows (both available and curated)
    const workflowMap = new Map()
    
    // Add available workflows
    availableWorkflows.forEach(workflow => {
      workflowMap.set(workflow.id, {
        id: workflow.id,
        name: workflow.name,
        description: workflow.description,
        tags: workflow.tags,
        isCurated: false,
        vistaraWorkflow: null
      })
    })
    
    // Mark curated workflows
    curatedWorkflows.forEach(vistaraWorkflow => {
      if (vistaraWorkflow.original_workflow_id) {
        const existingWorkflow = workflowMap.get(vistaraWorkflow.original_workflow_id)
        if (existingWorkflow) {
          // Mark as curated
          existingWorkflow.isCurated = true
          existingWorkflow.vistaraWorkflow = vistaraWorkflow
        } else {
          // Add workflow that's curated but not in available list
          workflowMap.set(vistaraWorkflow.original_workflow_id, {
            id: vistaraWorkflow.original_workflow_id,
            name: vistaraWorkflow.workflow_name,
            description: null,
            tags: [],
            isCurated: true,
            vistaraWorkflow: vistaraWorkflow
          })
        }
      }
    })
    
    return Array.from(workflowMap.values())
  }, [availableWorkflows, curatedWorkflows])

  const filteredWorkflows = allWorkflows.filter(wf =>
    wf.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] border-0 shadow-2xl bg-gradient-to-br from-white via-primary/5 to-primary/10 overflow-hidden">
        <DialogHeader className="relative pb-8">
          {/* Animated gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-primary-600/10" />
          <motion.div 
            className="absolute -top-10 -right-10 w-32 h-32 bg-primary/10 rounded-full blur-3xl"
            animate={{ scale: [1, 1.3, 1], opacity: [0.3, 0.5, 0.3] }}
            transition={{ duration: 5, repeat: Infinity }}
          />
          
          <DialogTitle className="relative">
            <motion.h2 
              className="text-3xl font-bold bg-gradient-to-r from-primary via-primary-600 to-primary bg-clip-text text-transparent"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              Manage Workflows
            </motion.h2>
          </DialogTitle>
          <p className="text-muted-foreground mt-3 text-base leading-relaxed">
            Curate workflows from your collection for Vistara analytics, or manage existing curated workflows.
          </p>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Category Selection Section */}
          <div>
            <CategorySelect
              categories={categories}
              selectedCategoryId={selectedCategoryId}
              onCategorySelect={setSelectedCategoryId}
              onCreateCategory={onCreateCategory}
              isCreatingCategory={isCreatingCategory}
              placeholder="Select category for new workflows"
            />
            <p className="text-xs text-muted-foreground mt-2">
              This category will be applied to workflows you curate below.
            </p>
          </div>
          
          {/* Available Workflows Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gradient">Workflow Management</h3>
                <p className="text-sm text-muted-foreground mt-1">Curate new workflows or remove existing ones from Vistara</p>
              </div>
              <Badge variant="outline" className="px-3 py-1">
                {filteredWorkflows.length} Available
              </Badge>
            </div>
            
            {/* Search */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Search available workflows..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 border-primary/20 focus:border-primary"
              />
            </div>

            {/* Workflows List */}
            <div className="h-80 border border-border/50 rounded-lg overflow-y-auto">
              {filteredWorkflows.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-8">
                  <motion.div 
                    className="w-20 h-20 rounded-full bg-gradient-to-br from-primary/20 to-primary-600/20 flex items-center justify-center mb-4"
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <Search className="w-10 h-10 text-primary/50" />
                  </motion.div>
                  <p className="text-center text-lg font-medium text-foreground/70">
                    {searchQuery ? 'No workflows match your search' : 'All workflows curated!'}
                  </p>
                  {!searchQuery && (
                    <p className="text-sm text-muted-foreground mt-2">Every workflow from your collection is already in Vistara</p>
                  )}
                </div>
              ) : (
                <div className="p-4 space-y-3">
                  {filteredWorkflows.map((workflow) => (
                    <div 
                      key={workflow.id}
                      className={`flex items-center justify-between p-3 rounded-lg border transition-all duration-200 ${
                        workflow.isCurated 
                          ? 'border-green-200 bg-green-50/50 hover:border-green-300' 
                          : 'border-border/50 hover:border-primary/30 hover:shadow-md'
                      }`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <div className={`w-2 h-2 rounded-full ${workflow.isCurated ? 'bg-green-500' : 'bg-primary'}`} />
                          <span className="font-medium text-foreground">{workflow.name}</span>
                          {workflow.isCurated && (
                            <Badge className="bg-gradient-to-r from-green-100 to-green-200 text-green-800 border-0 text-xs font-medium">
                              ✓ Curated
                            </Badge>
                          )}
                        </div>
                        
                        {workflow.description && (
                          <p className="text-sm text-muted-foreground mb-2">{workflow.description}</p>
                        )}
                        
                        {workflow.tags && workflow.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {workflow.tags.slice(0, 3).map((tag) => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                            {workflow.tags.length > 3 && (
                              <Badge variant="secondary" className="text-xs">
                                +{workflow.tags.length - 3} more
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                      
                      {workflow.isCurated ? (
                        <Button 
                          size="sm"
                          variant="outline"
                          onClick={() => workflow.vistaraWorkflow && onRemoveFromVistara(workflow.vistaraWorkflow)}
                          disabled={isRemoving}
                          className="border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300 ml-4"
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          {isRemoving ? 'Removing...' : 'Remove'}
                        </Button>
                      ) : (
                        <Button 
                          size="sm"
                          onClick={() => onAddFromExisting({ id: workflow.id, name: workflow.name, description: workflow.description || undefined, tags: workflow.tags }, selectedCategoryId)}
                          disabled={isLoading}
                          className="bg-gradient-to-r from-primary to-primary-600 hover:from-primary-600 hover:to-primary-700 ml-4"
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Add to Library
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button 
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-primary/20 text-primary hover:bg-primary/5"
          >
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
