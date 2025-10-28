/** Main CortexDB client */

import { HTTPClient } from "../http/client";
import { CollectionsAPI } from "../collections/api";
import { RecordsAPI } from "../records/api";
import { parseConnectionString } from "../utils/connection-string";

export interface CortexClientOptions {
  baseUrl?: string;
  apiKey?: string;
  timeout?: number;
}

export class CortexClient {
  private http: HTTPClient;
  public collections: CollectionsAPI;
  public records: RecordsAPI;

  /**
   * Create a new CortexDB client
   * 
   * @param options - Configuration options or connection string
   * 
   * @example
   * ```typescript
   * // Using options object
   * const client = new CortexClient({
   *   baseUrl: 'http://localhost:8000',
   *   apiKey: 'my-key'
   * });
   * 
   * // Using connection string
   * const client = new CortexClient('cortexdb://my-key@localhost:8000');
   * ```
   */
  constructor(options: CortexClientOptions | string = {}) {
    let baseUrl: string;
    let apiKey: string | undefined;
    let timeout: number;

    // Handle connection string
    if (typeof options === 'string') {
      const parsed = parseConnectionString(options);
      baseUrl = parsed.baseUrl;
      apiKey = parsed.apiKey;
      timeout = 30000;
    } else {
      // Handle options object
      baseUrl = options.baseUrl || "http://localhost:8000";
      apiKey = options.apiKey;
      timeout = options.timeout || 30000;
    }

    this.http = new HTTPClient(baseUrl, apiKey, timeout);
    this.collections = new CollectionsAPI(this.http);
    this.records = new RecordsAPI(this.http);
  }

  /**
   * Check if the connection to CortexDB is working
   */
  async health(): Promise<{ status: string }> {
    return this.http.get("/health");
  }

  /**
   * Shorthand for health check that returns boolean
   */
  async healthcheck(): Promise<boolean> {
    try {
      const response = await this.health();
      return response.status === "ok";
    } catch {
      return false;
    }
  }

  /**
   * Close the client (cleanup if needed)
   */
  async close(): Promise<void> {
    // Future: cleanup connections, cancel pending requests, etc.
  }
}
