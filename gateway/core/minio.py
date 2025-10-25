from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import BinaryIO, Optional

from minio import Minio
from minio.error import S3Error

from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MinioService:
    """Async helpers around the MinIO client."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False) -> None:
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    async def ensure_bucket(self, bucket: str) -> None:
        exists = await asyncio.to_thread(self._client.bucket_exists, bucket)
        if not exists:
            await asyncio.to_thread(self._client.make_bucket, bucket)
            logger.info("minio_bucket_created", extra={"bucket": bucket})

    async def upload_stream(
        self,
        bucket: str,
        object_name: str,
        stream: BinaryIO,
        length: int,
        content_type: Optional[str] = None,
    ) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            bucket,
            object_name,
            stream,
            length,
            content_type=content_type,
        )

    async def remove_object(self, bucket: str, object_name: str) -> None:
        await asyncio.to_thread(self._client.remove_object, bucket, object_name)

    async def generate_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> str:
        url = await asyncio.to_thread(
            self._client.presigned_get_object,
            bucket,
            object_name,
            expires=timedelta(seconds=expires),
        )
        return url

    async def get_object(self, bucket: str, object_name: str):
        return await asyncio.to_thread(self._client.get_object, bucket, object_name)

    async def healthcheck(self) -> bool:
        try:
            await asyncio.to_thread(self._client.list_buckets)
            return True
        except S3Error:
            return False


_service: Optional[MinioService] = None


def get_minio_service() -> MinioService:
    global _service
    if _service is None:
        settings = get_settings()
        _service = MinioService(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _service
