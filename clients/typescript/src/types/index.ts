/** Core types for CortexDB TypeScript SDK */

export type FieldType = "string" | "number" | "boolean" | "file" | "array";

/**
 * Storage location options for fields
 */
export enum StoreLocation {
  POSTGRES = "postgres",
  QDRANT_PAYLOAD = "qdrant_payload",
  MINIO = "minio",
}

export interface FieldDefinition {
  name: string;
  type: FieldType;
  vectorize?: boolean;
  required?: boolean;
  store_in?: StoreLocation[];
}

export interface CollectionConfig {
  embedding_provider_id?: string;
}

export interface Collection {
  name: string;
  fields: FieldDefinition[];
  config?: CollectionConfig;
}

export interface CortexRecord {
  id: string;
  data: { [key: string]: any };
  created_at?: string;
  updated_at?: string;
}

export interface SearchResult {
  record: CortexRecord;
  score: number;
  highlights?: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  took_ms: number;
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
}

export interface QueryParams {
  filters?: { [key: string]: any };
  limit?: number;
  offset?: number;
}

export interface SearchRequest {
  query: string;
  filters?: { [key: string]: any };
  limit?: number;
}

export interface EmbeddingProvider {
  id: string;
  name: string;
  provider: string;
  enabled: boolean;
}

export interface Database {
  name: string;
}

export interface CortexError {
  detail: string;
}

/**
 * Configuration for text extraction from files
 */
export interface ExtractConfig {
  chunk_size?: number;
  chunk_overlap?: number;
  ocr_if_needed?: boolean;
}

/**
 * Vector chunk representing a portion of text and its embedding
 */
export interface VectorChunk {
  id: string;
  text: string;
  metadata?: { [key: string]: any };
}

/**
 * Request for querying records with filters
 */
export interface QueryRequest {
  filters?: { [key: string]: any };
  limit?: number;
  offset?: number;
}

/**
 * Complete collection schema
 */
export interface CollectionSchema {
  name: string;
  database?: string;
  fields: FieldDefinition[];
  config?: CollectionConfig;
  created_at?: string;
  updated_at?: string;
}
