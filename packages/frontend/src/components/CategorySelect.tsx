import React from 'react'
import { motion } from 'framer-motion'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Plus, Palette, Tag, X } from 'lucide-react'
import { VistaraCategory, CreateVistaraCategoryData } from '@/services/vistaraCategoriesApi'
import { VistaraIcon } from '@/components/VistaraIcon'

interface CategorySelectProps {
  categories: VistaraCategory[]
  selectedCategoryId?: string
  onCategorySelect: (categoryId: string | undefined) => void
  onCreateCategory: (data: CreateVistaraCategoryData) => Promise<VistaraCategory>
  isCreatingCategory?: boolean
  placeholder?: string
}

const defaultColors = [
  '#6B46C1', '#7C3AED', '#8B5CF6', '#A855F7', '#C084FC',
  '#EC4899', '#F97316', '#EAB308', '#22C55E', '#06B6D4',
  '#3B82F6', '#6366F1', '#8B5CF6', '#EF4444', '#F59E0B'
]

export function CategorySelect({
  categories,
  selectedCategoryId,
  onCategorySelect,
  onCreateCategory,
  isCreatingCategory = false,
  placeholder = "Select category"
}: CategorySelectProps) {
  const [showCreateDialog, setShowCreateDialog] = React.useState(false)
  const [newCategoryName, setNewCategoryName] = React.useState('')
  const [newCategoryDescription, setNewCategoryDescription] = React.useState('')
  const [newCategoryColor, setNewCategoryColor] = React.useState(defaultColors[0])
  const [newCategoryIcon, setNewCategoryIcon] = React.useState('')

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) return

    try {
      const newCategory = await onCreateCategory({
        name: newCategoryName.trim(),
        description: newCategoryDescription.trim() || undefined,
        color: newCategoryColor,
        icon_name: newCategoryIcon.trim() || undefined
      })
      
      // Select the newly created category
      onCategorySelect(newCategory.id)
      
      // Reset form and close dialog
      setNewCategoryName('')
      setNewCategoryDescription('')
      setNewCategoryColor(defaultColors[0])
      setNewCategoryIcon('')
      setShowCreateDialog(false)
    } catch (error) {
      console.error('Failed to create category:', error)
    }
  }

  const selectedCategory = categories.find(cat => cat.id === selectedCategoryId)

  return (
    <div className="space-y-2">
      <Label htmlFor="category">Category (optional)</Label>
      
      <div className="flex gap-2">
        <Select 
          value={selectedCategoryId || "none"} 
          onValueChange={(value) => onCategorySelect(value === "none" ? undefined : value)}
        >
          <SelectTrigger className="flex-1">
            <SelectValue placeholder={placeholder}>
              {selectedCategory ? (
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full border border-white/20" 
                    style={{ backgroundColor: selectedCategory.color }}
                  />
                  <span>{selectedCategory.name}</span>
                </div>
              ) : (
                placeholder
              )}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full border-2 border-dashed border-gray-300" />
                <span className="text-gray-500">No category</span>
              </div>
            </SelectItem>
            {categories.map((category) => (
              <SelectItem key={category.id} value={category.id}>
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full border border-white/20" 
                    style={{ backgroundColor: category.color }}
                  />
                  <span>{category.name}</span>
                  {category.description && (
                    <span className="text-xs text-gray-500 ml-1">
                      ({category.description})
                    </span>
                  )}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setShowCreateDialog(true)}
          className="shrink-0 border-primary/20 text-primary hover:bg-primary/5"
        >
          <Plus className="w-4 h-4" />
        </Button>
      </div>

      {selectedCategory && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2"
        >
          <Badge 
            className="text-white border-0"
            style={{ backgroundColor: selectedCategory.color }}
          >
            <Tag className="w-3 h-3 mr-1" />
            {selectedCategory.name}
          </Badge>
          {selectedCategory.description && (
            <span className="text-xs text-muted-foreground">
              {selectedCategory.description}
            </span>
          )}
        </motion.div>
      )}

      {/* Create Category Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-primary-600 rounded-lg flex items-center justify-center shadow-lg">
                <VistaraIcon className="text-white" width={16} height={16} />
              </div>
              <span className="text-gradient">Create New Category</span>
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="category-name">Category Name *</Label>
              <Input
                id="category-name"
                placeholder="Enter category name"
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                className="mt-1"
                maxLength={100}
              />
            </div>
            
            <div>
              <Label htmlFor="category-description">Description (optional)</Label>
              <Textarea
                id="category-description"
                placeholder="Brief description of this category"
                value={newCategoryDescription}
                onChange={(e) => setNewCategoryDescription(e.target.value)}
                className="mt-1 resize-none"
                rows={2}
                maxLength={500}
              />
            </div>
            
            <div>
              <Label>Color</Label>
              <div className="mt-2 flex flex-wrap gap-2">
                {defaultColors.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setNewCategoryColor(color)}
                    className={`w-8 h-8 rounded-full border-2 transition-all ${
                      newCategoryColor === color 
                        ? 'border-gray-400 scale-110' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <div className="mt-2 flex items-center gap-2">
                <Input
                  type="text"
                  placeholder="#6B46C1"
                  value={newCategoryColor}
                  onChange={(e) => setNewCategoryColor(e.target.value)}
                  className="text-sm font-mono"
                  maxLength={7}
                />
                <div 
                  className="w-6 h-6 rounded border border-gray-200"
                  style={{ backgroundColor: newCategoryColor }}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="category-icon">Icon Name (optional)</Label>
              <Input
                id="category-icon"
                placeholder="e.g., workflow, automation, data"
                value={newCategoryIcon}
                onChange={(e) => setNewCategoryIcon(e.target.value)}
                className="mt-1"
                maxLength={50}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Icon identifier for future use
              </p>
            </div>
          </div>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
              disabled={isCreatingCategory}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateCategory}
              disabled={!newCategoryName.trim() || isCreatingCategory}
              className="bg-gradient-to-r from-primary to-primary-600 hover:from-primary-600 hover:to-primary-700"
            >
              {isCreatingCategory ? 'Creating...' : 'Create Category'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
