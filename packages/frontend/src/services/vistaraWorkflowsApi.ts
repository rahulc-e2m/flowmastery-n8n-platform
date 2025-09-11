import api from '@/services/authApi'
import { extractApiData } from '@/utils/apiUtils'
import type { StandardResponse, ErrorResponse } from '@/types/api'
import { VistaraCategory } from './vistaraCategoriesApi'

export interface VistaraWorkflowMetrics {
  total_executions: number
  successful_executions: number
  failed_executions: number
  success_rate: number
  avg_execution_time_ms: number
  manual_time_minutes: number
  time_saved_per_execution_minutes: number
  total_time_saved_hours: number
  last_execution?: string
}

export interface VistaraWorkflow {
  id: string
  original_workflow_id?: string
  n8n_workflow_id?: string
  workflow_name: string
  summary?: string
  documentation_link?: string
  category?: Pick<VistaraCategory, 'id' | 'name' | 'color' | 'description'>
  client?: {
    id: string
    name: string
    n8n_api_url?: string
  }
  is_featured: boolean
  display_order: number
  metrics: VistaraWorkflowMetrics
  created_at: string
  updated_at: string
}

export interface CreateVistaraWorkflowData {
  workflow_name: string
  original_workflow_id?: string
  summary?: string
  documentation_link?: string
  category_id?: string
  is_featured?: boolean
  display_order?: number
  // Metrics
  total_executions?: number
  successful_executions?: number
  failed_executions?: number
  success_rate?: number
  avg_execution_time_ms?: number
  manual_time_minutes?: number
  time_saved_per_execution_minutes?: number
  total_time_saved_hours?: number
}

export interface UpdateVistaraWorkflowData {
  workflow_name?: string
  summary?: string
  documentation_link?: string
  category_id?: string
  is_featured?: boolean
  display_order?: number
  // Metrics
  total_executions?: number
  successful_executions?: number
  failed_executions?: number
  success_rate?: number
  avg_execution_time_ms?: number
  manual_time_minutes?: number
  time_saved_per_execution_minutes?: number
  total_time_saved_hours?: number
}

export interface AvailableWorkflow {
  id: string
  name: string
  description?: string
  tags: string[]
}

export interface VistaraWorkflowQueryParams {
  category_id?: string
  is_featured?: boolean
}

export class VistaraWorkflowsApi {
  static async getVistaraWorkflows(params?: VistaraWorkflowQueryParams): Promise<VistaraWorkflow[]> {
    const queryString = params ? new URLSearchParams(params as any).toString() : ''
    const response = await api.get<StandardResponse<VistaraWorkflow[]> | ErrorResponse>(`/vistara/workflows/${queryString ? `?${queryString}` : ''}`)
    return extractApiData<VistaraWorkflow[]>(response)
  }

  static async getVistaraWorkflowDetails(id: string): Promise<VistaraWorkflow> {
    const response = await api.get<StandardResponse<VistaraWorkflow> | ErrorResponse>(`/vistara/workflows/${id}`)
    return extractApiData<VistaraWorkflow>(response)
  }

  static async createVistaraWorkflow(data: CreateVistaraWorkflowData): Promise<VistaraWorkflow> {
    const response = await api.post<StandardResponse<VistaraWorkflow> | ErrorResponse>('/vistara/workflows/', data)
    return extractApiData<VistaraWorkflow>(response)
  }

  static async updateVistaraWorkflow(id: string, data: UpdateVistaraWorkflowData): Promise<VistaraWorkflow> {
    const response = await api.put<StandardResponse<VistaraWorkflow> | ErrorResponse>(`/vistara/workflows/${id}`, data)
    return extractApiData<VistaraWorkflow>(response)
  }

  static async deleteVistaraWorkflow(id: string): Promise<{ id: string }> {
    const response = await api.delete<StandardResponse<{ id: string }> | ErrorResponse>(`/vistara/workflows/${id}`)
    return extractApiData<{ id: string }>(response)
  }

  static async getAvailableWorkflows(search?: string): Promise<AvailableWorkflow[]> {
    const queryString = search ? `?search=${encodeURIComponent(search)}` : ''
    const response = await api.get<StandardResponse<AvailableWorkflow[]> | ErrorResponse>(`/vistara/workflows/available-workflows/${queryString}`)
    
    // Debug: Log the response
    console.log('getAvailableWorkflows - Raw response:', response)
    console.log('getAvailableWorkflows - Response data:', response.data)
    
    const result = extractApiData<AvailableWorkflow[]>(response)
    console.log('getAvailableWorkflows - Extracted result:', result)
    console.log('getAvailableWorkflows - Result length:', result?.length)
    
    return result
  }

  static async syncVistaraMetrics(workflowId?: string): Promise<any> {
    const queryString = workflowId ? `?workflow_id=${encodeURIComponent(workflowId)}` : ''
    const response = await api.post<StandardResponse<any> | ErrorResponse>(`/vistara/workflows/sync-metrics${queryString}`)
    return extractApiData<any>(response)
  }
}
