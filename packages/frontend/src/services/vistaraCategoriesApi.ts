import api from '@/services/authApi'
import { extractApiData } from '@/utils/apiUtils'
import type { StandardResponse, ErrorResponse } from '@/types/api'

export interface VistaraCategory {
  id: string
  name: string
  description?: string
  color: string
  icon_name?: string
  display_order: number
  is_system: boolean
  created_at: string
  updated_at?: string
}

export interface CreateVistaraCategoryData {
  name: string
  description?: string
  color: string
  icon_name?: string
  display_order?: number
}

export interface UpdateVistaraCategoryData {
  name?: string
  description?: string
  color?: string
  icon_name?: string
  display_order?: number
}

export class VistaraCategoriesApi {
  static async getCategories(): Promise<VistaraCategory[]> {
    const response = await api.get<StandardResponse<VistaraCategory[]> | ErrorResponse>('/vistara/categories/')
    return extractApiData<VistaraCategory[]>(response)
  }

  static async createCategory(data: CreateVistaraCategoryData): Promise<VistaraCategory> {
    const response = await api.post<StandardResponse<VistaraCategory> | ErrorResponse>('/vistara/categories/', data)
    return extractApiData<VistaraCategory>(response)
  }

  static async updateCategory(id: string, data: UpdateVistaraCategoryData): Promise<VistaraCategory> {
    const response = await api.put<StandardResponse<VistaraCategory> | ErrorResponse>(`/vistara/categories/${id}`, data)
    return extractApiData<VistaraCategory>(response)
  }

  static async deleteCategory(id: string): Promise<{ id: string }> {
    const response = await api.delete<StandardResponse<{ id: string }> | ErrorResponse>(`/vistara/categories/${id}`)
    return extractApiData<{ id: string }>(response)
  }
}
