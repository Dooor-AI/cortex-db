/**
 * HTTP client for CortexDB API
 * 
 * Handles all HTTP requests with automatic error handling,
 * timeout management, and status code mapping to specific exceptions.
 */

import { CortexError } from "../types";
import {
  CortexDBConnectionError,
  CortexDBTimeoutError,
  CortexDBNotFoundError,
  CortexDBValidationError,
  CortexDBAuthenticationError,
  CortexDBPermissionError,
  CortexDBServerError,
} from "../exceptions";

/**
 * HTTP client for making requests to CortexDB API
 */
export class HTTPClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;

  /**
   * Create a new HTTP client
   * 
   * @param baseUrl - Base URL of the CortexDB gateway
   * @param apiKey - Optional API key for authentication
   * @param timeout - Request timeout in milliseconds (default: 30000)
   */
  constructor(baseUrl: string, apiKey?: string, timeout: number = 30000) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.timeout = timeout;
  }

  /**
   * Make a GET request
   * 
   * @param path - API endpoint path
   * @returns Response data
   */
  async get<T>(path: string): Promise<T> {
    return this.request<T>("GET", path);
  }

  /**
   * Make a POST request
   * 
   * @param path - API endpoint path
   * @param body - Request body
   * @returns Response data
   */
  async post<T>(path: string, body?: any): Promise<T> {
    return this.request<T>("POST", path, body);
  }

  /**
   * Make a PUT request
   * 
   * @param path - API endpoint path
   * @param body - Request body
   * @returns Response data
   */
  async put<T>(path: string, body?: any): Promise<T> {
    return this.request<T>("PUT", path, body);
  }

  /**
   * Make a PATCH request
   * 
   * @param path - API endpoint path
   * @param body - Request body
   * @returns Response data
   */
  async patch<T>(path: string, body?: any): Promise<T> {
    return this.request<T>("PATCH", path, body);
  }

  /**
   * Make a DELETE request
   * 
   * @param path - API endpoint path
   * @returns Response data
   */
  async delete<T>(path: string): Promise<T> {
    return this.request<T>("DELETE", path);
  }

  /**
   * Internal method to make HTTP requests
   * 
   * @param method - HTTP method
   * @param path - API endpoint path
   * @param body - Optional request body
   * @returns Response data
   * @throws {CortexDBError} Various error types based on HTTP status codes
   */
  private async request<T>(
    method: string,
    path: string,
    body?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }

    const options: RequestInit = {
      method,
      headers,
    };

    if (body && method !== "GET" && method !== "DELETE") {
      options.body = JSON.stringify(body);
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, { ...options, signal: controller.signal });
      clearTimeout(timeoutId);
      
      const contentType = response.headers.get("content-type");
      let data: any;

      if (contentType && contentType.includes("application/json")) {
        data = await response.json();
      } else {
        const text = await response.text();
        data = text ? { detail: text } : {};
      }

      if (!response.ok) {
        const errorMessage = (data as CortexError).detail || response.statusText;
        
        // Map HTTP status codes to specific exceptions
        switch (response.status) {
          case 400:
            throw new CortexDBValidationError(errorMessage);
          case 401:
            throw new CortexDBAuthenticationError(errorMessage);
          case 403:
            throw new CortexDBPermissionError(errorMessage);
          case 404:
            throw new CortexDBNotFoundError(errorMessage);
          case 408:
            throw new CortexDBTimeoutError(errorMessage);
          case 500:
          case 502:
          case 503:
          case 504:
            throw new CortexDBServerError(errorMessage);
          default:
            throw new CortexDBConnectionError(errorMessage);
        }
      }

      return data as T;
    } catch (error: any) {
      if (error.name === "AbortError") {
        throw new CortexDBTimeoutError(`Request timed out after ${this.timeout}ms`);
      }
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        throw new CortexDBConnectionError(`Failed to connect to ${url}`);
      }
      throw error;
    }
  }
}