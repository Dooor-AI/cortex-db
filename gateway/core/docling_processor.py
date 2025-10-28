"""Document processing using Docling for advanced PDF, DOCX, XLSX, etc. parsing."""

from __future__ import annotations

import asyncio
import io
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

from ..models.schema import ExtractConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DoclingProcessor:
    """Process documents using Docling for superior PDF/DOCX/XLSX understanding."""

    def __init__(self) -> None:
        """Initialize Docling converter with optimized pipeline options."""
        # Configure pipeline for better performance and quality
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True  # Enable OCR for scanned documents
        pipeline_options.do_table_structure = True  # Extract table structure
        pipeline_options.table_structure_options.do_cell_matching = True
        
        self._converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    async def extract_text_and_chunks(
        self,
        file_bytes: bytes,
        filename: str,
        config: Optional[ExtractConfig] = None,
    ) -> Tuple[str, List[str]]:
        """
        Extract text and semantic chunks from document.
        
        Args:
            file_bytes: Raw file bytes
            filename: Original filename (used to detect format)
            config: Optional extraction config
            
        Returns:
            Tuple of (full_text, semantic_chunks)
        """
        config = config or ExtractConfig()
        
        try:
            # Run Docling conversion in thread pool (CPU intensive)
            result = await asyncio.to_thread(
                self._convert_document,
                file_bytes,
                filename
            )
            
            if not result:
                logger.warning(
                    "docling_conversion_failed",
                    extra={"file_name": filename}
                )
                return "", []
            
            # Export to markdown (preserves structure)
            full_text = result.document.export_to_markdown()
            
            # Get semantic chunks based on document structure
            chunks = self._create_semantic_chunks(
                result.document,
                config.chunk_size or 500,
                config.chunk_overlap or 50
            )
            
            return full_text, chunks
            
        except Exception as exc:
            logger.exception(
                "docling_processing_error",
                extra={"file_name": filename, "error": str(exc)}
            )
            return "", []

    def _convert_document(self, file_bytes: bytes, filename: str):
        """Convert document using Docling (runs in thread pool)."""
        # Save to temporary file (Docling requires actual file path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Convert document
            result = self._converter.convert(tmp_path)
            return result
        finally:
            # Cleanup temporary file
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass

    def _create_semantic_chunks(
        self,
        document,
        target_chunk_size: int,
        overlap: int
    ) -> List[str]:
        """
        Create semantic chunks respecting document structure.
        
        Docling preserves document hierarchy (sections, paragraphs, tables, etc).
        We chunk intelligently to keep related content together.
        """
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_size = 0
        
        # Iterate through document elements
        for element in document.iterate_items():
            element_text = self._get_element_text(element)
            if not element_text:
                continue
            
            element_tokens = len(element_text.split())
            
            # If single element is larger than chunk size, split it
            if element_tokens > target_chunk_size:
                # Save current chunk if any
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split large element
                words = element_text.split()
                for i in range(0, len(words), target_chunk_size - overlap):
                    chunk_words = words[i:i + target_chunk_size]
                    chunks.append(" ".join(chunk_words))
                continue
            
            # If adding this element exceeds chunk size, save current chunk
            if current_size + element_tokens > target_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                # Keep last part for overlap
                if overlap > 0:
                    overlap_words = " ".join(current_chunk).split()[-overlap:]
                    current_chunk = [" ".join(overlap_words)]
                    current_size = len(overlap_words)
                else:
                    current_chunk = []
                    current_size = 0
            
            # Add element to current chunk
            current_chunk.append(element_text)
            current_size += element_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    def _get_element_text(self, element) -> str:
        """Extract text from Docling document element."""
        try:
            # Handle different element types
            if hasattr(element, 'text'):
                return element.text.strip()
            elif hasattr(element, 'export_to_markdown'):
                return element.export_to_markdown().strip()
            else:
                return str(element).strip()
        except Exception:
            return ""


_processor: Optional[DoclingProcessor] = None


def get_docling_processor() -> DoclingProcessor:
    """Get singleton instance of DoclingProcessor."""
    global _processor
    if _processor is None:
        _processor = DoclingProcessor()
    return _processor

