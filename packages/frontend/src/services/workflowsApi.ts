import api from '@/services/authApi'
import { extractApiData } from '@/utils/apiUtils'
import type { StandardResponse, ErrorResponse } from '@/types/api'

export type WorkflowListItem = {
  id: string
  client_id: string
  client_name?: string
  n8n_workflow_id: string
  workflow_name: string
  active: boolean
  total_executions: number
  successful_executions: number
  failed_executions: number
  success_rate: number
  avg_execution_time_ms: number
  avg_execution_time_seconds: number
  last_execution?: string | null
  time_saved_per_execution_minutes: number
  time_saved_hours?: number
}

export type WorkflowListResponse = {
  workflows: WorkflowListItem[]
  total: number
}

export interface WorkflowDetails extends WorkflowListItem {
  // Additional details that might be returned for individual workflow
}

export interface WorkflowUpdate {
  time_saved_per_execution_minutes?: number
  // Other updatable fields can be added here
}

export class WorkflowsApi {
  // New consolidated methods
  static async getWorkflows(clientId?: string, active?: boolean): Promise<WorkflowListResponse> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)
    if (active !== undefined) params.append('active', active.toString())
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const res = await api.get<StandardResponse<WorkflowListResponse> | ErrorResponse>(`/workflows/${queryString}`)
    return extractApiData<WorkflowListResponse>(res)
  }

  static async getWorkflow(workflowId: string): Promise<WorkflowDetails> {
    const res = await api.get<StandardResponse<WorkflowDetails> | ErrorResponse>(`/workflows/${workflowId}`)
    return extractApiData<WorkflowDetails>(res)
  }

  static async updateWorkflow(workflowId: string, data: WorkflowUpdate): Promise<WorkflowDetails> {
    const res = await api.patch<StandardResponse<WorkflowDetails> | ErrorResponse>(`/workflows/${workflowId}`, data)
    return extractApiData<WorkflowDetails>(res)
  }

}


