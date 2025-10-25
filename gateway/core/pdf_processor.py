from __future__ import annotations

import io
from typing import Optional

import pdfplumber
from pdf2image import convert_from_bytes

from ..models.schema import ExtractConfig
from ..utils.logger import get_logger
from .vision import get_vision_service

logger = get_logger(__name__)


class PDFProcessor:
    """Process PDFs to extract text using native parsing with Gemini OCR fallback."""

    def __init__(self) -> None:
        self._vision = get_vision_service()

    async def extract_text(self, pdf_bytes: bytes, config: Optional[ExtractConfig] = None) -> str:
        config = config or ExtractConfig()
        text = self._extract_text_native(pdf_bytes)
        if text.strip():
            return text

        if config.ocr_if_needed:
            return await self._extract_text_with_ocr(pdf_bytes)

        return ""

    def _extract_text_native(self, pdf_bytes: bytes) -> str:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                pages_text = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(filter(None, pages_text))
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("pdf_native_extraction_failed", extra={"error": str(exc)})
            return ""

    async def _extract_text_with_ocr(self, pdf_bytes: bytes) -> str:
        try:
            images = convert_from_bytes(pdf_bytes)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("pdf_to_image_failed", extra={"error": str(exc)})
            return ""

        parts: list[str] = []
        for image in images:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            text = await self._vision.extract_text(buffer.getvalue(), "image/png")
            parts.append(text.strip())

        return "\n".join(filter(None, parts))


_processor: Optional[PDFProcessor] = None


def get_pdf_processor() -> PDFProcessor:
    global _processor
    if _processor is None:
        _processor = PDFProcessor()
    return _processor
