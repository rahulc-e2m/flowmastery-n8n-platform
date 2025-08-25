import api from './authApi'
import type {
  ClientMetrics,
  ClientWorkflowMetrics,
  AdminMetricsResponse
} from '@/types/metrics'

export class MetricsApi {
  static async getAllClientsMetrics(): Promise<AdminMetricsResponse> {
    const response = await api.get<AdminMetricsResponse>('/metrics/all')
    return response.data
  }

  static async getClientMetrics(clientId: number): Promise<ClientMetrics> {
    const response = await api.get<ClientMetrics>(`/metrics/client/${clientId}`)
    return response.data
  }

  static async getClientWorkflowMetrics(clientId: number): Promise<ClientWorkflowMetrics> {
    const response = await api.get<ClientWorkflowMetrics>(`/metrics/client/${clientId}/workflows`)
    return response.data
  }

  static async getMyMetrics(): Promise<ClientMetrics> {
    const response = await api.get<ClientMetrics>('/metrics/my-metrics')
    return response.data
  }

  static async getMyWorkflowMetrics(): Promise<ClientWorkflowMetrics> {
    const response = await api.get<ClientWorkflowMetrics>('/metrics/my-workflows')
    return response.data
  }
}