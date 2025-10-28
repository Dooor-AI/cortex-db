# CortexDB Python SDK

Official Python client for CortexDB.

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
- **Automatic chunking**: Smart text splitting optimized for RAG applications using Docling
- **Flexible schema**: Define collections with typed fields and storage locations
- **Hybrid queries**: Combine exact filters with semantic search
- **File upload**: Direct file upload with automatic text extraction and vectorization
- **Type-safe**: Full type hints and Pydantic models for validation
- **Async/await**: Built with httpx for high-performance async operations

## Installation

```bash
pip install cortexdb
```

Or with Poetry:

```bash
poetry add cortexdb
```

## Quick Start

```python
import asyncio
from cortexdb import CortexClient, FieldDefinition, FieldType

async def main():
    async with CortexClient("http://localhost:8000") as client:
        # Create a collection with vectorization enabled
        await client.collections.create(
            name="documents",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="content", type=FieldType.TEXT, vectorize=True)
            ],
            embedding_provider="your-provider-id"  # Required when vectorize=True
        )

        # Create a record
        record = await client.records.create(
            collection="documents",
            data={
                "title": "Introduction to AI",
                "content": "Artificial intelligence is transforming how we build software..."
            }
        )

        # Semantic search - finds relevant content by meaning
        results = await client.records.query(
            collection="documents",
            query="How is AI changing software development?",
            limit=10
        )

        for result in results:
            print(f"Score: {result.score:.4f}")
            print(f"Title: {result.data['title']}")
            print(f"Content: {result.data['content']}\n")

asyncio.run(main())
```

## Usage

### Initialize Client

```python
from cortexdb import CortexClient

# Using connection string (recommended)
client = CortexClient("cortexdb://localhost:8000")

# With API key
client = CortexClient("cortexdb://my-api-key@localhost:8000")

# Production (HTTPS auto-detected)
client = CortexClient("cortexdb://my-key@api.cortexdb.com")

# Using traditional URL (alternative)
client = CortexClient("http://localhost:8000", api_key="your-key")

# Custom timeout
client = CortexClient("cortexdb://localhost:8000", timeout=60.0)

# Use with context manager (recommended)
async with CortexClient("cortexdb://my-key@localhost:8000") as client:
    # Your code here
    pass
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

```python
from cortexdb import FieldDefinition, FieldType, StoreLocation

# Create collection with vectorization
schema = await client.collections.create(
    name="articles",
    fields=[
        FieldDefinition(
            name="title",
            type=FieldType.STRING
        ),
        FieldDefinition(
            name="content",
            type=FieldType.TEXT,
            vectorize=True  # Enable semantic search on this field
        ),
        FieldDefinition(
            name="year",
            type=FieldType.INT,
            store_in=[StoreLocation.POSTGRES, StoreLocation.QDRANT_PAYLOAD]
        )
    ],
    embedding_provider="provider-id"  # Required when vectorize=True
)

# List collections
collections = await client.collections.list()

# Get collection schema
schema = await client.collections.get("articles")

# Delete collection and all its records
await client.collections.delete("articles")
```

### Records

Records are the actual data stored in collections. They must match the collection schema.

```python
# Create record
record = await client.records.create(
    collection="articles",
    data={
        "title": "Machine Learning Basics",
        "content": "Introduction to ML concepts...",
        "year": 2024
    }
)

# Get record by ID
record = await client.records.get("articles", record_id="abc-123")

# Update record
updated = await client.records.update(
    collection="articles",
    record_id="abc-123",
    data={"year": 2025}
)

# Delete record
await client.records.delete("articles", record_id="abc-123")
```

### Semantic Search

Semantic search finds records by meaning, not just exact keyword matches. It uses vector embeddings to understand context.

```python
# Basic semantic search
results = await client.records.query(
    collection="articles",
    query="machine learning fundamentals",
    limit=10
)

# Search with filters - combine semantic search with exact matches
results = await client.records.query(
    collection="articles",
    query="neural networks",
    limit=5,
    filters={
        "year": {"$gte": 2023},  # Year >= 2023
        "category": "AI"          # Exact match
    }
)

# Process results - ordered by relevance score
for result in results:
    print(f"Score: {result.score:.4f}")  # Higher = more relevant
    print(f"Title: {result.data['title']}")
    print(f"Year: {result.data['year']}")
```

### File Upload

CortexDB can process documents and automatically extract text for vectorization using Docling.

```python
from pathlib import Path

# Create collection with file field
await client.collections.create(
    name="documents",
    fields=[
        FieldDefinition(name="title", type=FieldType.STRING),
        FieldDefinition(
            name="pdf",
            type=FieldType.FILE,
            vectorize=True  # Extract text and create embeddings
        )
    ],
    embedding_provider="provider-id"
)

# Upload file from path
record = await client.records.create(
    collection="documents",
    data={"title": "Annual Report"},
    files={"pdf": Path("/path/to/file.pdf")}
)

# Upload file from bytes
record = await client.records.create(
    collection="documents",
    data={"title": "Contract"},
    files={"pdf": file_bytes}
)

# Get vectorized chunks
chunks = await client.records.get_vectors("documents", record.id)
for chunk in chunks:
    print(f"Field: {chunk.field}")
    print(f"Chunk {chunk.chunk_index}: {chunk.text[:100]}...")
```

### Filter Operators

```python
# Comparison operators
filters = {
    "year": {"$gte": 2020},    # Greater than or equal
    "score": {"$lte": 100},    # Less than or equal
    "views": {"$gt": 1000},    # Greater than
    "price": {"$lt": 50},      # Less than
}

# Exact match
filters = {
    "category": "technology",
    "published": True
}

# Combine filters
filters = {
    "year": {"$gte": 2020, "$lte": 2024},
    "category": "AI"
}
```

## Error Handling

The SDK provides specific error types for different failure scenarios.

```python
from cortexdb import (
    CortexDBError,
    CortexDBNotFoundError,
    CortexDBValidationError,
    CortexDBConnectionError
)

try:
    record = await client.records.get("articles", "invalid-id")
except CortexDBNotFoundError as e:
    print(f"Record not found: {e.message}")
except CortexDBValidationError as e:
    print(f"Validation error: {e.message}")
except CortexDBConnectionError as e:
    print(f"Connection failed: {e.message}")
except CortexDBError as e:
    print(f"General error: {e.message}")
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/cortexdb
cd cortexdb/clients/python

# Install with Poetry
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# With coverage
poetry run pytest --cov=cortexdb --cov-report=html

# Run specific test
poetry run pytest tests/test_client.py::test_create_collection
```

### Code Quality

```bash
# Format with Black
poetry run black cortexdb tests

# Lint with Ruff
poetry run ruff check cortexdb

# Type check with mypy
poetry run mypy cortexdb
```

## Examples

Check the [`examples/`](./examples) directory for complete working examples:

- [`quickstart.py`](./examples/quickstart.py) - Complete walkthrough of SDK features
- [`file_upload.py`](./examples/file_upload.py) - Document upload and vectorization

Run examples:

```bash
poetry run python examples/quickstart.py
```

## Requirements

- Python 3.8+
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

MIT License - see [LICENSE](../../LICENSE) for details.

## Related

- [CortexDB TypeScript SDK](../typescript) - TypeScript/JavaScript client for CortexDB
- [CortexDB Documentation](../../docs) - Complete platform documentation
