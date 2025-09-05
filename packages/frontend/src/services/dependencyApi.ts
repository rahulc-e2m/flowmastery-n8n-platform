import api from './authApi';
import { extractApiData } from '@/utils/apiUtils';
import type { StandardResponse, ErrorResponse } from '@/types/api';

export interface Dependency {
  id: string;
  platform_name: string;
  where_to_get?: string;
  guide_link?: string;
  documentation_link?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface DependencyCreate {
  platform_name: string;
  where_to_get?: string;
  guide_link?: string;
  documentation_link?: string;
  description?: string;
}

export interface DependencyUpdate {
  platform_name?: string;
  where_to_get?: string;
  guide_link?: string;
  documentation_link?: string;
  description?: string;
}

export interface DependencyListResponse {
  dependencies: Dependency[];
  total: number;
  page: number;
  per_page: number;
}

export interface DependencyFilters {
  page?: number;
  per_page?: number;
  search?: string;
}

class DependencyApi {
  /**
   * Get paginated list of dependencies (guides)
   */
  async getDependencies(filters: DependencyFilters = {}): Promise<DependencyListResponse> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.per_page) params.append('per_page', filters.per_page.toString());
    if (filters.search) params.append('search', filters.search);
    
    const response = await api.get<StandardResponse<DependencyListResponse> | ErrorResponse>(`/guides/?${params.toString()}`);
    return extractApiData<DependencyListResponse>(response);
  }

  /**
   * Get a specific dependency by ID
   */
  async getDependency(id: string): Promise<Dependency> {
    const response = await api.get<StandardResponse<Dependency> | ErrorResponse>(`/guides/${id}`);
    return extractApiData<Dependency>(response);
  }

  /**
   * Get a dependency by platform name
   */
  async getDependencyByPlatform(platformName: string): Promise<Dependency> {
    const response = await api.get<StandardResponse<Dependency> | ErrorResponse>(`/guides/platform/${encodeURIComponent(platformName)}`);
    return extractApiData<Dependency>(response);
  }

  /**
   * Create a new dependency (admin only)
   */
  async createDependency(data: DependencyCreate): Promise<Dependency> {
    const response = await api.post<StandardResponse<Dependency> | ErrorResponse>('/guides/', data);
    return extractApiData<Dependency>(response);
  }

  /**
   * Update an existing dependency (admin only)
   */
  async updateDependency(id: string, data: DependencyUpdate): Promise<Dependency> {
    const response = await api.put<StandardResponse<Dependency> | ErrorResponse>(`/guides/${id}`, data);
    return extractApiData<Dependency>(response);
  }

  /**
   * Delete a dependency (admin only)
   */
  async deleteDependency(id: string): Promise<void> {
    await api.delete<StandardResponse<void> | ErrorResponse>(`/guides/${id}`);
    // Delete operations typically return 204 No Content, so no data to extract
  }

  /**
   * Get all dependencies without pagination (for simple lists)
   */
  async getAllDependencies(): Promise<Dependency[]> {
    const allDependencies: Dependency[] = [];
    let page = 1;
    const perPage = 100; // Maximum allowed by API
    
    while (true) {
      const response = await this.getDependencies({ 
        page, 
        per_page: perPage 
      });
      
      allDependencies.push(...response.dependencies);
      
      // If we got fewer items than requested, we've reached the end
      if (response.dependencies.length < perPage) {
        break;
      }
      
      page++;
    }
    
    return allDependencies;
  }
}

export const dependencyApi = new DependencyApi();

// System API for consolidated system operations
export interface SyncRequest {
  type: 'client' | 'all' | 'quick'
  client_id?: string
  options?: Record<string, any>
}

export interface SyncResult {
  message: string
  task_id?: string
  result?: any
  successful?: number
  failed?: number
}

export interface CacheStats {
  redis_info: {
    used_memory: string
    connected_clients: number
    total_commands_processed: number
  }
  cache_summary: {
    total_keys: number
    client_keys: number
    system_keys: number
  }
  client_cache_status: Array<{
    client_id: string
    client_name: string
    cache_keys: number
    last_updated: string
  }>
}

export interface CacheResult {
  message: string
  cleared_keys: number
  pattern?: string
}

export interface TaskStatus {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  result?: any
  error?: string
  started_at?: string
  completed_at?: string
}

export interface WorkerStats {
  active_workers: number
  total_tasks: number
  pending_tasks: number
  failed_tasks: number
  worker_details: Array<{
    worker_id: string
    status: string
    current_task?: string
  }>
}

export class SystemApi {
  static async sync(request: SyncRequest): Promise<SyncResult> {
    const response = await api.post<StandardResponse<SyncResult> | ErrorResponse>('/system/sync', request)
    return extractApiData<SyncResult>(response)
  }

  static async getCacheStats(): Promise<CacheStats> {
    const response = await api.get<StandardResponse<CacheStats> | ErrorResponse>('/cache/status')
    return extractApiData<CacheStats>(response)
  }

  static async clearCache(clientId?: string, pattern?: string): Promise<CacheResult> {
    const params = new URLSearchParams()
    if (clientId) params.append('client_id', clientId)
    if (pattern) params.append('pattern', pattern)
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    const response = await api.delete<StandardResponse<CacheResult> | ErrorResponse>(`/cache/all${queryString}`)
    return extractApiData<CacheResult>(response)
  }

  static async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await api.get<StandardResponse<TaskStatus> | ErrorResponse>(`/system/tasks/${taskId}`)
    return extractApiData<TaskStatus>(response)
  }

  static async getWorkerStats(): Promise<WorkerStats> {
    const response = await api.get<StandardResponse<WorkerStats> | ErrorResponse>('/system/worker-stats')
    return extractApiData<WorkerStats>(response)
  }
}