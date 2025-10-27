from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status

from ..core.records import RecordService, get_record_service

router = APIRouter(prefix="/collections/{collection}/records", tags=["records"])


def get_service() -> RecordService:
    return get_record_service()


async def _parse_request_body(request: Request) -> tuple[Dict[str, Any], Dict[str, UploadFile]]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        data: Dict[str, Any] = {}
        files: Dict[str, UploadFile] = {}
        for key, value in form.multi_items():
            # Check if value has file-like attributes (UploadFile)
            if hasattr(value, 'file') and hasattr(value, 'filename'):
                files[key] = value
            elif isinstance(value, str):
                try:
                    data[key] = json.loads(value)
                except json.JSONDecodeError:
                    data[key] = value
            else:
                data[key] = value
        return data, files

    try:
        json_payload = await request.json()
        if not isinstance(json_payload, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request body must be a JSON object")
        return json_payload, {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body") from exc


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_record(collection: str, request: Request, service: RecordService = Depends(get_service)):
    data, files = await _parse_request_body(request)
    try:
        result = await service.create_record(collection, data, files)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return result


@router.get("/{record_id}")
async def get_record(collection: str, record_id: str, service: RecordService = Depends(get_service)):
    try:
        record = await service.get_record(collection, record_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


@router.patch("/{record_id}")
async def update_record(collection: str, record_id: str, request: Request, service: RecordService = Depends(get_service)):
    data, files = await _parse_request_body(request)
    try:
        result = await service.update_record(collection, record_id, data, files)
    except ValueError as exc:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc))
    return result


@router.get("/{record_id}/vectors")
async def get_record_vectors(collection: str, record_id: str, service: RecordService = Depends(get_service)):
    """Get all vector chunks for a record"""
    try:
        vectors = await service.get_record_vectors(collection, record_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {"vectors": vectors}


@router.delete("/{record_id}")
async def delete_record(collection: str, record_id: str, service: RecordService = Depends(get_service)):
    try:
        await service.delete_record(collection, record_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {"status": "deleted", "id": record_id}
