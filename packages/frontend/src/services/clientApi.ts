import api from './authApi'
import type {
  Client,
  ClientCreate,
  ClientUpdate,
  ClientN8nConfig
} from '@/types/client'
import { extractApiData } from '@/utils/apiUtils'
import type { StandardResponse, ErrorResponse, PaginatedResponse } from '@/types/api'

export interface N8nConnectionTestResponse {
  status: 'success' | 'warning' | 'error'
  connection_healthy: boolean
  api_accessible: boolean
  message: string
  instance_info: Record<string, any>
}

export interface ClientSyncResponse {
  message: string
  client_id: string
  client_name: string
  immediate_sync_triggered: boolean
  note: string
}

export interface ManualSyncResponse {
  message: string
  sync_result: Record<string, any>
}

export class ClientApi {
  static async createClient(client: ClientCreate): Promise<Client> {
    const response = await api.post<StandardResponse<Client> | ErrorResponse>('/clients/', client)
    return extractApiData<Client>(response)
  }

  static async getClients(): Promise<Client[]> {
    try {
      const response = await api.get<StandardResponse<PaginatedResponse<Client>> | ErrorResponse>('/clients/')
      const paginatedData = extractApiData<PaginatedResponse<Client>>(response)
      return paginatedData?.items || []
    } catch (error) {
      return []
    }
  }

  // Alias for consistency with other APIs
  static async getAll(): Promise<Client[]> {
    return this.getClients()
  }

  static async getClient(clientId: string): Promise<Client> {
    const response = await api.get<StandardResponse<Client> | ErrorResponse>(`/clients/${clientId}`)
    return extractApiData<Client>(response)
  }

  static async updateClient(clientId: string, client: ClientUpdate): Promise<Client> {
    const response = await api.put<StandardResponse<Client> | ErrorResponse>(`/clients/${clientId}`, client)
    return extractApiData<Client>(response)
  }

  // New consolidated methods
  static async configureClient(
    clientId: string, 
    config: ClientN8nConfig, 
    testConnection?: boolean
  ): Promise<ClientSyncResponse> {
    const params = new URLSearchParams()
    if (testConnection !== undefined) params.append('test_connection', testConnection.toString())
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.post<StandardResponse<ClientSyncResponse> | ErrorResponse>(`/clients/${clientId}/configure${queryString}`, config)
    return extractApiData<ClientSyncResponse>(response)
  }

  static async testConnection(clientId: string): Promise<N8nConnectionTestResponse> {
    const response = await api.post<StandardResponse<N8nConnectionTestResponse> | ErrorResponse>(`/clients/${clientId}/test-connection`)
    return extractApiData<N8nConnectionTestResponse>(response)
  }

  static async syncClient(clientId: string): Promise<ManualSyncResponse> {
    const response = await api.post<StandardResponse<ManualSyncResponse> | ErrorResponse>(`/clients/${clientId}/sync`)
    return extractApiData<ManualSyncResponse>(response)
  }

  // Enhanced getClient method with optional config status
  static async getClientWithConfig(clientId: string, includeConfigStatus?: boolean): Promise<Client> {
    const params = new URLSearchParams()
    if (includeConfigStatus) params.append('include_config_status', 'true')
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.get<StandardResponse<Client> | ErrorResponse>(`/clients/${clientId}${queryString}`)
    return extractApiData<Client>(response)
  }

  // Legacy methods for backward compatibility
  static async configureN8nApi(clientId: string, config: ClientN8nConfig): Promise<ClientSyncResponse> {
    console.warn('ClientApi.configureN8nApi is deprecated. Use ClientApi.configureClient instead.')
    return this.configureClient(clientId, config, false)
  }

  static async testN8nConnection(config: ClientN8nConfig): Promise<N8nConnectionTestResponse> {
    console.warn('ClientApi.testN8nConnection is deprecated. Use ClientApi.testConnection instead.')
    // This method signature doesn't match the new API, so we'll need to handle it differently
    // For now, we'll throw an error suggesting the new approach
    throw new Error('testN8nConnection with config parameter is deprecated. Use testConnection(clientId) after configuring the client.')
  }

  static async triggerImmediateSync(clientId: string): Promise<ManualSyncResponse> {
    console.warn('ClientApi.triggerImmediateSync is deprecated. Use ClientApi.syncClient instead.')
    return this.syncClient(clientId)
  }

  static async getClientConfigStatus(clientId: string): Promise<any> {
    console.warn('ClientApi.getClientConfigStatus is deprecated. Use ClientApi.getClientWithConfig(id, true) instead.')
    const client = await this.getClientWithConfig(clientId, true)
    return (client as any).config_status
  }

  static async deleteClient(clientId: string): Promise<{ message: string }> {
    const response = await api.delete<StandardResponse<{ message: string }> | ErrorResponse>(`/clients/${clientId}`)
    return extractApiData<{ message: string }>(response)
  }
}