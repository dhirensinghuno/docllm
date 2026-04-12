# Author: dhirenkumarsingh
"""FastAPI application for Document Query System."""

import logging
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from config import settings
from models import (
    DocumentUploadResponse,
    QuestionRequest,
    AnswerResponse,
    DocumentListResponse,
    HealthResponse,
)
from rag_service import rag_service

logger = logging.getLogger(__name__)

upload_tasks = {}


def process_upload(task_id: str, pdf_bytes: bytes, filename: str, s3_upload: bool):
    """Background task to process document upload."""
    try:
        logger.info(f"Starting background upload processing: task_id={task_id}")
        result = rag_service.upload_document_from_bytes(
            pdf_bytes=pdf_bytes, filename=filename, s3_upload=s3_upload
        )
        upload_tasks[task_id] = {
            "status": "completed",
            "result": {
                "document_id": result["document_id"],
                "filename": result["filename"],
                "status": result["status"],
                "num_chunks": result["num_chunks"],
            },
        }
        logger.info(f"Upload completed: document_id={result['document_id']}")
    except Exception as e:
        import traceback

        logger.error(f"Upload failed: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        upload_tasks[task_id] = {"status": "failed", "error": str(e)}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Document Query System starting up...")
    logger.info(f"Vector DB: {settings.vector_db}")
    logger.info(f"LLM: {'OpenAI' if settings.use_openai else 'Ollama'}")
    logger.info(f"Embedding Model: {settings.embedding_model}")
    logger.info("=" * 50)
    yield
    logger.info("Document Query System shutting down...")


app = FastAPI(
    title="Document Query System",
    description="AI-powered RAG system for querying PDF documents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("FastAPI application configured")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health."""
    logger.info("Health check endpoint called")
    response = HealthResponse(
        status="healthy",
        vector_db=settings.vector_db,
        llm_type="OpenAI" if settings.use_openai else "Ollama",
    )
    logger.info(f"Health check response: {response}")
    return response


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    upload_to_s3: bool = False,
):
    """Upload and index a PDF document."""
    filename = file.filename or "document.pdf"
    logger.info(f"Upload request: filename={filename}, upload_to_s3={upload_to_s3}")

    if not filename.endswith(".pdf"):
        logger.warning(f"Invalid file type: {filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    contents = await file.read()
    logger.info(f"Read {len(contents)} bytes from uploaded file")

    task_id = str(uuid.uuid4())
    upload_tasks[task_id] = {"status": "processing"}

    background_tasks.add_task(process_upload, task_id, contents, filename, upload_to_s3)

    return DocumentUploadResponse(
        document_id=task_id,
        filename=filename,
        status="processing",
        message="Document upload started. Use /upload/{task_id} to check status.",
    )


@app.get("/upload/{task_id}")
async def get_upload_status(task_id: str):
    """Get status of an upload task."""
    if task_id not in upload_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = upload_tasks[task_id]
    if task["status"] == "completed":
        return DocumentUploadResponse(
            document_id=task["result"]["document_id"],
            filename=task["result"]["filename"],
            status=task["result"]["status"],
            message=f"Successfully indexed {task['result']['num_chunks']} chunks",
        )
    elif task["status"] == "failed":
        raise HTTPException(status_code=500, detail=task["error"])
    else:
        return {"status": "processing", "message": "Upload still processing..."}


@app.post("/upload/sync", response_model=DocumentUploadResponse)
async def upload_document_sync(
    file: UploadFile = File(...), upload_to_s3: bool = False
):
    """Synchronous upload endpoint."""
    filename = file.filename or "document.pdf"
    logger.info(
        f"Sync upload request: filename={filename}, upload_to_s3={upload_to_s3}"
    )

    if not filename.endswith(".pdf"):
        logger.warning(f"Invalid file type: {filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        contents = await file.read()
        logger.info(f"Read {len(contents)} bytes from uploaded file")
        result = rag_service.upload_document_from_bytes(
            pdf_bytes=contents, filename=filename, s3_upload=upload_to_s3
        )
        logger.info(f"Upload successful: document_id={result['document_id']}")

        return DocumentUploadResponse(
            document_id=result["document_id"],
            filename=result["filename"],
            status=result["status"],
            message=f"Successfully indexed {result['num_chunks']} chunks",
        )
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=AnswerResponse)
async def query_documents(request: QuestionRequest):
    """Ask a question about uploaded documents."""
    logger.info(
        f"Query request: question={request.question[:50]}..., document_id={request.document_id}"
    )

    try:
        result = rag_service.query(
            question=request.question,
            document_id=request.document_id,
            top_k=request.top_k,
        )
        logger.info(f"Query successful, answer length: {len(result['answer'])}")

        return AnswerResponse(
            answer=result["answer"],
            sources=result["sources"],
            document_id=result["document_id"],
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents."""
    logger.info("List documents request received")

    try:
        documents = rag_service.list_documents()
        logger.info(f"Returning {len(documents)} documents")
        return DocumentListResponse(documents=documents, total=len(documents))
    except Exception as e:
        logger.error(f"List documents failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its embeddings."""
    logger.info(f"Delete document request: document_id={document_id}")

    try:
        rag_service.delete_document(document_id)
        logger.info(f"Document deleted: {document_id}")
        return {"status": "success", "message": f"Document {document_id} deleted"}
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting uvicorn server...")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_keep_alive=300,  # 5 minutes timeout
        limit_concurrency=10,
    )
