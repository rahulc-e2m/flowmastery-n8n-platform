import { AxiosResponse } from 'axios'
import { StandardResponse, ErrorResponse, isErrorResponse, isSuccessResponse } from '@/types/api'

/**
 * Extracts data from standardized API response
 * Handles both success and error responses according to the new API format
 */
export function extractApiData<T>(response: AxiosResponse<StandardResponse<T> | ErrorResponse>): T {
  const data = response.data

  // Handle error responses
  if (isErrorResponse(data)) {
    const error = new Error(data.message)
    // Attach additional error information
    ;(error as any).code = data.code
    ;(error as any).details = data.details
    ;(error as any).requestId = data.request_id
    ;(error as any).status = response.status
    throw error
  }

  // Handle success responses
  if (isSuccessResponse<T>(data)) {
    return data.data as T
  }

  // Fallback for unexpected response format
  throw new Error('Unexpected API response format')
}

/**
 * Extracts the full standardized response (including metadata)
 */
export function extractFullApiResponse<T>(
  response: AxiosResponse<StandardResponse<T> | ErrorResponse>
): StandardResponse<T> {
  const data = response.data

  if (isErrorResponse(data)) {
    const error = new Error(data.message)
    ;(error as any).code = data.code
    ;(error as any).details = data.details
    ;(error as any).requestId = data.request_id
    ;(error as any).status = response.status
    throw error
  }

  if (isSuccessResponse<T>(data)) {
    return data
  }

  throw new Error('Unexpected API response format')
}

/**
 * Creates a standardized error from axios error
 */
export function createApiError(error: any): Error {
  if (error.response?.data) {
    const errorData = error.response.data
    
    // Handle standardized error response
    if (isErrorResponse(errorData)) {
      const apiError = new Error(errorData.message)
      ;(apiError as any).code = errorData.code
      ;(apiError as any).details = errorData.details
      ;(apiError as any).requestId = errorData.request_id
      ;(apiError as any).status = error.response.status
      return apiError
    }
    
    // Handle legacy error format
    if (errorData.detail) {
      return new Error(errorData.detail)
    }
    
    if (errorData.message) {
      return new Error(errorData.message)
    }
  }

  // Fallback to original error
  return error.response?.statusText 
    ? new Error(`${error.response.status}: ${error.response.statusText}`)
    : error
}