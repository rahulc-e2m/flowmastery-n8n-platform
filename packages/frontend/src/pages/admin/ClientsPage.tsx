import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ClientApi, type N8nConnectionTestResponse } from '@/services/clientApi'
import { 
  Building2, 
  Plus, 
  Settings, 
  Trash2, 
  CheckCircle,
  XCircle,
  ExternalLink,
  TestTube,
  RefreshCw,
  Loader2
} from 'lucide-react'
import { ClientStatusIndicator } from '@/components/ui/client-status-indicator'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { formatDistanceToNow } from 'date-fns'
import type { Client, ClientN8nConfig } from '@/types/client'

const createClientSchema = z.object({
  name: z.string().min(1, 'Client name is required'),
})

const n8nConfigSchema = z.object({
  n8n_api_url: z.string().url('Invalid URL'),
  n8n_api_key: z.string().min(1, 'API key is required'),
})

type CreateClientFormData = z.infer<typeof createClientSchema>
type N8nConfigFormData = z.infer<typeof n8nConfigSchema>

export function ClientsPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  const [selectedClient, setSelectedClient] = useState<Client | null>(null)
  const [connectionTestResult, setConnectionTestResult] = useState<N8nConnectionTestResponse | null>(null)
  const [isTestingConnection, setIsTestingConnection] = useState(false)
  const queryClient = useQueryClient()

  const { data: clients, isLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: ClientApi.getClients,
  })

  const createClientMutation = useMutation({
    mutationFn: ClientApi.createClient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      setCreateDialogOpen(false)
      toast.success('Client created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create client')
    },
  })

  const configureN8nMutation = useMutation({
    mutationFn: ({ clientId, config }: { clientId: string; config: ClientN8nConfig }) =>
      ClientApi.configureN8nApi(clientId, config),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      setConfigDialogOpen(false)
      setSelectedClient(null)
      setConnectionTestResult(null)
      toast.success(
        `n8n configuration updated successfully! ${data.note}`,
        { duration: 5000 }
      )
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to configure n8n API')
    },
  })

  const deleteClientMutation = useMutation({
    mutationFn: ClientApi.deleteClient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      toast.success('Client deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete client')
    },
  })

  const triggerSyncMutation = useMutation({
    mutationFn: ClientApi.triggerImmediateSync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      toast.success('Immediate sync completed successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to trigger sync')
    },
  })

  const {
    register: registerCreate,
    handleSubmit: handleCreateSubmit,
    formState: { errors: createErrors },
    reset: resetCreate,
  } = useForm<CreateClientFormData>({
    resolver: zodResolver(createClientSchema),
  })

  const {
    register: registerConfig,
    handleSubmit: handleConfigSubmit,
    formState: { errors: configErrors },
    reset: resetConfig,
  } = useForm<N8nConfigFormData>({
    resolver: zodResolver(n8nConfigSchema),
  })

  const onCreateClient = (data: CreateClientFormData) => {
    createClientMutation.mutate(data)
  }

  const onConfigureN8n = (data: N8nConfigFormData) => {
    if (selectedClient) {
      configureN8nMutation.mutate({
        clientId: selectedClient.id,
        config: data,
      })
    }
  }

  const testConnection = async (data: N8nConfigFormData) => {
    setIsTestingConnection(true)
    setConnectionTestResult(null)
    
    try {
      const result = await ClientApi.testN8nConnection(data)
      setConnectionTestResult(result)
      
      if (result.status === 'success') {
        toast.success('Connection test successful!')
      } else if (result.status === 'warning') {
        toast.warning(result.message)
      } else {
        toast.error(result.message)
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Connection test failed'
      toast.error(errorMessage)
      setConnectionTestResult({
        status: 'error',
        connection_healthy: false,
        api_accessible: false,
        message: errorMessage,
        instance_info: {}
      })
    } finally {
      setIsTestingConnection(false)
    }
  }

  const handleConfigureN8n = (client: Client) => {
    setSelectedClient(client)
    setConnectionTestResult(null)
    resetConfig({
      n8n_api_url: client.n8n_api_url || '',
      n8n_api_key: '',
    })
    setConfigDialogOpen(true)
  }

  const handleTriggerSync = (clientId: string) => {
    if (confirm('This will immediately sync data from the n8n instance. Continue?')) {
      triggerSyncMutation.mutate(clientId, {
        onError: (error: any) => {
          const status = error.response?.status
          const message = error.response?.data?.detail || error.message
          
          if (status === 503) {
            toast.error(
              'n8n workspace is currently offline. Please try again later.',
              { duration: 8000 }
            )
          } else if (status === 400 && message?.includes('API key')) {
            toast.error(
              'n8n API configuration issue. Please reconfigure the API settings.',
              { duration: 8000 }
            )
          } else {
            toast.error(message || 'Failed to trigger sync')
          }
        }
      })
    }
  }

  const handleDeleteClient = (clientId: string) => {
    if (confirm('Are you sure you want to delete this client? This action cannot be undone.')) {
      deleteClientMutation.mutate(clientId)
    }
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-muted rounded w-64"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-48 bg-muted rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Clients</h1>
          <p className="text-muted-foreground mt-2">Manage your clients and their n8n configurations</p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => resetCreate()}>
              <Plus className="w-4 h-4 mr-2" />
              Add Client
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Client</DialogTitle>
              <DialogDescription>
                Add a new client to the system. You can configure their n8n API later.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateSubmit(onCreateClient)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Client Name</Label>
                <Input
                  id="name"
                  placeholder="Enter client name"
                  {...registerCreate('name')}
                  className={createErrors.name ? 'border-red-500' : ''}
                />
                {createErrors.name && (
                  <p className="text-sm text-red-500">{createErrors.name.message}</p>
                )}
              </div>
              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCreateDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createClientMutation.isPending}>
                  {createClientMutation.isPending ? 'Creating...' : 'Create Client'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clients?.map((client) => (
          <Card key={client.id} className="relative admin-card hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{client.name}</CardTitle>
                    <CardDescription>
                      Created {formatDistanceToNow(new Date(client.created_at), { addSuffix: true })}
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">n8n Status</span>
                  <ClientStatusIndicator 
                    clientId={client.id}
                    clientName={client.name}
                    hasApiKey={client.has_n8n_api_key}
                    compact={true}
                  />
                </div>

                {client.n8n_api_url && (
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <ExternalLink className="w-4 h-4" />
                    <span className="truncate">{client.n8n_api_url}</span>
                  </div>
                )}

                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleConfigureN8n(client)}
                    className="flex-1"
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    Configure n8n
                  </Button>
                  {client.has_n8n_api_key && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleTriggerSync(client.id)}
                      disabled={triggerSyncMutation.isPending}
                      className="flex-1"
                    >
                      {triggerSyncMutation.isPending ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-2" />
                      )}
                      Sync Now
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteClient(client.id)}
                    className="text-destructive hover:text-destructive/80 hover:bg-destructive/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* n8n Configuration Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Configure n8n API</DialogTitle>
            <DialogDescription>
              Set up the n8n API connection for {selectedClient?.name}. Connection will be tested and data will be fetched immediately upon configuration.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleConfigSubmit(onConfigureN8n)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="n8n_api_url">n8n API URL</Label>
              <Input
                id="n8n_api_url"
                placeholder="https://your-n8n-instance.com/api/v1"
                {...registerConfig('n8n_api_url')}
                className={configErrors.n8n_api_url ? 'border-red-500' : ''}
              />
              {configErrors.n8n_api_url && (
                <p className="text-sm text-red-500">{configErrors.n8n_api_url.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="n8n_api_key">n8n API Key</Label>
              <Input
                id="n8n_api_key"
                type="password"
                placeholder="Enter n8n API key"
                {...registerConfig('n8n_api_key')}
                className={configErrors.n8n_api_key ? 'border-red-500' : ''}
              />
              {configErrors.n8n_api_key && (
                <p className="text-sm text-red-500">{configErrors.n8n_api_key.message}</p>
              )}
            </div>
            
            {/* Connection Test Results */}
            {connectionTestResult && (
              <div className={`p-3 rounded-lg border ${
                connectionTestResult.status === 'success' ? 'bg-green-50 border-green-200' :
                connectionTestResult.status === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center space-x-2 mb-2">
                  {connectionTestResult.status === 'success' ? (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  ) : connectionTestResult.status === 'warning' ? (
                    <XCircle className="w-4 h-4 text-yellow-600" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-600" />
                  )}
                  <span className={`text-sm font-medium ${
                    connectionTestResult.status === 'success' ? 'text-green-800' :
                    connectionTestResult.status === 'warning' ? 'text-yellow-800' :
                    'text-red-800'
                  }`}>
                    Connection Test: {connectionTestResult.status === 'success' ? 'Success' : 
                                    connectionTestResult.status === 'warning' ? 'Warning' : 'Failed'}
                  </span>
                </div>
                <p className={`text-sm ${
                  connectionTestResult.status === 'success' ? 'text-green-700' :
                  connectionTestResult.status === 'warning' ? 'text-yellow-700' :
                  'text-red-700'
                }`}>
                  {connectionTestResult.message}
                </p>
                {connectionTestResult.instance_info && Object.keys(connectionTestResult.instance_info).length > 0 && (
                  <div className="mt-2 text-xs text-gray-600">
                    <div>Has workflows: {connectionTestResult.instance_info.has_workflows ? 'Yes' : 'No'}</div>
                    <div>Has executions: {connectionTestResult.instance_info.has_executions ? 'Yes' : 'No'}</div>
                  </div>
                )}
              </div>
            )}
            
            <div className="flex justify-end space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setConfigDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleConfigSubmit(testConnection)}
                disabled={isTestingConnection}
              >
                {isTestingConnection ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <TestTube className="w-4 h-4 mr-2" />
                )}
                Validate Key
              </Button>
              <Button 
                type="submit" 
                disabled={configureN8nMutation.isPending || (connectionTestResult?.status === 'error')}
              >
                {configureN8nMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Configuring & Syncing...
                  </>
                ) : (
                  'Save & Sync Data'
                )}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}