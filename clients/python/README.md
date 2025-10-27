# CortexDB Python SDK

Official Python client for CortexDB - Multi-modal RAG Platform.

## Features

- Async/await support with httpx
- Semantic search with vector embeddings
- File upload with automatic text extraction and vectorization
- Type hints for better IDE support
- Pydantic models for data validation
- Context manager support
- Error handling with custom exceptions

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
        # Create a collection
        await client.collections.create(
            name="documents",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="content", type=FieldType.TEXT, vectorize=True)
            ]
        )

        # Create a record
        record = await client.records.create(
            collection="documents",
            data={"title": "Hello", "content": "World"}
        )

        # Semantic search
        results = await client.records.query(
            collection="documents",
            query="hello world",
            limit=10
        )

        for result in results:
            print(f"Score: {result.score:.4f} - {result.data['title']}")

asyncio.run(main())
```

## Usage

### Initialize Client

```python
from cortexdb import CortexClient

# Local development
client = CortexClient("http://localhost:8000")

# With API key
client = CortexClient("https://api.cortexdb.com", api_key="your-key")

# Custom timeout
client = CortexClient("http://localhost:8000", timeout=60.0)
```

### Collections

```python
from cortexdb import FieldDefinition, FieldType, StoreLocation

# Create collection
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
            vectorize=True  # Enable semantic search
        ),
        FieldDefinition(
            name="year",
            type=FieldType.INT,
            store_in=[StoreLocation.POSTGRES, StoreLocation.QDRANT_PAYLOAD]
        )
    ]
)

# List collections
collections = await client.collections.list()

# Get collection
schema = await client.collections.get("articles")

# Delete collection
await client.collections.delete("articles")
```

### Records

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

```python
# Basic search
results = await client.records.query(
    collection="articles",
    query="machine learning fundamentals",
    limit=10
)

# Search with filters
results = await client.records.query(
    collection="articles",
    query="neural networks",
    limit=5,
    filters={
        "year": {"$gte": 2023},  # Year >= 2023
        "category": "AI"          # Exact match
    }
)

# Process results
for result in results:
    print(f"Score: {result.score:.4f}")
    print(f"Title: {result.data['title']}")
    print(f"Year: {result.data['year']}")
```

### File Upload

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
            vectorize=True  # Extract text and vectorize
        )
    ]
)

# Upload file
record = await client.records.create(
    collection="documents",
    data={"title": "Annual Report"},
    files={"pdf": Path("/path/to/file.pdf")}
)

# Or upload bytes
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
    "year": {"$gte": 2020, "$lte": 2024"},
    "category": "AI"
}
```

## Error Handling

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

Check the [`examples/`](./examples) directory for more usage examples:

- [`quickstart.py`](./examples/quickstart.py) - Walkthrough of SDK features
- [`file_upload.py`](./examples/file_upload.py) - File upload and vectorization

Run examples:

```bash
poetry run python examples/quickstart.py
```

## Requirements

- Python 3.8+
- CortexDB gateway running (local or remote)

## License

MIT License - see [LICENSE](../../LICENSE) for details.
