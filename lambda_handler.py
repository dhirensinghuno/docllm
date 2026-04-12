# Author: dhirenkumarsingh
"""AWS Lambda handler for document processing."""

import json
import base64
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

s3_client = boto3.client("s3")

ALLOWED_ORIGINS = ["https://your-frontend-domain.com", "http://localhost:3000"]


def get_cors_headers(event):
    """Get CORS headers from the request or use defaults."""
    logger.debug("Getting CORS headers")
    origin = event.get("headers", {}).get("origin", "")

    if origin in ALLOWED_ORIGINS or not origin:
        return {
            "Access-Control-Allow-Origin": origin if origin else ALLOWED_ORIGINS[0],
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
        }
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
    }


def lambda_handler(event, context):
    """Main Lambda handler."""
    logger.info(
        f"Lambda invoked: path={event.get('path')}, method={event.get('httpMethod')}"
    )

    http_method = event.get(
        "httpMethod",
        event.get("requestContext", {}).get("http", {}).get("method", "GET"),
    )
    path = event.get("path", "/")
    headers = get_cors_headers(event)

    if http_method == "OPTIONS":
        logger.info("Handling OPTIONS preflight request")
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "OK"}),
        }

    try:
        if path == "/health":
            logger.info("Routing to health endpoint")
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(
                    {"status": "healthy", "service": "document-query-system"}
                ),
            }

        if path == "/upload" and http_method == "POST":
            logger.info("Routing to upload endpoint")
            return handle_upload(event, headers)

        if path == "/query" and http_method == "POST":
            logger.info("Routing to query endpoint")
            return handle_query(event, headers)

        if path.startswith("/documents") and http_method == "GET":
            logger.info("Routing to list documents endpoint")
            return handle_list_documents(event, headers)

        if path.startswith("/documents/") and http_method == "DELETE":
            document_id = path.split("/")[-1]
            logger.info(f"Routing to delete document endpoint: {document_id}")
            return handle_delete_document(document_id, headers)

        logger.warning(f"No matching route: {path} {http_method}")
        return {
            "statusCode": 404,
            "headers": headers,
            "body": json.dumps({"error": "Not found"}),
        }

    except Exception as e:
        logger.error(f"Lambda error: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)}),
        }


def handle_upload(event, headers):
    """Handle document upload."""
    logger.info("Processing upload request")
    from rag_service import rag_service

    body = json.loads(event.get("body", "{}"))
    document_base64 = body.get("document")
    filename = body.get("filename", "document.pdf")

    if not document_base64:
        logger.warning("No document provided in upload request")
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "No document provided"}),
        }

    try:
        document_bytes = base64.b64decode(document_base64)
        logger.info(f"Decoded document: {len(document_bytes)} bytes")
        result = rag_service.upload_document_from_bytes(
            pdf_bytes=document_bytes, filename=filename
        )
        logger.info(f"Upload successful: {result}")
        return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)}),
        }


def handle_query(event, headers):
    """Handle query request."""
    logger.info("Processing query request")
    from rag_service import rag_service

    body = json.loads(event.get("body", "{}"))
    question = body.get("question")
    document_id = body.get("document_id")
    top_k = body.get("top_k", 5)

    if not question:
        logger.warning("No question provided in query request")
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "No question provided"}),
        }

    try:
        logger.info(f"Executing query: {question[:50]}..., top_k={top_k}")
        result = rag_service.query(
            question=question, document_id=document_id, top_k=top_k
        )
        logger.info(f"Query successful, answer length: {len(result['answer'])}")
        return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)}),
        }


def handle_list_documents(event, headers):
    """Handle list documents request."""
    logger.info("Processing list documents request")
    from rag_service import rag_service

    try:
        documents = rag_service.list_documents()
        logger.info(f"Found {len(documents)} documents")
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"documents": documents, "total": len(documents)}),
        }
    except Exception as e:
        logger.error(f"List documents failed: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)}),
        }


def handle_delete_document(document_id, headers):
    """Handle delete document request."""
    logger.info(f"Processing delete request: {document_id}")
    from rag_service import rag_service

    try:
        rag_service.delete_document(document_id)
        logger.info(f"Document deleted: {document_id}")
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(
                {"status": "success", "message": f"Document {document_id} deleted"}
            ),
        }
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)}),
        }
