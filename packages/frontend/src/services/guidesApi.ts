import api from './authApi';
import { extractApiData } from '@/utils/apiUtils';
import type { StandardResponse, ErrorResponse } from '@/types/api';

// Updated interface to match backend guides structure
export interface Guide {
  id: string;
  title: string; // Backend uses 'title' field
  platform_name: string;
  where_to_get?: string;
  guide_link?: string;
  documentation_link?: string;
  description?: string;
  content?: string; // Backend may include content field
  created_at: string;
  updated_at: string;
}

export interface GuideCreate {
  title: string;
  platform_name: string;
  where_to_get?: string;
  guide_link?: string;
  documentation_link?: string;
  description?: string;
  content?: string;
}

export interface GuideUpdate {
  title?: string;
  platform_name?: string;
  where_to_get?: string;
  guide_link?: string;
  documentation_link?: string;
  description?: string;
  content?: string;
}

export interface GuideListResponse {
  guides: Guide[]; // Backend returns 'guides' array
  total: number;
  page: number;
  per_page: number;
}

export interface GuideFilters {
  page?: number;
  per_page?: number;
  search?: string;
}

export class GuidesApi {
  /**
   * Get paginated list of guides (public access)
   */
  static async getGuides(filters: GuideFilters = {}): Promise<GuideListResponse> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.per_page) params.append('per_page', filters.per_page.toString());
    if (filters.search) params.append('search', filters.search);
    
    const queryString = params.toString() ? `?${params.toString()}` : '';
    const response = await api.get<StandardResponse<GuideListResponse> | ErrorResponse>(`/guides/${queryString}`);
    return extractApiData<GuideListResponse>(response);
  }

  /**
   * Get a specific guide by ID (public access)
   */
  static async getGuide(id: string): Promise<Guide> {
    const response = await api.get<StandardResponse<Guide> | ErrorResponse>(`/guides/${id}`);
    return extractApiData<Guide>(response);
  }

  /**
   * Get a guide by platform name (public access)
   */
  static async getGuideByPlatform(platformName: string): Promise<Guide> {
    const response = await api.get<StandardResponse<Guide> | ErrorResponse>(`/guides/platform/${encodeURIComponent(platformName)}`);
    return extractApiData<Guide>(response);
  }

  /**
   * Create a new guide (admin only)
   */
  static async createGuide(data: GuideCreate): Promise<Guide> {
    const response = await api.post<StandardResponse<Guide> | ErrorResponse>('/guides/', data);
    return extractApiData<Guide>(response);
  }

  /**
   * Update an existing guide (admin only)
   */
  static async updateGuide(id: string, data: GuideUpdate): Promise<Guide> {
    const response = await api.put<StandardResponse<Guide> | ErrorResponse>(`/guides/${id}`, data);
    return extractApiData<Guide>(response);
  }

  /**
   * Delete a guide (admin only)
   */
  static async deleteGuide(id: string): Promise<{ message: string }> {
    const response = await api.delete<StandardResponse<{ message: string }> | ErrorResponse>(`/guides/${id}`);
    return extractApiData<{ message: string }>(response);
  }

  /**
   * Get all guides without pagination (for simple lists)
   */
  static async getAllGuides(): Promise<Guide[]> {
    const allGuides: Guide[] = [];
    let page = 1;
    const perPage = 100; // Maximum allowed by API
    
    while (true) {
      try {
        const response = await this.getGuides({ 
          page, 
          per_page: perPage 
        });
        
        // Handle case where guides field might be undefined
        const guides = response?.guides || [];
        if (!Array.isArray(guides)) {
          console.warn('Expected guides to be an array, got:', typeof guides);
          break;
        }
        
        allGuides.push(...guides);
        
        // If we got fewer items than requested, we've reached the end
        if (guides.length < perPage) {
          break;
        }
        
        page++;
      } catch (error) {
        console.error('Error fetching guides page', page, ':', error);
        // Return what we have so far instead of crashing
        break;
      }
    }
    
    return allGuides;
  }
}

// Legacy export for backward compatibility
export const dependencyApi = {
  getDependencies: (filters?: GuideFilters) => GuidesApi.getGuides(filters),
  getDependency: (id: string) => GuidesApi.getGuide(id),
  getDependencyByPlatform: (platformName: string) => GuidesApi.getGuideByPlatform(platformName),
  createDependency: (data: GuideCreate) => GuidesApi.createGuide(data),
  updateDependency: (id: string, data: GuideUpdate) => GuidesApi.updateGuide(id, data),
  deleteDependency: (id: string) => GuidesApi.deleteGuide(id),
  getAllDependencies: () => GuidesApi.getAllGuides()
};

// Legacy interfaces for backward compatibility
export interface Dependency extends Guide {}
export interface DependencyCreate extends GuideCreate {}
export interface DependencyUpdate extends GuideUpdate {}
export interface DependencyListResponse extends GuideListResponse {
  dependencies: Guide[]; // Map guides to dependencies for backward compatibility
}
export interface DependencyFilters extends GuideFilters {}
