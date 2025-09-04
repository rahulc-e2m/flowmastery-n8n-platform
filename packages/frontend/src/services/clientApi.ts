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
    const response = await api.get<StandardResponse<PaginatedResponse<Client>> | ErrorResponse>('/clients/')
    const paginatedData = extractApiData<PaginatedResponse<Client>>(response)
    return paginatedData.items
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

  static async configureN8nApi(clientId: string, config: ClientN8nConfig): Promise<ClientSyncResponse> {
    const response = await api.post<StandardResponse<ClientSyncResponse> | ErrorResponse>(`/clients/${clientId}/n8n-config`, config)
    return extractApiData<ClientSyncResponse>(response)
  }

  static async testN8nConnection(config: ClientN8nConfig): Promise<N8nConnectionTestResponse> {
    const response = await api.post<StandardResponse<N8nConnectionTestResponse> | ErrorResponse>('/clients/test-n8n-connection', config)
    return extractApiData<N8nConnectionTestResponse>(response)
  }

  static async triggerImmediateSync(clientId: string): Promise<ManualSyncResponse> {
    const response = await api.post<StandardResponse<ManualSyncResponse> | ErrorResponse>(`/clients/${clientId}/sync-n8n`)
    return extractApiData<ManualSyncResponse>(response)
  }

  static async getClientConfigStatus(clientId: string): Promise<any> {
    const response = await api.get<StandardResponse<any> | ErrorResponse>(`/clients/${clientId}/config-status`)
    return extractApiData<any>(response)
  }

  static async deleteClient(clientId: string): Promise<{ message: string }> {
    const response = await api.delete<StandardResponse<{ message: string }> | ErrorResponse>(`/clients/${clientId}`)
    return extractApiData<{ message: string }>(response)
  }
}