from __future__ import annotations

from pathlib import Path
from typing import Any, Union

import yaml

from ..models.schema import CollectionSchema
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SchemaParseError(RuntimeError):
    """Exception raised when a schema cannot be parsed."""


def parse_schema(yaml_content: Union[str, bytes, dict[str, Any]]) -> CollectionSchema:
    """
    Parse a YAML schema definition into a CollectionSchema.

    Args:
        yaml_content: YAML string, bytes, or already parsed dictionary.

    Returns:
        CollectionSchema: Parsed schema object.
    """
    if isinstance(yaml_content, (str, bytes)):
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as exc:  # pragma: no cover - defensive logging
            logger.exception("failed to parse YAML schema", extra={"error": str(exc)})
            raise SchemaParseError("Failed to parse YAML schema") from exc
    elif isinstance(yaml_content, dict):
        data = yaml_content
    else:
        raise TypeError("yaml_content must be str, bytes, or dict")

    if not isinstance(data, dict):
        raise SchemaParseError("Schema root must be a mapping")

    try:
        schema = CollectionSchema.model_validate(data)
    except Exception as exc:
        logger.exception("schema validation error", extra={"error": str(exc)})
        raise SchemaParseError(f"Schema validation error: {exc}") from exc

    return schema


def load_schema_file(path: Union[str, Path]) -> CollectionSchema:
    """Load and parse a schema from a file path."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    content = file_path.read_text(encoding="utf-8")
    return parse_schema(content)
