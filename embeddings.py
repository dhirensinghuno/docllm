"""Embedding generation using OpenAI or Ollama."""

import logging
from typing import List
from openai import OpenAI
import httpx
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for text chunks."""

    def __init__(self):
        logger.info("Initializing EmbeddingGenerator")
        self.use_openai = settings.use_openai
        self.embedding_model = settings.embedding_model
        self.ollama_model = (
            settings.embedding_model
        )  # Use embedding_model for Ollama embeddings
        self.dimension = 1536

        if self.use_openai:
            logger.info(f"Using OpenAI embeddings: {self.embedding_model}")
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            logger.info(
                f"Using Ollama embeddings at: {settings.ollama_base_url} with model: {self.ollama_model}"
            )
            self.client = None

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        logger.info(f"Generating embeddings for {len(texts)} texts")
        try:
            if self.use_openai:
                response = self.client.embeddings.create(
                    model=self.embedding_model, input=texts
                )
                result = [item.embedding for item in response.data]
                logger.info(f"Generated {len(result)} embeddings from OpenAI")
                return result
            else:
                logger.info("Calling Ollama for embeddings")
                result = self._ollama_embeddings(texts)
                logger.info(f"Generated {len(result)} embeddings from Ollama")
                return result
        except Exception as e:
            logger.error(f"Error generating embeddings: {type(e).__name__}: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a query string."""
        logger.info(f"Generating embedding for query: {query[:50]}...")
        try:
            if self.use_openai:
                response = self.client.embeddings.create(
                    model=self.embedding_model, input=[query]
                )
                result = response.data[0].embedding
                logger.info(f"Generated query embedding with {len(result)} dimensions")
                return result
            else:
                logger.info(
                    f"Using Ollama model {self.ollama_model} for query embedding"
                )
                result = self._ollama_embeddings([query])[0]
                logger.info(
                    f"Generated query embedding with {len(result)} dimensions from Ollama"
                )
                return result
        except Exception as e:
            logger.error(
                f"Error generating query embedding: {type(e).__name__}: {str(e)}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _ollama_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama API with batch processing."""
        logger.info(
            f"Calling Ollama API at {settings.ollama_base_url} for {len(texts)} embeddings"
        )
        logger.info(f"Using Ollama model: {self.ollama_model}")

        embeddings = []

        with httpx.Client(timeout=300.0) as client:
            for i, text in enumerate(texts):
                try:
                    response = client.post(
                        f"{settings.ollama_base_url}/api/embeddings",
                        json={"model": self.ollama_model, "prompt": text},
                    )
                    response.raise_for_status()
                    embeddings.append(response.json()["embedding"])

                    if (i + 1) % 10 == 0:
                        logger.info(f"Embedding progress: {i + 1}/{len(texts)}")

                except Exception as e:
                    logger.error(f"Error getting embedding {i}: {e}")
                    raise

        logger.info(f"Successfully generated {len(embeddings)} embeddings from Ollama")
        return embeddings

    def get_embedding_dimension(self) -> int:
        """Return the dimension of the embedding model."""
        logger.info("Getting embedding dimension")
        test_embedding = self.generate_query_embedding("test")
        dimension = len(test_embedding)
        logger.info(f"Embedding dimension: {dimension}")
        return dimension
