import api from './authApi';

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
    
    const response = await api.get(`/dependencies/?${params.toString()}`);
    return response.data;
  }

  /**
   * Get a specific dependency by ID
   */
  async getDependency(id: string): Promise<Dependency> {
    const response = await api.get(`/dependencies/${id}`);
    return response.data;
  }

  /**
   * Get a dependency by platform name
   */
  async getDependencyByPlatform(platformName: string): Promise<Dependency> {
    const response = await api.get(`/dependencies/platform/${encodeURIComponent(platformName)}`);
    return response.data;
  }

  /**
   * Create a new dependency (admin only)
   */
  async createDependency(data: DependencyCreate): Promise<Dependency> {
    const response = await api.post('/dependencies/', data);
    return response.data;
  }

  /**
   * Update an existing dependency (admin only)
   */
  async updateDependency(id: string, data: DependencyUpdate): Promise<Dependency> {
    const response = await api.put(`/dependencies/${id}`, data);
    return response.data;
  }

  /**
   * Delete a dependency (admin only)
   */
  async deleteDependency(id: string): Promise<void> {
    await api.delete(`/dependencies/${id}`);
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