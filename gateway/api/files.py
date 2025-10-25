from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ..core.collections import default_bucket_name
from ..core.minio import MinioService, get_minio_service


router = APIRouter(prefix="/files", tags=["files"])


def get_service() -> MinioService:
    return get_minio_service()


@router.post("/upload")
async def upload_file(
    collection: str = Form(...),
    file: UploadFile = File(...),
    service: MinioService = Depends(get_service),
):
    bucket = default_bucket_name(collection)
    await service.ensure_bucket(bucket)
    content = await file.read()
    buffer = io.BytesIO(content)
    buffer.seek(0)
    object_path = f"{collection}/uploads/{uuid.uuid4()}_{file.filename}"
    await service.upload_stream(bucket, object_path, buffer, length=len(content), content_type=file.content_type)
    url = await service.generate_presigned_url(bucket, object_path)
    return {
        "bucket": bucket,
        "path": object_path,
        "url": url,
    }


@router.get("/{collection}/{record_id}/{filename}")
async def download_file(collection: str, record_id: str, filename: str, service: MinioService = Depends(get_service)):
    bucket = default_bucket_name(collection)
    object_path = f"{collection}/{record_id}/{filename}"
    try:
        obj = await service.get_object(bucket, object_path)
    except Exception as exc:  # pragma: no cover - depends on MinIO
        raise HTTPException(status_code=404, detail="File not found") from exc

    def iterator():
        try:
            for chunk in obj.stream(32 * 1024):
                yield chunk
        finally:
            obj.close()

    return StreamingResponse(iterator(), media_type=obj.headers.get("Content-Type", "application/octet-stream"))
