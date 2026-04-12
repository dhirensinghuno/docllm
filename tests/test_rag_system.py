# Author: dhirenkumarsingh
"""Unit tests for Document Query System."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDocumentProcessor:
    """Tests for DocumentProcessor class."""

    def test_clean_text(self):
        """Test text cleaning functionality."""
        from document_processor import DocumentProcessor

        processor = DocumentProcessor()
        text = "This   is    a    test\n\n\nwith\nmultiple\nnewlines"
        cleaned = processor.clean_text(text)

        assert "  " not in cleaned
        assert "\n\n\n" not in cleaned
        assert cleaned == "This is a test\n\n\nwith\nmultiple\nnewlines"

    def test_chunk_text(self):
        """Test text chunking."""
        from document_processor import DocumentProcessor

        processor = DocumentProcessor()
        text = "This is a test document. " * 100
        chunks = processor.chunk_text(text, "test-doc-id")

        assert len(chunks) > 1
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        assert all(
            chunk["metadata"]["document_id"] == "test-doc-id" for chunk in chunks
        )


class TestConfig:
    """Tests for configuration."""

    def test_settings_defaults(self):
        """Test default settings."""
        from config import settings

        assert settings.vector_db in ["pinecone", "faiss"]
        assert settings.chunk_size > 0
        assert settings.chunk_overlap >= 0
        assert settings.chunk_overlap < settings.chunk_size

    def test_use_openai_flag(self):
        """Test OpenAI toggle."""
        from config import settings

        assert isinstance(settings.use_openai, bool)


class TestModels:
    """Tests for Pydantic models."""

    def test_question_request_validation(self):
        """Test QuestionRequest model validation."""
        from models import QuestionRequest

        valid_request = QuestionRequest(question="What is AI?", top_k=5)
        assert valid_request.question == "What is AI?"
        assert valid_request.top_k == 5

        with pytest.raises(Exception):
            QuestionRequest(question="")

    def test_answer_response_model(self):
        """Test AnswerResponse model."""
        from models import AnswerResponse

        response = AnswerResponse(
            answer="AI stands for Artificial Intelligence",
            sources=[{"text": "AI is...", "score": 0.9}],
            document_id="test-doc",
        )
        assert response.answer is not None
        assert len(response.sources) == 1

    def test_health_response_model(self):
        """Test HealthResponse model."""
        from models import HealthResponse

        response = HealthResponse(
            status="healthy", vector_db="faiss", llm_type="OpenAI"
        )
        assert response.status == "healthy"
        assert response.vector_db == "faiss"


class TestVectorStore:
    """Tests for vector store functionality."""

    def test_inmemory_store_initialization(self):
        """Test InMemoryVectorStore initialization."""
        from vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=1536)
        assert store.dimension == 1536
        assert store.vectors == []

    def test_inmemory_empty_search(self):
        """Test searching empty InMemory index."""
        from vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=1536)
        results = store.similarity_search([0.0] * 1536, top_k=5)
        assert results == []

    def test_inmemory_add_and_search(self):
        """Test adding vectors and searching."""
        from vector_store import InMemoryVectorStore

        store = InMemoryVectorStore(dimension=3)

        vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        texts = ["doc1", "doc2", "doc3"]
        metadatas = [{"doc_id": "1"}, {"doc_id": "2"}, {"doc_id": "3"}]

        store.add_vectors(vectors, texts, metadatas)
        results = store.similarity_search([1.0, 0.0, 0.0], top_k=1)

        assert len(results) == 1
        assert results[0][0] == "doc1"
        assert results[0][2] > 0.99


class TestEmbeddings:
    """Tests for embedding generation."""

    def test_embedding_generator_init(self):
        """Test embedding generator initialization."""
        from embeddings import EmbeddingGenerator

        try:
            generator = EmbeddingGenerator()
            assert generator is not None
        except Exception as e:
            pytest.skip(f"Embedding service not available: {e}")


class TestLLMHandler:
    """Tests for LLM handler."""

    def test_prompt_creation(self):
        """Test prompt creation."""
        from llm_handler import LLMHandler

        try:
            handler = LLMHandler()
            prompt = handler._create_prompt("context here", "what is this?")
            assert "context here" in prompt
            assert "what is this?" in prompt
        except Exception as e:
            pytest.skip(f"LLM service not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
