import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Plus,
  MessageCircle,
  Trash2,
  ExternalLink,
  Building2,
  Globe,
  Edit,
  Search
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'
import { ClientApi } from '@/services/clientApi'
import { ChatbotApi, type Chatbot, type CreateChatbotData } from '@/services/chatbotApi'

export function ChatbotListPage() {
  const { isAdmin, user } = useAuth()
  const queryClient = useQueryClient()
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [editingChatbot, setEditingChatbot] = useState<Chatbot | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [formData, setFormData] = useState<CreateChatbotData>({
    name: '',
    description: '',
    webhook_url: '',
    client_id: ''
  })

  // Fetch chatbots
  const { data: chatbotsData, isLoading } = useQuery({
    queryKey: ['chatbots'],
    queryFn: isAdmin ? ChatbotApi.getAll : ChatbotApi.getMine
  })

  const chatbots = chatbotsData?.chatbots || []

  // Fetch clients for selection
  const { data: clients = [] } = useQuery({
    queryKey: ['clients'],
    queryFn: ClientApi.getClients,
    enabled: isAdmin
  })

  // Create chatbot mutation
  const createMutation = useMutation({
    mutationFn: ChatbotApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] })
      setShowCreateDialog(false)
      resetForm()
      toast.success('Chatbot created successfully')
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to create chatbot')
    }
  })

  // Update chatbot mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateChatbotData> }) =>
      ChatbotApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] })
      setEditingChatbot(null)
      resetForm()
      toast.success('Chatbot updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update chatbot')
    }
  })

  // Delete chatbot mutation
  const deleteMutation = useMutation({
    mutationFn: ChatbotApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] })
      toast.success('Chatbot deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to delete chatbot')
    }
  })

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      webhook_url: '',
      client_id: ''
    })
  }

  const handleCreate = () => {
    if (!formData.name || !formData.webhook_url) {
      toast.error('Please fill in all required fields')
      return
    }
    
    // For non-admin users, use their client_id automatically
    const dataToSubmit = {
      ...formData,
      client_id: isAdmin ? formData.client_id : user?.client_id || ''
    }
    
    if (!dataToSubmit.client_id) {
      toast.error('Client ID is required')
      return
    }
    
    createMutation.mutate(dataToSubmit)
  }

  const handleUpdate = () => {
    if (!editingChatbot || !formData.name || !formData.webhook_url) {
      toast.error('Please fill in all required fields')
      return
    }
    
    // For non-admin users, use their client_id automatically
    const dataToSubmit = {
      ...formData,
      client_id: isAdmin ? formData.client_id : user?.client_id || editingChatbot.client_id
    }
    
    if (!dataToSubmit.client_id) {
      toast.error('Client ID is required')
      return
    }
    
    updateMutation.mutate({ id: editingChatbot.id, data: dataToSubmit })
  }

  const handleEdit = (chatbot: Chatbot) => {
    setEditingChatbot(chatbot)
    setFormData({
      name: chatbot.name,
      description: chatbot.description || '',
      webhook_url: chatbot.webhook_url,
      client_id: chatbot.client_id
    })
  }

  const handleDelete = (chatbot: Chatbot) => {
    if (confirm(`Are you sure you want to delete "${chatbot.name}"?`)) {
      deleteMutation.mutate(chatbot.id)
    }
  }

  const filteredChatbots = chatbots.filter(chatbot =>
    chatbot.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    chatbot.client_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading chatbots...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <motion.div 
            className="p-3 rounded-xl bg-blue-500 text-white"
            whileHover={{ scale: 1.05 }}
          >
            <MessageCircle className="w-6 h-6" />
          </motion.div>
          <div>
            <h1 className="text-3xl font-bold">Chatbot Management</h1>
            <p className="text-muted-foreground">Manage your AI chatbot instances</p>
          </div>
        </div>
        <Button
          onClick={() => {
            setShowCreateDialog(true)
            // Pre-fill client_id for non-admin users
            if (!isAdmin && user?.client_id) {
              setFormData(prev => ({ ...prev, client_id: user.client_id! }))
            }
          }}
          className="flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Chatbot</span>
        </Button>
      </div>

      {/* Search */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search chatbots..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Badge variant="secondary">
          {filteredChatbots.length} chatbot{filteredChatbots.length !== 1 ? 's' : ''}
        </Badge>
      </div>

      {/* Chatbots Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredChatbots.map((chatbot) => (
          <motion.div
            key={chatbot.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5 }}
            transition={{ duration: 0.2 }}
          >
            <Card className="h-full hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
                      <MessageCircle className="w-5 h-5" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{chatbot.name}</CardTitle>
                      <div className="flex items-center space-x-2 mt-1">
                        <Building2 className="w-3 h-3 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">{chatbot.client_name}</span>
                      </div>
                    </div>
                  </div>
                  <Badge variant={chatbot.is_active ? "default" : "secondary"}>
                    {chatbot.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {chatbot.description && (
                  <p className="text-sm text-muted-foreground">{chatbot.description}</p>
                )}
                
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <Globe className="w-3 h-3" />
                  <span className="truncate">{chatbot.webhook_url}</span>
                </div>

                <div className="text-xs text-muted-foreground">
                  Created {new Date(chatbot.created_at).toLocaleDateString()}
                </div>

                <div className="flex items-center justify-between pt-2 border-t">
                  <Link to={`/chatbots/${chatbot.id}`}>
                    <Button variant="outline" size="sm" className="flex items-center space-x-1">
                      <ExternalLink className="w-3 h-3" />
                      <span>Open Chat</span>
                    </Button>
                  </Link>
                  
                  <div className="flex items-center space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(chatbot)}
                      className="p-2"
                    >
                      <Edit className="w-3 h-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(chatbot)}
                      className="p-2 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {filteredChatbots.length === 0 && (
        <div className="text-center py-12">
          <MessageCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No chatbots found</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery ? 'No chatbots match your search criteria.' : 'Get started by creating your first chatbot.'}
          </p>
          {!searchQuery && (
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Chatbot
            </Button>
          )}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showCreateDialog || !!editingChatbot} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false)
          setEditingChatbot(null)
          resetForm()
        }
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingChatbot ? 'Edit Chatbot' : 'Create New Chatbot'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="Enter chatbot name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                placeholder="Brief description of the chatbot"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="webhook_url">Webhook URL *</Label>
              <Input
                id="webhook_url"
                placeholder="https://your-n8n-webhook-url.com"
                value={formData.webhook_url}
                onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
              />
            </div>

            {isAdmin && (
              <div>
                <Label htmlFor="client">Client *</Label>
                <Select
                  value={formData.client_id}
                  onValueChange={(value) => setFormData({ ...formData, client_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a client" />
                  </SelectTrigger>
                  <SelectContent>
                    {clients.map((client) => (
                      <SelectItem key={client.id} value={client.id}>
                        {client.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCreateDialog(false)
                setEditingChatbot(null)
                resetForm()
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={editingChatbot ? handleUpdate : handleCreate}
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {editingChatbot ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}