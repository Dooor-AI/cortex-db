# Changelog

All notable changes to the CortexDB TypeScript SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-28

### Added
- Initial release of CortexDB TypeScript SDK
- Core client with `CortexClient` class
- Collections API (CRUD operations)
- Records API (CRUD operations + semantic search)
- TypeScript type definitions for all models
- Custom error classes for better error handling:
  - `CortexDBError` (base)
  - `CortexDBConnectionError`
  - `CortexDBTimeoutError`
  - `CortexDBNotFoundError`
  - `CortexDBValidationError`
  - `CortexDBAuthenticationError`
  - `CortexDBPermissionError`
  - `CortexDBServerError`
- HTTP client with native `fetch` API (Node.js 18+)
- Support for semantic search with vector embeddings
- Field types: STRING, NUMBER, BOOLEAN, FILE, ARRAY
- Storage location options: POSTGRES, QDRANT_PAYLOAD, MINIO
- Health check methods (`health()`, `healthcheck()`)
- Comprehensive examples:
  - Basic operations
  - Quickstart guide
  - Semantic search
- Full README documentation
- MIT License

### Technical Details
- Built with TypeScript 5.0+
- Requires Node.js >= 18.0.0
- No external dependencies (uses native fetch)
- CommonJS module format
- Full type declarations included

### Known Limitations
- File upload functionality not yet implemented
- No retry logic for failed requests
- No streaming support

## [Unreleased]

### Planned
- File upload support with FormData
- Retry logic with exponential backoff
- Request cancellation support
- Streaming API support
- Batch operations
- More comprehensive test suite

