# Author: dhirenkumarsingh
"""Simple API client for testing."""

import requests
import base64
from typing import Optional


class DocumentQueryClient:
    """Client for Document Query System API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def health_check(self) -> dict:
        """Check API health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def upload_document(self, file_path: str, upload_to_s3: bool = False) -> dict:
        """Upload a PDF document."""
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"upload_to_s3": str(upload_to_s3).lower()}
            response = requests.post(f"{self.base_url}/upload", files=files, data=data)
        response.raise_for_status()
        return response.json()

    def upload_document_base64(
        self, pdf_base64: str, filename: str = "document.pdf"
    ) -> dict:
        """Upload a PDF document from base64 encoded string."""
        response = requests.post(
            f"{self.base_url}/upload",
            json={"document": pdf_base64, "filename": filename},
        )
        response.raise_for_status()
        return response.json()

    def query(
        self, question: str, document_id: Optional[str] = None, top_k: int = 5
    ) -> dict:
        """Ask a question about documents."""
        response = requests.post(
            f"{self.base_url}/query",
            json={"question": question, "document_id": document_id, "top_k": top_k},
        )
        response.raise_for_status()
        return response.json()

    def list_documents(self) -> dict:
        """List all uploaded documents."""
        response = requests.get(f"{self.base_url}/documents")
        response.raise_for_status()
        return response.json()

    def delete_document(self, document_id: str) -> dict:
        """Delete a document."""
        response = requests.delete(f"{self.base_url}/documents/{document_id}")
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    client = DocumentQueryClient()

    print("Checking health...")
    health = client.health_check()
    print(f"Health: {health}")

    print("\nListing documents...")
    docs = client.list_documents()
    print(f"Documents: {docs}")
