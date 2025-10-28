/** Records API for CortexDB */

import { CortexRecord, SearchRequest, SearchResponse, QueryParams } from "../types";
import { HTTPClient } from "../http/client";

export class RecordsAPI {
  constructor(private http: HTTPClient) {}

  /**
   * Create a new record
   */
  async create(
    collection: string,
    data: { [key: string]: any },
    files?: { [key: string]: File | Buffer }
  ): Promise<CortexRecord> {
    if (files && Object.keys(files).length > 0) {
      // Handle multipart/form-data for file uploads
      return this.createWithFiles(collection, data, files);
    }
    return this.http.post<CortexRecord>(`/collections/${collection}/records`, data);
  }

  /**
   * Get a record by ID
   */
  async get(collection: string, id: string): Promise<CortexRecord> {
    return this.http.get<CortexRecord>(`/collections/${collection}/records/${id}`);
  }

  /**
   * List records in a collection
   */
  async list(
    collection: string,
    params?: QueryParams
  ): Promise<{ records: CortexRecord[]; total: number }> {
    // Use POST to query endpoint with filters
    const response = await this.http.post<{ records: CortexRecord[]; total: number }>(
      `/collections/${collection}/query`,
      params || {}
    );
    return response;
  }

  /**
   * Update a record
   */
  async update(
    collection: string,
    id: string,
    data: { [key: string]: any }
  ): Promise<CortexRecord> {
    return this.http.put<CortexRecord>(
      `/collections/${collection}/records/${id}`,
      data
    );
  }

  /**
   * Delete a record
   */
  async delete(collection: string, id: string): Promise<void> {
    await this.http.delete(`/collections/${collection}/records/${id}`);
  }

  /**
   * Semantic search
   */
  async search(
    collection: string,
    query: string,
    filters?: { [key: string]: any },
    limit: number = 10
  ): Promise<SearchResponse> {
    const request: SearchRequest = { query, filters, limit };
    return this.http.post<SearchResponse>(
      `/collections/${collection}/search`,
      request
    );
  }

  /**
   * Create record with files
   */
  private async createWithFiles(
    collection: string,
    data: { [key: string]: any },
    files: { [key: string]: File | Buffer }
  ): Promise<CortexRecord> {
    // For file uploads, we need to use FormData
    // This is a simplified version - in production you'd use form-data library
    throw new Error("File uploads not yet implemented in TypeScript SDK");
  }
}
