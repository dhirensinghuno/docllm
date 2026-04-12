# Author: dhirenkumarsingh
"""RAG service orchestrating all components."""

import uuid
import os
import logging
from typing import List, Optional
from document_processor import DocumentProcessor
from embeddings import EmbeddingGenerator
from vector_store import get_vector_store
from llm_handler import LLMHandler
from s3_storage import S3Storage
from config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Main service for RAG-based document query."""

    def __init__(self):
        logger.info("Initializing RAGService")
        self.doc_processor = DocumentProcessor()
        self.skip_embeddings = settings.skip_embeddings

        if self.skip_embeddings:
            logger.info("Skipping embeddings - using simple text search mode")
            self.embedding_generator = None
            self._vector_store = None
        else:
            self.embedding_generator = EmbeddingGenerator()
            self._vector_store = None

        self.llm_handler = LLMHandler()
        self.chunks_store = []

        s3_enabled = bool(
            settings.aws_access_key_id
            and settings.aws_secret_access_key
            and settings.s3_bucket
        )
        logger.info(
            f"AWS credentials check - Access Key: {bool(settings.aws_access_key_id)}, Secret: {bool(settings.aws_secret_access_key)}, Bucket: {bool(settings.s3_bucket)}"
        )

        if s3_enabled:
            try:
                self.s3_storage = S3Storage()
                logger.info("S3 storage enabled")
            except Exception as e:
                logger.error(f"Failed to initialize S3 storage: {e}")
                self.s3_storage = None
        else:
            logger.info("S3 storage disabled - no AWS credentials configured")
            self.s3_storage = None

        self.document_metadata = {}
        logger.info(
            f"RAGService initialized. S3 storage: {'enabled' if self.s3_storage else 'disabled'}, Skip embeddings: {self.skip_embeddings}"
        )

    def _get_vector_store(self):
        """Lazy initialization of vector store."""
        if self.skip_embeddings:
            return None
        logger.debug("Getting vector store instance")
        if self._vector_store is None:
            dimension = self.embedding_generator.get_embedding_dimension()
            logger.info(f"Initializing vector store with dimension: {dimension}")
            self._vector_store = get_vector_store(dimension=dimension)
            logger.info("Vector store initialized")
        return self._vector_store

    def upload_document(
        self, file_path: str, filename: str = "document.pdf", s3_upload: bool = True
    ) -> dict:
        """Process and index a document."""
        logger.info(f"Uploading document: filename={filename}, file_path={file_path}")
        document_id = str(uuid.uuid4())
        logger.info(f"Generated document_id: {document_id}")

        try:
            text = self.doc_processor.extract_text_from_pdf(file_path)
            text = self.doc_processor.clean_text(text)
            chunks = self.doc_processor.chunk_text(text, document_id)

            if self.skip_embeddings:
                self.chunks_store.extend(chunks)
            else:
                texts = [chunk["content"] for chunk in chunks]
                metadatas = [chunk["metadata"] for chunk in chunks]
                vectors = self.embedding_generator.generate_embeddings(texts)
                self._get_vector_store().add_vectors(vectors, texts, metadatas)

            if s3_upload and self.s3_storage:
                s3_path = self.s3_storage.upload_document(file_path, document_id)
            else:
                s3_path = None

            self.document_metadata[document_id] = {
                "document_id": document_id,
                "filename": filename,
                "num_chunks": len(chunks),
                "s3_path": s3_path,
            }

            result = {
                "document_id": document_id,
                "filename": filename,
                "num_chunks": len(chunks),
                "status": "success",
            }
            logger.info(f"Document upload successful: {document_id}")
            return result
        except Exception as e:
            logger.error(f"Error uploading document: {type(e).__name__}: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def upload_document_from_bytes(
        self,
        pdf_bytes: bytes,
        filename: str = "document.pdf",
        s3_upload: bool = True,
    ) -> dict:
        """Process and index a document from bytes."""
        import tempfile

        logger.info(
            f"Uploading document from bytes: filename={filename}, size={len(pdf_bytes)}"
        )
        document_id = str(uuid.uuid4())
        logger.info(f"Generated document_id: {document_id}")

        try:
            text = self.doc_processor.extract_text_from_bytes(pdf_bytes)
            text = self.doc_processor.clean_text(text)
            chunks = self.doc_processor.chunk_text(text, document_id)

            if self.skip_embeddings:
                logger.info(
                    f"Adding {len(chunks)} chunks to chunks_store (skip_embeddings=True)"
                )
                self.chunks_store.extend(chunks)
                logger.info(
                    f"chunks_store now has {len(self.chunks_store)} total chunks"
                )
            else:
                texts = [chunk["content"] for chunk in chunks]
                metadatas = [chunk["metadata"] for chunk in chunks]
                vectors = self.embedding_generator.generate_embeddings(texts)
                self._get_vector_store().add_vectors(vectors, texts, metadatas)

            if s3_upload and self.s3_storage:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_bytes)
                    tmp_path = tmp.name
                try:
                    s3_path = self.s3_storage.upload_document(tmp_path, document_id)
                finally:
                    os.unlink(tmp_path)
            else:
                s3_path = None

            self.document_metadata[document_id] = {
                "document_id": document_id,
                "filename": filename,
                "num_chunks": len(chunks),
                "s3_path": s3_path,
            }

            result = {
                "document_id": document_id,
                "filename": filename,
                "num_chunks": len(chunks),
                "status": "success",
            }
            logger.info(f"Document upload from bytes successful: {document_id}")
            return result
        except Exception as e:
            import traceback

            logger.error(
                f"Error uploading document from bytes: {type(e).__name__}: {str(e)}"
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _simple_search(
        self, query: str, document_id: Optional[str] = None, top_k: int = 5
    ):
        """Simple text search without embeddings."""
        query_lower = query.lower()
        results = []

        for chunk in self.chunks_store:
            if document_id and chunk["metadata"].get("document_id") != document_id:
                continue

            content_lower = chunk["content"].lower()
            words = query_lower.split()
            score = sum(1 for word in words if word in content_lower)

            if score > 0:
                results.append(
                    (chunk["content"], chunk["metadata"], float(score / len(words)))
                )

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]

    def query(
        self, question: str, document_id: Optional[str] = None, top_k: int = 5
    ) -> dict:
        """Answer a question using RAG."""
        logger.info(
            f"Processing query: question={question[:50]}..., document_id={document_id}, top_k={top_k}"
        )

        try:
            if self.skip_embeddings:
                results = self._simple_search(question, document_id, top_k)
            else:
                query_embedding = self.embedding_generator.generate_query_embedding(
                    question
                )
                results = self._get_vector_store().similarity_search(
                    query_embedding, top_k=top_k
                )

                if document_id:
                    results = [
                        (text, meta, score)
                        for text, meta, score in results
                        if meta.get("document_id") == document_id
                    ]
                    logger.info(
                        f"Filtered to {len(results)} results for document_id={document_id}"
                    )

            answer = self.llm_handler.generate_answer(question, results)

            sources = [
                {
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "document_id": meta.get("document_id"),
                    "chunk_index": meta.get("chunk_index"),
                    "relevance_score": score,
                }
                for text, meta, score in results
            ]

            result = {"answer": answer, "sources": sources, "document_id": document_id}
            logger.info(f"Query successful, answer length: {len(answer)}")
            return result
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its embeddings."""
        logger.info(f"Deleting document: {document_id}")

        try:
            if self.s3_storage:
                try:
                    self.s3_storage.delete_document(document_id)
                except Exception as e:
                    logger.warning(f"Failed to delete from S3: {e}")

            if not self.skip_embeddings:
                self._get_vector_store().delete({"document_id": document_id})

            self.chunks_store = [
                c
                for c in self.chunks_store
                if c["metadata"].get("document_id") != document_id
            ]

            if document_id in self.document_metadata:
                del self.document_metadata[document_id]

            logger.info(f"Document deleted: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise

    def list_documents(self) -> List[dict]:
        """List all indexed documents."""
        logger.info("Listing all documents")
        doc_ids = set(meta["document_id"] for meta in self.document_metadata.values())
        documents = [
            {
                "document_id": doc_id,
                "filename": self.document_metadata[doc_id]["filename"],
                "num_chunks": self.document_metadata[doc_id]["num_chunks"],
                "s3_path": self.document_metadata[doc_id].get("s3_path"),
            }
            for doc_id in doc_ids
        ]
        logger.info(f"Found {len(documents)} documents")
        return documents


logger.info("Creating RAG service instance")
rag_service = RAGService()
logger.info("RAG service instance created")
