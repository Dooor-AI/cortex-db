/**
 * Parse CortexDB connection strings
 * 
 * Format: cortexdb://[api_key@]host[:port]
 * 
 * Examples:
 * - cortexdb://localhost:8000
 * - cortexdb://my_key@localhost:8000
 * - cortexdb://my_key@api.cortexdb.com
 */

export interface ParsedConnection {
  baseUrl: string;
  apiKey?: string;
}

/**
 * Parse a CortexDB connection string
 * 
 * @param connectionString - Connection string in format cortexdb://[api_key@]host[:port]
 * @returns Parsed connection options
 * @throws Error if connection string is invalid
 * 
 * @example
 * ```typescript
 * parseConnectionString('cortexdb://localhost:8000')
 * // { baseUrl: 'http://localhost:8000' }
 * 
 * parseConnectionString('cortexdb://my_key@localhost:8000')
 * // { baseUrl: 'http://localhost:8000', apiKey: 'my_key' }
 * 
 * parseConnectionString('cortexdb://key@api.cortexdb.com:443')
 * // { baseUrl: 'https://api.cortexdb.com:443', apiKey: 'key' }
 * ```
 */
export function parseConnectionString(connectionString: string): ParsedConnection {
  // Remove cortexdb:// prefix
  if (!connectionString.startsWith('cortexdb://')) {
    throw new Error('Connection string must start with "cortexdb://"');
  }

  const withoutProtocol = connectionString.slice('cortexdb://'.length);
  
  // Split by @ to separate api_key from host
  let apiKey: string | undefined;
  let hostPart: string;

  if (withoutProtocol.includes('@')) {
    const parts = withoutProtocol.split('@');
    if (parts.length !== 2) {
      throw new Error('Invalid connection string format');
    }
    apiKey = parts[0];
    hostPart = parts[1];
  } else {
    hostPart = withoutProtocol;
  }

  // Parse host and port
  let host: string;
  let port: string | undefined;
  
  if (hostPart.includes(':')) {
    const hostPortParts = hostPart.split(':');
    host = hostPortParts[0];
    port = hostPortParts[1];
  } else {
    host = hostPart;
  }

  // Determine protocol (https for port 443 or production domains, http otherwise)
  const isSecure = port === '443' || 
                   host.includes('cortexdb.com') || 
                   (!host.includes('localhost') && !host.startsWith('127.'));
  
  const protocol = isSecure ? 'https' : 'http';
  
  // Build base URL
  let baseUrl = `${protocol}://${host}`;
  if (port && !(port === '443' && isSecure) && !(port === '80' && !isSecure)) {
    baseUrl += `:${port}`;
  }

  return {
    baseUrl,
    apiKey
  };
}

