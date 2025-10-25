from __future__ import annotations

import re
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, FieldValidationInfo, field_validator, model_validator


class FieldType(str, Enum):
    STRING = "string"
    TEXT = "text"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ENUM = "enum"
    ARRAY = "array"
    FILE = "file"
    JSON = "json"


class StoreLocation(str, Enum):
    POSTGRES = "postgres"
    QDRANT = "qdrant"
    QDRANT_PAYLOAD = "qdrant_payload"
    MINIO = "minio"


class ExtractConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extract_text: bool = Field(default=True)
    ocr_if_needed: bool = Field(default=True)
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


class FieldDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: FieldType
    description: Optional[str] = None
    required: bool = False
    indexed: bool = False
    unique: bool = False
    filterable: bool = False
    vectorize: bool = False
    default: Optional[Any] = None
    values: Optional[List[Any]] = None
    store_in: List[StoreLocation] = Field(default_factory=lambda: [StoreLocation.POSTGRES])
    schema: Optional[List["FieldDefinition"]] = None
    extract_config: Optional[ExtractConfig] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        identifier_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        if not identifier_pattern.match(value):
            raise ValueError("field name must match ^[a-zA-Z_][a-zA-Z0-9_]*$")
        return value

    @field_validator("store_in")
    @classmethod
    def ensure_store_non_empty(cls, value: List[StoreLocation]) -> List[StoreLocation]:
        if not value:
            raise ValueError("store_in must contain at least one location")
        return value

    @field_validator("values")
    @classmethod
    def validate_enum_values(
        cls, value: Optional[List[Any]], info: FieldValidationInfo
    ) -> Optional[List[Any]]:
        if info.data.get("type") == FieldType.ENUM and (not value or len(value) == 0):
            raise ValueError("enum fields must declare at least one value")
        return value

    @model_validator(mode="after")
    def validate_field(self) -> "FieldDefinition":
        if self.type != FieldType.ENUM and self.values:
            raise ValueError("values is only valid for enum fields")

        if self.vectorize and self.type not in {FieldType.TEXT, FieldType.STRING, FieldType.FILE}:
            raise ValueError("vectorize can only be enabled for string, text, or file fields")

        if self.type == FieldType.ARRAY:
            if not self.schema or len(self.schema) == 0:
                raise ValueError("array fields require a non-empty nested schema")
        else:
            if self.schema:
                raise ValueError("schema is only allowed for array fields")

        if self.type != FieldType.FILE and self.extract_config:
            raise ValueError("extract_config is only applicable to file fields")

        if self.unique and self.type not in {FieldType.STRING, FieldType.INT, FieldType.FLOAT}:
            raise ValueError("unique constraint is only supported for string, int, or float fields")

        return self


FieldDefinition.model_rebuild()


class CollectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    embedding_provider_id: Optional[str] = None


class CollectionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    database: Optional[str] = None
    description: Optional[str] = None
    fields: List[FieldDefinition]
    config: CollectionConfig = Field(default_factory=CollectionConfig)

    @model_validator(mode="after")
    def ensure_unique_field_names(self) -> "CollectionSchema":
        seen: set[str] = set()
        for field in self.fields:
            if field.name in seen:
                raise ValueError(f"duplicate field name detected: {field.name}")
            seen.add(field.name)
        return self

    @model_validator(mode="after")
    def validate_collection_name(self) -> "CollectionSchema":
        identifier_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        if not identifier_pattern.match(self.name):
            raise ValueError("collection name must match ^[a-zA-Z_][a-zA-Z0-9_]*$")
        return self

    def get_field(self, field_name: str) -> FieldDefinition:
        for field in self.fields:
            if field.name == field_name:
                return field
        raise KeyError(field_name)
