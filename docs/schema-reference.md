# Schema Reference

Each collection is defined with a YAML document containing the following sections:

- `name`: snake_case identifier for the collection.
- `description`: optional text.
- `fields`: list of field definitions.
- `config`: optional collection configuration overrides.

## Field Attributes

| Key | Type | Description |
| --- | --- | --- |
| `name` | string | Unique field identifier (snake_case). |
| `type` | enum | One of `string`, `text`, `int`, `float`, `boolean`, `date`, `datetime`, `enum`, `array`, `file`, `json`. |
| `required` | bool | If true, field must be supplied on insert. |
| `indexed` | bool | Creates a Postgres index (for non-array fields). |
| `unique` | bool | Adds a uniqueness constraint (string/int/float). |
| `filterable` | bool | Adds filter metadata to Qdrant payload. |
| `vectorize` | bool | Automatically embed content with Gemini. |
| `store_in` | list | Any of `postgres`, `qdrant`, `qdrant_payload`, `minio`. Defaults to `postgres`. |
| `default` | any | Default value when omitted. |
| `values` | list | Allowed values for `enum` type. |
| `extract_config` | object | File extraction configuration (see below). |

### Array Fields

Array fields describe nested objects via their own `schema` array. Items are stored in a dedicated relational table with a foreign key to the parent record.

### File Fields

`extract_config` supports:

- `extract_text` (bool): extract text payload.
- `ocr_if_needed` (bool): fallback OCR via Gemini for scanned PDFs or images.
- `chunk_size`/`chunk_overlap`: custom chunking overrides.

### Collection Config

```
config:
  embedding_model: models/text-embedding-004
  chunk_size: 800
  chunk_overlap: 100
```

Values fall back to environment defaults (`DEFAULT_CHUNK_SIZE`, `DEFAULT_CHUNK_OVERLAP`).
