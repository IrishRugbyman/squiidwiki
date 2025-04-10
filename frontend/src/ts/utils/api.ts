import { ApiResponse } from '../types';

/**
 * API utility functions for making requests to the backend
 */

/**
 * Generic fetch function with type safety
 */
async function fetchApi<T>(
  url: string, 
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        error: data.detail || data.message || 'An error occurred',
      };
    }
    
    return {
      success: true,
      data: data as T,
    };
  } catch (error) {
    console.error('API request failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unknown error occurred',
    };
  }
}

/**
 * GET request
 */
export async function get<T>(url: string): Promise<ApiResponse<T>> {
  return fetchApi<T>(url);
}

/**
 * POST request with typed request body
 */
export async function post<T, R = any>(url: string, data: R): Promise<ApiResponse<T>> {
  return fetchApi<T>(url, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * PUT request with typed request body
 */
export async function put<T, R = any>(url: string, data: R): Promise<ApiResponse<T>> {
  return fetchApi<T>(url, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * DELETE request
 */
export async function del<T>(url: string): Promise<ApiResponse<T>> {
  return fetchApi<T>(url, {
    method: 'DELETE',
  });
}

/**
 * Form data POST for file uploads
 */
export async function postFormData<T>(url: string, formData: FormData): Promise<ApiResponse<T>> {
  return fetchApi<T>(url, {
    method: 'POST',
    headers: {}, // Let the browser set the correct Content-Type with boundary
    body: formData,
  });
} 