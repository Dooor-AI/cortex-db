# CortexDB TypeScript SDK

Official TypeScript/JavaScript client for CortexDB.

## What is CortexDB?

CortexDB is a multi-modal RAG (Retrieval Augmented Generation) platform that combines traditional database capabilities with vector search and advanced document processing. It enables you to:

- Store structured and unstructured data in a unified database
- Automatically extract text from documents (PDF, DOCX, XLSX) using Docling
- Generate embeddings for semantic search using various providers (OpenAI, Gemini, etc.)
- Perform hybrid search combining filters with vector similarity
- Build RAG applications with automatic chunking and vectorization

CortexDB handles the complex infrastructure of vector databases (Qdrant), object storage (MinIO), and traditional databases (PostgreSQL) behind a simple API.

## Features

- **Multi-modal document processing**: Upload PDFs, DOCX, XLSX files and automatically extract text with OCR fallback
- **Semantic search**: Vector-based search using embeddings from OpenAI, Gemini, or custom providers
- **Automatic chunking**: Smart text splitting optimized for RAG applications
- **Flexible schema**: Define collections with typed fields (string, number, boolean, file, array)
- **Hybrid queries**: Combine exact filters with semantic search
- **Storage control**: Choose where each field is stored (PostgreSQL, Qdrant, MinIO)
- **Type-safe**: Full TypeScript support with comprehensive type definitions
- **Modern API**: Async/await using native fetch (Node.js 18+)

## Installation

```bash
npm install @dooor-ai/cortexdb
```

Or with yarn:

```bash
yarn add @dooor-ai/cortexdb
```

Or with pnpm:

```bash
pnpm add @dooor-ai/cortexdb
```

## Quick Start

```typescript
import { CortexClient, FieldType } from '@dooor-ai/cortexdb';

async function main() {
  const client = new CortexClient({
    baseUrl: 'http://localhost:8000'
  });

  // Create a collection with vectorization enabled
  await client.collections.create(
    'documents',
    [
      { name: 'title', type: FieldType.STRING },
      { name: 'content', type: FieldType.STRING, vectorize: true }
    ],
    'your-embedding-provider-id'  // Required when vectorize=true
  );

  // Create a record
  const record = await client.records.create('documents', {
    title: 'Introduction to AI',
    content: 'Artificial intelligence is transforming how we build software...'
  });

  // Semantic search - finds relevant content by meaning, not just keywords
  const results = await client.records.search(
    'documents',
    'How is AI changing software development?',
    undefined,
    10
  );

  results.results.forEach(result => {
    console.log(`Score: ${result.score.toFixed(4)}`);
    console.log(`Title: ${result.record.data.title}`);
    console.log(`Content: ${result.record.data.content}\n`);
  });

  await client.close();
}

main();
```

## Usage

### Initialize Client

```typescript
import { CortexClient } from '@dooor-ai/cortexdb';

// Using connection string (recommended)
const client = new CortexClient('cortexdb://localhost:8000');

// With API key
const client = new CortexClient('cortexdb://my-api-key@localhost:8000');

// Production (HTTPS auto-detected)
const client = new CortexClient('cortexdb://my-key@api.cortexdb.com');

// Using options object (alternative)
const client = new CortexClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key',
  timeout: 60000  // 60 seconds
});
```

**Connection String Format:**  
`cortexdb://[api_key@]host[:port]`

Benefits:
- Single string configuration
- Easy to store in environment variables
- Familiar pattern (like PostgreSQL, MongoDB, Redis)
- Auto-detects HTTP vs HTTPS

### Collections

Collections define the schema for your data. Each collection can have multiple fields with different types and storage options.

```typescript
import { FieldType, StoreLocation } from '@dooor-ai/cortexdb';

// Create collection with vectorization
const collection = await client.collections.create(
  'articles',
  [
    {
      name: 'title',
      type: FieldType.STRING
    },
    {
      name: 'content',
      type: FieldType.STRING,
      vectorize: true  // Enable semantic search on this field
    },
    {
      name: 'year',
      type: FieldType.NUMBER,
      store_in: [StoreLocation.POSTGRES, StoreLocation.QDRANT_PAYLOAD]
    }
  ],
  'embedding-provider-id'  // Required when any field has vectorize=true
);

// List collections
const collections = await client.collections.list();

// Get collection schema
const schema = await client.collections.get('articles');

// Delete collection and all its records
await client.collections.delete('articles');
```

### Records

Records are the actual data stored in collections. They must match the collection schema.

```typescript
// Create record
const record = await client.records.create('articles', {
  title: 'Machine Learning Basics',
  content: 'Machine learning is a subset of AI that focuses on learning from data...',
  year: 2024
});

// Get record by ID
const fetched = await client.records.get('articles', record.id);

// Update record
const updated = await client.records.update('articles', record.id, {
  year: 2025
});

// Delete record
await client.records.delete('articles', record.id);

// List records with pagination
const results = await client.records.list('articles', {
  limit: 10,
  offset: 0
});
```

### Semantic Search

Semantic search finds records by meaning, not just exact keyword matches. It uses vector embeddings to understand context.

```typescript
// Basic semantic search
const results = await client.records.search(
  'articles',
  'machine learning fundamentals',
  undefined,
  10
);

// Search with filters - combine semantic search with exact matches
const filteredResults = await client.records.search(
  'articles',
  'neural networks',
  {
    year: 2024,
    category: 'AI'
  },
  5
);

// Process results - ordered by relevance score
filteredResults.results.forEach(result => {
  console.log(`Score: ${result.score.toFixed(4)}`);  // Higher = more relevant
  console.log(`Title: ${result.record.data.title}`);
  console.log(`Year: ${result.record.data.year}`);
});
```

### Working with Files

CortexDB can process documents and automatically extract text for vectorization.

```typescript
// Create collection with file field
await client.collections.create(
  'documents',
  [
    { name: 'title', type: FieldType.STRING },
    {
      name: 'document',
      type: FieldType.FILE,
      vectorize: true  // Extract text and create embeddings
    }
  ],
  'embedding-provider-id'
);

// Note: File upload support is currently available in the REST API
// TypeScript SDK file upload will be added in a future version
```

### Filter Operators

```typescript
// Exact match filters
const results = await client.records.list('articles', {
  filters: {
    category: 'technology',
    published: true,
    year: 2024
  }
});

// Combine multiple filters
const filtered = await client.records.list('articles', {
  filters: {
    year: 2024,
    category: 'AI',
    author: 'John Doe'
  },
  limit: 20
});
```

## Error Handling

The SDK provides specific error types for different failure scenarios.

```typescript
import {
  CortexDBError,
  CortexDBNotFoundError,
  CortexDBValidationError,
  CortexDBConnectionError,
  CortexDBTimeoutError
} from '@dooor-ai/cortexdb';

try {
  const record = await client.records.get('articles', 'invalid-id');
} catch (error) {
  if (error instanceof CortexDBNotFoundError) {
    console.log('Record not found');
  } else if (error instanceof CortexDBValidationError) {
    console.log('Invalid data:', error.message);
  } else if (error instanceof CortexDBConnectionError) {
    console.log('Connection failed:', error.message);
  } else if (error instanceof CortexDBTimeoutError) {
    console.log('Request timed out:', error.message);
  } else if (error instanceof CortexDBError) {
    console.log('General error:', error.message);
  }
}
```

## Examples

Check the [`examples/`](./examples) directory for complete working examples:

- [`quickstart.ts`](./examples/quickstart.ts) - Complete walkthrough of SDK features
- [`search.ts`](./examples/search.ts) - Semantic search with filters and providers
- [`basic.ts`](./examples/basic.ts) - Basic CRUD operations

Run examples:

```bash
npx ts-node -O '{"module":"commonjs"}' examples/quickstart.ts
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/cortexdb
cd cortexdb/clients/typescript

# Install dependencies
npm install

# Build
npm run build
```

### Scripts

```bash
# Build TypeScript
npm run build

# Build in watch mode
npm run build:watch

# Clean build artifacts
npm run clean

# Lint code
npm run lint

# Format code
npm run format
```

## Requirements

- Node.js >= 18.0.0 (for native fetch support)
- CortexDB gateway running locally or remotely
- Embedding provider configured (OpenAI, Gemini, etc.) if using vectorization

## Architecture

CortexDB integrates multiple technologies:

- **PostgreSQL**: Stores structured data and metadata
- **Qdrant**: Vector database for semantic search
- **MinIO**: Object storage for files
- **Docling**: Advanced document processing and text extraction

The SDK abstracts this complexity into a simple, unified API.

## License

MIT License - see [LICENSE](./LICENSE) for details.

## Related

- [CortexDB Python SDK](../python) - Python client for CortexDB
- [CortexDB Documentation](../../docs) - Complete platform documentation
