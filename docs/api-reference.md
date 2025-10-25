# API Reference

Base URL: `http://localhost:8000`

## Collections

- `POST /collections` — create collection from YAML payload.
- `GET /collections` — list collections and schemas.
- `GET /collections/{name}` — fetch schema details.
- `DELETE /collections/{name}` — drop collection and associated metadata.

## Records

- `POST /collections/{name}/records` — insert record (JSON or multipart).
- `GET /collections/{name}/records/{id}` — retrieve record with files and arrays.
- `PATCH /collections/{name}/records/{id}` — partial update of record fields/files.
- `DELETE /collections/{name}/records/{id}` — remove record and associated vectors/files.

## Search & Query

- `POST /collections/{name}/search` — hybrid semantic search.
- `POST /collections/{name}/query` — structured filter query (SQL-like equality/range).

## Files

- `POST /files/upload` — direct file upload to MinIO bucket.
- `GET /files/{collection}/{record_id}/{filename}` — download stored file.

## Health

- `GET /health` — basic service health.
- `GET /health/postgres` — checks Postgres connectivity.
- `GET /health/qdrant` — checks Qdrant connectivity.
- `GET /health/minio` — checks MinIO connectivity.
- `GET /health/all` — aggregated health check.
