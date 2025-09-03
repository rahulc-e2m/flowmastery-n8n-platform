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
   * Get paginated list of dependencies
   */
  async getDependencies(filters: DependencyFilters = {}): Promise<DependencyListResponse> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.per_page) params.append('per_page', filters.per_page.toString());
    if (filters.search) params.append('search', filters.search);
    
    const response = await api.get<StandardResponse<DependencyListResponse> | ErrorResponse>(`/dependencies/?${params.toString()}`);
    return extractApiData<DependencyListResponse>(response);
  }

  /**
   * Get a specific dependency by ID
   */
  async getDependency(id: string): Promise<Dependency> {
    const response = await api.get<StandardResponse<Dependency> | ErrorResponse>(`/dependencies/${id}`);
    return extractApiData<Dependency>(response);
  }

  /**
   * Get a dependency by platform name
   */
  async getDependencyByPlatform(platformName: string): Promise<Dependency> {
    const response = await api.get<StandardResponse<Dependency> | ErrorResponse>(`/dependencies/platform/${encodeURIComponent(platformName)}`);
    return extractApiData<Dependency>(response);
  }

  /**
   * Create a new dependency (admin only)
   */
  async createDependency(data: DependencyCreate): Promise<Dependency> {
    const response = await api.post<StandardResponse<Dependency> | ErrorResponse>('/dependencies/', data);
    return extractApiData<Dependency>(response);
  }

  /**
   * Update an existing dependency (admin only)
   */
  async updateDependency(id: string, data: DependencyUpdate): Promise<Dependency> {
    const response = await api.put<StandardResponse<Dependency> | ErrorResponse>(`/dependencies/${id}`, data);
    return extractApiData<Dependency>(response);
  }

  /**
   * Delete a dependency (admin only)
   */
  async deleteDependency(id: string): Promise<void> {
    await api.delete<StandardResponse<void> | ErrorResponse>(`/dependencies/${id}`);
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