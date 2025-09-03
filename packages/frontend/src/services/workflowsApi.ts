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

export class WorkflowsApi {
  static async listAll(clientId?: string, activeFilter?: string): Promise<WorkflowListResponse> {
    const params: any = {}
    if (clientId) params.client_id = clientId
    if (activeFilter && activeFilter !== 'all') params.active = activeFilter === 'active'
    const res = await api.get<StandardResponse<WorkflowListResponse> | ErrorResponse>('/workflows', { params })
    return extractApiData<WorkflowListResponse>(res)
  }

  static async listMine(activeFilter?: string): Promise<WorkflowListResponse> {
    const params: any = {}
    if (activeFilter && activeFilter !== 'all') params.active = activeFilter === 'active'
    const res = await api.get<StandardResponse<WorkflowListResponse> | ErrorResponse>('/workflows/my', { params })
    return extractApiData<WorkflowListResponse>(res)
  }

  static async updateMinutes(workflowDbId: string, minutes: number): Promise<{ id: string; time_saved_per_execution_minutes: number }> {
    const res = await api.patch<StandardResponse<{ id: string; time_saved_per_execution_minutes: number }> | ErrorResponse>(`/workflows/${workflowDbId}`, { time_saved_per_execution_minutes: minutes })
    return extractApiData<{ id: string; time_saved_per_execution_minutes: number }>(res)
  }
}


