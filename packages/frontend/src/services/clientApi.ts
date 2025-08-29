import api from './authApi'
import type {
  Client,
  ClientCreate,
  ClientUpdate,
  ClientN8nConfig
} from '@/types/client'

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
    const response = await api.post<Client>('/clients/', client)
    return response.data
  }

  static async getClients(): Promise<Client[]> {
    const response = await api.get<Client[]>('/clients/')
    return response.data
  }

  // Alias for consistency with other APIs
  static async getAll(): Promise<Client[]> {
    return this.getClients()
  }

  static async getClient(clientId: string): Promise<Client> {
    const response = await api.get<Client>(`/clients/${clientId}`)
    return response.data
  }

  static async updateClient(clientId: string, client: ClientUpdate): Promise<Client> {
    const response = await api.put<Client>(`/clients/${clientId}`, client)
    return response.data
  }

  static async configureN8nApi(clientId: string, config: ClientN8nConfig): Promise<ClientSyncResponse> {
    const response = await api.post<ClientSyncResponse>(`/clients/${clientId}/n8n-config`, config)
    return response.data
  }

  static async testN8nConnection(config: ClientN8nConfig): Promise<N8nConnectionTestResponse> {
    const response = await api.post<N8nConnectionTestResponse>('/clients/test-n8n-connection', config)
    return response.data
  }

  static async triggerImmediateSync(clientId: string): Promise<ManualSyncResponse> {
    const response = await api.post<ManualSyncResponse>(`/clients/${clientId}/sync-n8n`)
    return response.data
  }

  static async deleteClient(clientId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/clients/${clientId}`)
    return response.data
  }
}