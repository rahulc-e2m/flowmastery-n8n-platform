import api from './authApi'
import type {
  Client,
  ClientCreate,
  ClientUpdate,
  ClientN8nConfig
} from '@/types/client'

export class ClientApi {
  static async createClient(client: ClientCreate): Promise<Client> {
    const response = await api.post<Client>('/clients/', client)
    return response.data
  }

  static async getClients(): Promise<Client[]> {
    const response = await api.get<Client[]>('/clients/')
    return response.data
  }

  static async getClient(clientId: number): Promise<Client> {
    const response = await api.get<Client>(`/clients/${clientId}`)
    return response.data
  }

  static async updateClient(clientId: number, client: ClientUpdate): Promise<Client> {
    const response = await api.put<Client>(`/clients/${clientId}`, client)
    return response.data
  }

  static async configureN8nApi(clientId: number, config: ClientN8nConfig): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>(`/clients/${clientId}/n8n-config`, config)
    return response.data
  }

  static async deleteClient(clientId: number): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/clients/${clientId}`)
    return response.data
  }
}