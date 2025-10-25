from __future__ import annotations

import asyncio
from typing import Optional

import google.generativeai as genai

from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GeminiVisionService:
    """Use Gemini multimodal models for OCR or image descriptions."""

    def __init__(self, api_key: str, model: str) -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    async def extract_text(self, image_bytes: bytes, mime_type: str) -> str:
        """Run OCR on the provided image and return extracted text."""
        prompt = "Extract all textual content from this document image. Respond with text only."
        payload = [{"mime_type": mime_type, "data": image_bytes}, prompt]
        response = await asyncio.to_thread(self._model.generate_content, payload)
        return response.text or ""

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        """Provide a description of the image."""
        prompt = "Provide a concise description of this image suitable for search indexing."
        payload = [{"mime_type": mime_type, "data": image_bytes}, prompt]
        response = await asyncio.to_thread(self._model.generate_content, payload)
        return response.text or ""


_vision_service: Optional[GeminiVisionService] = None


def get_vision_service() -> Optional[GeminiVisionService]:
    global _vision_service
    if _vision_service is None:
        settings = get_settings()
        if not settings.gemini_api_key:
            return None  # Return None if API key not configured
        _vision_service = GeminiVisionService(settings.gemini_api_key, settings.gemini_vision_model)
    return _vision_service
