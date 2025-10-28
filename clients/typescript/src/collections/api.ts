/**
 * Collections API for CortexDB
 * 
 * Provides methods to create, read, update, and delete collections.
 * Collections define the schema and structure for records.
 */

import { Collection, FieldDefinition, CollectionConfig } from "../types";
import { HTTPClient } from "../http/client";

/**
 * API for managing CortexDB collections
 */
export class CollectionsAPI {
  /**
   * Create a new CollectionsAPI instance
   * 
   * @param http - HTTP client for making requests
   */
  constructor(private http: HTTPClient) {}

  /**
   * List all collections in the database
   * 
   * @returns Array of all collections
   * @example
   * ```typescript
   * const collections = await client.collections.list();
   * console.log(`Found ${collections.length} collections`);
   * ```
   */
  async list(): Promise<Collection[]> {
    return this.http.get<Collection[]>("/collections");
  }

  /**
   * Get a specific collection by name
   * 
   * @param name - Name of the collection to retrieve
   * @returns Collection details including schema
   * @throws {CortexDBNotFoundError} If collection doesn't exist
   * @example
   * ```typescript
   * const collection = await client.collections.get('my_collection');
   * console.log(collection.fields);
   * ```
   */
  async get(name: string): Promise<Collection> {
    return this.http.get<Collection>(`/collections/${name}`);
  }

  /**
   * Create a new collection with the specified schema
   * 
   * @param name - Name for the new collection
   * @param fields - Array of field definitions
   * @param embedding_provider - Optional embedding provider ID (required if any field has vectorize=true)
   * @returns Created collection details
   * @throws {CortexDBValidationError} If schema is invalid or embedding provider is missing when required
   * @example
   * ```typescript
   * const collection = await client.collections.create('documents', [
   *   { name: 'title', type: FieldType.STRING },
   *   { name: 'content', type: FieldType.STRING, vectorize: true }
   * ], 'embedding-provider-id');
   * ```
   */
  async create(
    name: string,
    fields: FieldDefinition[],
    embedding_provider?: string
  ): Promise<Collection> {
    const payload: any = { name, fields };
    if (embedding_provider) {
      payload.config = { embedding_provider_id: embedding_provider };
    }
    return this.http.post<Collection>("/collections", payload);
  }

  /**
   * Update an existing collection's schema
   * 
   * @param name - Name of the collection to update
   * @param fields - New field definitions
   * @returns Updated collection details
   * @throws {CortexDBNotFoundError} If collection doesn't exist
   * @example
   * ```typescript
   * const updated = await client.collections.update('documents', [
   *   { name: 'title', type: FieldType.STRING },
   *   { name: 'description', type: FieldType.STRING }
   * ]);
   * ```
   */
  async update(name: string, fields: FieldDefinition[]): Promise<Collection> {
    return this.http.put<Collection>(`/collections/${name}`, { fields });
  }

  /**
   * Delete a collection and all its records
   * 
   * @param name - Name of the collection to delete
   * @throws {CortexDBNotFoundError} If collection doesn't exist
   * @example
   * ```typescript
   * await client.collections.delete('old_collection');
   * ```
   */
  async delete(name: string): Promise<void> {
    await this.http.delete(`/collections/${name}`);
  }
}
