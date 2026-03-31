"""Document processing utilities."""

import re
import logging
from typing import List
from PyPDF2 import PdfReader
from config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles PDF document processing and text extraction."""

    def __init__(self):
        logger.info("Initializing DocumentProcessor")
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        logger.info(
            f"DocumentProcessor initialized: chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}"
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file."""
        logger.info(f"Extracting text from PDF: {pdf_path}")
        try:
            reader = PdfReader(pdf_path)
            text = ""
            page_count = len(reader.pages)
            for page in reader.pages:
                text += page.extract_text() or ""
            logger.info(f"Extracted {len(text)} characters from {page_count} pages")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text content from PDF bytes."""
        logger.info(f"Extracting text from PDF bytes: {len(pdf_bytes)} bytes")
        try:
            from io import BytesIO

            reader = PdfReader(BytesIO(pdf_bytes))
            text = ""
            page_count = len(reader.pages)
            for page in reader.pages:
                text += page.extract_text() or ""
            logger.info(f"Extracted {len(text)} characters from {page_count} pages")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF bytes: {e}")
            raise

    def chunk_text(self, text: str, document_id: str) -> List[dict]:
        """Split text into chunks with metadata."""
        logger.info(
            f"Chunking text for document_id={document_id}, text_length={len(text)}"
        )
        logger.info("Starting _split_text")
        chunks = self._split_text(text)
        logger.info(f"_split_text completed, got {len(chunks)} chunks")
        result = [
            {
                "content": chunk,
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            }
            for i, chunk in enumerate(chunks)
        ]
        logger.info(f"Created {len(chunks)} chunks for document_id={document_id}")
        return result

    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        logger.info(
            f"_split_text started with text_length={len(text)}, chunk_size={self.chunk_size}"
        )
        separators = ["\n\n", "\n", ". ", " "]
        chunks = []
        start = 0
        iterations = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            if end < len(text):
                for sep in separators:
                    last_sep = chunk.rfind(sep)
                    if last_sep != -1:
                        chunk = chunk[: last_sep + len(sep)]
                        end = start + len(chunk)
                        break

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap if start < end else end
            iterations += 1
            if iterations % 10 == 0:
                logger.info(
                    f"_split_text progress: {iterations} iterations, start={start}/{len(text)}"
                )

        logger.info(
            f"_split_text completed: {len(chunks)} chunks in {iterations} iterations"
        )
        return [c for c in chunks if c]

    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        logger.debug(f"Cleaning text of length {len(text)}")
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n+", "\n", text)
        return text.strip()
