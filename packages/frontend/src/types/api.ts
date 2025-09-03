// Standardized API response types to match backend format

export interface StandardResponse<T = any> {
  status: 'success' | 'error'
  data?: T
  message: string
  timestamp: string
  request_id: string
}

export interface ErrorResponse {
  status: 'error'
  error: string
  message: string
  code: string
  details?: any
  timestamp: string
  request_id: string
  path?: string
}

export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  size: number
  total_pages: number
}

// Type guard to check if response is an error
export function isErrorResponse(response: any): response is ErrorResponse {
  return response.status === 'error'
}

// Type guard to check if response is successful
export function isSuccessResponse<T>(response: any): response is StandardResponse<T> {
  return response.status === 'success'
}