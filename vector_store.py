"""Vector store implementations using scikit-learn (pure Python fallback)."""

import os
import pickle
import logging
from typing import List, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Base class for vector stores."""

    def add_vectors(
        self, vectors: List[List[float]], texts: List[str], metadatas: List[dict]
    ) -> None:
        """Add vectors to the store."""
        raise NotImplementedError

    def similarity_search(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Tuple[str, dict, float]]:
        """Search for similar vectors."""
        raise NotImplementedError

    def delete(self, filter_dict: dict) -> None:
        """Delete vectors by filter."""
        raise NotImplementedError


class PineconeStore(VectorStore):
    """Pinecone vector store implementation."""

    def __init__(self):
        logger.info("Initializing PineconeStore")
        from pinecone import Pinecone

        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self._get_or_create_index()
        logger.info("PineconeStore initialized")

    def _get_or_create_index(self):
        """Get or create Pinecone index."""
        logger.info(f"Connecting to Pinecone index: {settings.pinecone_index}")
        from pinecone import ServerlessSpec

        existing = [idx.name for idx in self.pc.list_indexes()]
        logger.debug(f"Existing indexes: {existing}")

        if settings.pinecone_index not in existing:
            logger.info(f"Creating new Pinecone index: {settings.pinecone_index}")
            dimension = 1536
            self.pc.create_index(
                name=settings.pinecone_index,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.pinecone_environment),
            )
            logger.info(f"Pinecone index created: {settings.pinecone_index}")

        return self.pc.Index(settings.pinecone_index)

    def add_vectors(
        self, vectors: List[List[float]], texts: List[str], metadatas: List[dict]
    ) -> None:
        """Add vectors to Pinecone."""
        logger.info(f"Adding {len(vectors)} vectors to Pinecone")
        try:
            vectors_with_ids = [
                (
                    f"doc_{metadatas[i]['document_id']}_chunk_{metadatas[i]['chunk_index']}",
                    vectors[i],
                    {**metadatas[i], "text": texts[i]},
                )
                for i in range(len(vectors))
            ]
            self.index.upsert(vectors=vectors_with_ids)
            logger.info(f"Successfully upserted {len(vectors)} vectors to Pinecone")
        except Exception as e:
            logger.error(f"Error adding vectors to Pinecone: {e}")
            raise

    def similarity_search(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Tuple[str, dict, float]]:
        """Search Pinecone for similar vectors."""
        logger.info(f"Searching Pinecone with top_k={top_k}")
        try:
            results = self.index.query(
                vector=query_vector, top_k=top_k, include_metadata=True
            )
            matches = results.matches
            logger.info(f"Found {len(matches)} matches in Pinecone")
            return [
                (match.metadata.get("text", ""), match.metadata, match.score)
                for match in results.matches
            ]
        except Exception as e:
            logger.error(f"Error searching Pinecone: {e}")
            raise

    def delete(self, filter_dict: dict) -> None:
        """Delete vectors from Pinecone."""
        logger.info(f"Deleting vectors from Pinecone with filter: {filter_dict}")
        try:
            self.index.delete(filter=filter_dict)
            logger.info("Vectors deleted from Pinecone")
        except Exception as e:
            logger.error(f"Error deleting from Pinecone: {e}")
            raise


class InMemoryVectorStore(VectorStore):
    """Pure Python in-memory vector store using scikit-learn."""

    def __init__(self, dimension: int = 1536):
        logger.info(f"Initializing InMemoryVectorStore with dimension={dimension}")
        self.dimension = dimension
        self.vectors: List[List[float]] = []
        self.texts: List[str] = []
        self.metadatas: List[dict] = []
        self._load_existing()
        logger.info(
            f"InMemoryVectorStore initialized with {len(self.vectors)} existing vectors"
        )

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors for cosine similarity."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms

    def _load_existing(self):
        """Load existing index if available."""
        logger.info(f"Loading existing index from: {settings.faiss_index_path}")
        os.makedirs(settings.faiss_index_path, exist_ok=True)
        meta_file = os.path.join(settings.faiss_index_path, "metadata.pkl")

        if os.path.exists(meta_file):
            try:
                with open(meta_file, "rb") as f:
                    data = pickle.load(f)
                    self.vectors = data.get("vectors", [])
                    self.texts = data.get("texts", [])
                    self.metadatas = data.get("metadatas", [])
                logger.info(f"Loaded {len(self.vectors)} existing vectors")
            except Exception as e:
                logger.warning(f"Error loading existing index: {e}, starting fresh")
                self.vectors = []
                self.texts = []
                self.metadatas = []
        else:
            logger.info("No existing index found, starting fresh")

    def _save(self):
        """Save index and metadata."""
        logger.debug(f"Saving index with {len(self.vectors)} vectors")
        os.makedirs(settings.faiss_index_path, exist_ok=True)
        meta_file = os.path.join(settings.faiss_index_path, "metadata.pkl")

        with open(meta_file, "wb") as f:
            pickle.dump(
                {
                    "vectors": self.vectors,
                    "texts": self.texts,
                    "metadatas": self.metadatas,
                },
                f,
            )
        logger.debug("Index saved successfully")

    def add_vectors(
        self, vectors: List[List[float]], texts: List[str], metadatas: List[dict]
    ) -> None:
        """Add vectors to the store."""
        logger.info(f"Adding {len(vectors)} vectors to InMemoryVectorStore")
        self.vectors.extend(vectors)
        self.texts.extend(texts)
        self.metadatas.extend(metadatas)
        self._save()
        logger.info(f"Total vectors now: {len(self.vectors)}")

    def similarity_search(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Tuple[str, dict, float]]:
        """Search for similar vectors using cosine similarity."""
        logger.info(
            f"Searching InMemoryVectorStore with top_k={top_k}, total={len(self.vectors)}"
        )
        if not self.vectors:
            logger.info("No vectors in store, returning empty")
            return []

        vectors_array = np.array(self.vectors)
        query_array = np.array([query_vector])

        similarities = cosine_similarity(query_array, vectors_array)[0]

        top_indices = np.argsort(similarities)[::-1][: min(top_k, len(similarities))]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                results.append(
                    (self.texts[idx], self.metadatas[idx], float(similarities[idx]))
                )
        logger.info(f"Found {len(results)} similar vectors")
        return results

    def delete(self, filter_dict: dict) -> None:
        """Delete vectors by filter."""
        doc_id = filter_dict.get("document_id")
        logger.info(f"Deleting vectors for document_id={doc_id}")
        if doc_id:
            indices_to_keep = [
                i
                for i, m in enumerate(self.metadatas)
                if m.get("document_id") != doc_id
            ]
            self.vectors = [self.vectors[i] for i in indices_to_keep]
            self.texts = [self.texts[i] for i in indices_to_keep]
            self.metadatas = [self.metadatas[i] for i in indices_to_keep]
            self._save()
            logger.info(f"Deleted vectors, remaining: {len(self.vectors)}")


def get_vector_store(dimension: int = 1536) -> VectorStore:
    """Factory function to get the configured vector store."""
    logger.info(f"Getting vector store, configured: {settings.vector_db}")
    if settings.vector_db == "pinecone":
        if not settings.pinecone_api_key:
            logger.error("Pinecone API key not provided")
            raise ValueError("Pinecone API key required when using Pinecone")
        logger.info("Returning PineconeStore")
        return PineconeStore()
    logger.info("Returning InMemoryVectorStore")
    return InMemoryVectorStore(dimension=dimension)
