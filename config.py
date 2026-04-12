# Author: dhirenkumarsingh
"""Configuration management for Document Query System."""

import os
import logging
from typing import Literal
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info("Configuration module loaded")


class Settings(BaseSettings):
    """Application settings."""

    use_openai: bool = False
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"

    vector_db: Literal["pinecone", "faiss"] = "faiss"
    pinecone_api_key: str = ""
    pinecone_index: str = "document-query-system"
    pinecone_environment: str = "us-east-1"

    faiss_index_path: str = "./data/faiss_index"

    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    embedding_model: str = "nomic-embed-text"
    chunk_size: int = 10000
    chunk_overlap: int = 200
    skip_embeddings: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
logger.info(
    f"Settings loaded - Vector DB: {settings.vector_db}, LLM: {'OpenAI' if settings.use_openai else 'Ollama'}"
)
logger.info(
    f"AWS Config - Region: {settings.aws_region}, Bucket: {settings.s3_bucket}, Has Credentials: {bool(settings.aws_access_key_id)}"
)
