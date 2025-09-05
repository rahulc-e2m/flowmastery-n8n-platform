import api from './authApi';
import { extractApiData } from '@/utils/apiUtils';
import type { StandardResponse, ErrorResponse } from '@/types/api';

export interface TaskStatusResponse {
  status: string;
  client_id: string;
  last_sync?: string;
  sync_in_progress: boolean;
  message?: string;
}

export interface TaskSyncResponse {
  message: string;
  client_id: string;
  sync_triggered: boolean;
  task_id?: string;
}

export interface TaskSyncRequest {
  force?: boolean;
  type?: 'full' | 'incremental';
}

export class TasksApi {
  /**
   * Get task status for a specific client
   */
  static async getTaskStatus(clientId: string): Promise<TaskStatusResponse> {
    const response = await api.get<StandardResponse<TaskStatusResponse> | ErrorResponse>(`/tasks/status/${clientId}`);
    return extractApiData<TaskStatusResponse>(response);
  }

  /**
   * Trigger sync for a specific client
   */
  static async syncClient(clientId: string, options: TaskSyncRequest = {}): Promise<TaskSyncResponse> {
    const response = await api.post<StandardResponse<TaskSyncResponse> | ErrorResponse>(`/tasks/sync/${clientId}`, options);
    return extractApiData<TaskSyncResponse>(response);
  }

  /**
   * Get task status for multiple clients (admin only)
   */
  static async getAllTaskStatuses(): Promise<TaskStatusResponse[]> {
    const response = await api.get<StandardResponse<TaskStatusResponse[]> | ErrorResponse>('/tasks/status');
    return extractApiData<TaskStatusResponse[]>(response);
  }
}

export default TasksApi;
