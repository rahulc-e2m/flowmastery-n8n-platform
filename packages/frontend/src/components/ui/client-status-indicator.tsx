import { useQuery } from '@tanstack/react-query'
import { ClientApi } from '@/services/clientApi'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react'

interface ClientStatusIndicatorProps {
  clientId: string
  clientName: string
  hasApiKey: boolean
  compact?: boolean
}

export function ClientStatusIndicator({ 
  clientId, 
  hasApiKey, 
  compact = false 
}: ClientStatusIndicatorProps) {
  const { data: client, isLoading } = useQuery({
      queryKey: ['client', clientId],
      queryFn: () => ClientApi.getClientWithConfig(clientId, true),
      enabled: hasApiKey, // Only check status if client has basic config
      refetchInterval: 30000, // Check every 30 seconds
      retry: 1,
    })

  const configStatus = client?.config_status

  if (!hasApiKey) {
    return (
      <Badge variant="secondary" className="flex items-center space-x-1">
        <XCircle className="w-3 h-3" />
        <span>Not configured</span>
      </Badge>
    )
  }

  if (isLoading) {
    return (
      <Badge variant="outline" className="flex items-center space-x-1">
        <Loader2 className="w-3 h-3 animate-spin" />
        <span>Checking...</span>
      </Badge>
    )
  }

  if (!configStatus) {
    return (
      <Badge variant="secondary" className="flex items-center space-x-1">
        <AlertCircle className="w-3 h-3" />
        <span>Unknown</span>
      </Badge>
    )
  }

  if (configStatus.configured) {
    return (
      <Badge variant="default" className="flex items-center space-x-1">
        <CheckCircle className="w-3 h-3" />
        <span>Connected</span>
      </Badge>
    )
  }

  // Determine the type of issue based on connection status
  const connectionStatus = configStatus.n8n_connection_status
  const errorMessage = connectionStatus === 'error' ? 'Connection error' : ''
  const isServiceIssue = errorMessage.includes('offline') || 
                        errorMessage.includes('503') || 
                        errorMessage.includes('unavailable')
  
  const isAuthIssue = errorMessage.includes('authentication') || 
                     errorMessage.includes('API key') || 
                     errorMessage.includes('401') || 
                     errorMessage.includes('403')

  if (isServiceIssue) {
    return (
      <Badge variant="destructive" className="flex items-center space-x-1">
        <AlertCircle className="w-3 h-3" />
        <span>{compact ? 'Offline' : 'Service Offline'}</span>
      </Badge>
    )
  }

  if (isAuthIssue) {
    return (
      <Badge variant="destructive" className="flex items-center space-x-1">
        <XCircle className="w-3 h-3" />
        <span>{compact ? 'Auth Error' : 'Auth Failed'}</span>
      </Badge>
    )
  }

  return (
    <Badge variant="destructive" className="flex items-center space-x-1">
      <XCircle className="w-3 h-3" />
      <span>{compact ? 'Error' : 'Connection Error'}</span>
    </Badge>
  )
}