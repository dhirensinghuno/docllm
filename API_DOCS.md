# API Documentation

## Document Query System API Reference

### Base URL
```
Development: http://localhost:8000
Production:   https://your-api-gateway-url.amazonaws.com/prod
```

---

## Authentication

Currently, the API does not require authentication. For production deployment, implement:

1. API Key authentication
2. JWT tokens
3. AWS Cognito integration
4. OAuth 2.0

---

## Rate Limiting

No rate limiting is implemented by default. For production:

```python
# Example with FastAPI-Limiter
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/query", dependencies=[Depends(RateLimiter(times=10, minutes=1))])
async def query():
    ...
```

---

## Endpoints

### 1. Health Check

Check if the API is running and healthy.

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "vector_db": "faiss",
  "llm_type": "Ollama"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Health status: "healthy" or "unhealthy" |
| `vector_db` | string | Vector database in use: "faiss" or "pinecone" |
| `llm_type` | string | LLM provider: "OpenAI" or "Ollama" |

---

### 2. Upload Document

Upload a PDF document for indexing.

```http
POST /upload
Content-Type: multipart/form-data
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | file | Yes | - | PDF file to upload |
| `upload_to_s3` | boolean | No | false | Upload to AWS S3 |

**Example Request:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf" \
  -F "upload_to_s3=false"
```

**Response (200 OK):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "status": "success",
  "message": "Successfully indexed 5 chunks"
}
```

**Error Responses:**

| Status | Response |
|---------|----------|
| 400 | `{"detail": "Only PDF files are supported"}` |
| 500 | `{"detail": "Error message here"}` |

**Processing Flow:**
1. Receive PDF file
2. Extract text from PDF
3. Clean and normalize text
4. Split text into chunks
5. Generate embeddings for each chunk
6. Store vectors in vector database
7. (Optional) Upload PDF to S3
8. Return document ID

---

### 3. Query Documents

Ask a question about uploaded documents.

```http
POST /query
Content-Type: application/json
```

**Request Body:**

```json
{
  "question": "What is the main topic of the document?",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "top_k": 5
}
```

| Field | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `question` | string | Yes | - | The question to ask (1-1000 chars) |
| `document_id` | string | No | null | Filter by specific document |
| `top_k` | integer | No | 5 | Number of sources to return (1-20) |

**Example Request:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key findings?",
    "top_k": 5
  }'
```

**Response (200 OK):**
```json
{
  "answer": "Based on the documents, the key findings are...",
  "sources": [
    {
      "text": "The study found that...",
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_index": 0,
      "relevance_score": 0.95
    },
    {
      "text": "Additionally, researchers discovered...",
      "document_id": "550e8400-e29b-41d4-a716-446655440001",
      "chunk_index": 3,
      "relevance_score": 0.87
    }
  ],
  "document_id": null
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | AI-generated answer based on context |
| `sources` | array | List of relevant document chunks |
| `sources[].text` | string | Text content (truncated to 200 chars) |
| `sources[].document_id` | string | Source document ID |
| `sources[].chunk_index` | integer | Chunk index in the document |
| `sources[].relevance_score` | float | Similarity score (0-1) |
| `document_id` | string | Filter applied (null if all documents) |

**Processing Flow:**
1. Receive question
2. Generate embedding for question
3. Search vector database for similar chunks
4. (Optional) Filter by document_id
5. Send context + question to LLM
6. Return answer with sources

---

### 4. List Documents

Get a list of all uploaded documents.

```http
GET /documents
```

**Example Request:**
```bash
curl http://localhost:8000/documents
```

**Response (200 OK):**
```json
{
  "documents": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "document1.pdf",
      "num_chunks": 5,
      "s3_path": "s3://bucket/documents/550e8400/document.pdf"
    },
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440001",
      "filename": "document2.pdf",
      "num_chunks": 8,
      "s3_path": null
    }
  ],
  "total": 2
}
```

---

### 5. Delete Document

Delete a document and its associated vectors.

```http
DELETE /documents/{document_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | string | Yes | UUID of document to delete |

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/documents/550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Document 550e8400-e29b-41d4-a716-446655440000 deleted"
}
```

**Warning:** This action is irreversible. Deleting a document will:
- Remove all vectors from the vector database
- (If S3 enabled) Delete the PDF from S3
- Remove document metadata

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 413 | Payload Too Large - File exceeds size limit |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Dependency unavailable |

---

## Webhooks

For production, implement webhooks for async processing:

```python
@app.post("/webhooks/upload")
async def upload_webhook(
    request: Request,
    x_webhook_secret: str = Header(None)
):
    # Verify webhook signature
    if x_webhook_secret != os.getenv("WEBHOOK_SECRET"):
        raise HTTPException(status_code=401)
    
    body = await request.json()
    # Process webhook...
```

---

## Pagination

List endpoints support pagination:

```http
GET /documents?skip=0&limit=10
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of items to skip |
| `limit` | integer | 100 | Max items to return |

---

## Filtering

### By Document ID

Filter query results to specific document:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is X?",
    "document_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### By Date Range (Future)

```bash
curl "http://localhost:8000/documents?from_date=2024-01-01&to_date=2024-12-31"
```

---

## Batch Operations

### Batch Upload

Process multiple files:

```bash
for file in *.pdf; do
  curl -X POST http://localhost:8000/upload \
    -F "file=@$file"
done
```

### Batch Delete

Delete multiple documents:

```bash
for doc_id in "id1" "id2" "id3"; do
  curl -X DELETE "http://localhost:8000/documents/$doc_id"
done
```

---

## SDK Examples

### Python SDK

```python
import requests

class DocumentQueryClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def upload(self, file_path: str) -> dict:
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/upload",
                files={'file': f}
            )
        return response.json()
    
    def query(self, question: str, top_k: int = 5) -> dict:
        response = requests.post(
            f"{self.base_url}/query",
            json={'question': question, 'top_k': top_k}
        )
        return response.json()
    
    def list_documents(self) -> list:
        response = requests.get(f"{self.base_url}/documents")
        return response.json()['documents']
    
    def delete(self, document_id: str) -> dict:
        response = requests.delete(
            f"{self.base_url}/documents/{document_id}"
        )
        return response.json()

# Usage
client = DocumentQueryClient("http://localhost:8000")
client.upload("document.pdf")
result = client.query("What is this about?")
print(result['answer'])
```

### JavaScript/TypeScript SDK

```typescript
class DocumentQueryClient {
  constructor(private baseUrl: string) {}

  async upload(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  }

  async query(question: string, topK: number = 5): Promise<any> {
    const response = await fetch(`${this.baseUrl}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: topK }),
    });
    return response.json();
  }

  async listDocuments(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/documents`);
    const data = await response.json();
    return data.documents;
  }

  async delete(documentId: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/documents/${documentId}`,
      { method: 'DELETE' }
    );
    return response.json();
  }
}

// Usage
const client = new DocumentQueryClient('http://localhost:8000');
const result = await client.query('What is this about?');
console.log(result.answer);
```

---

## Testing

### API Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# Upload
curl -X POST http://localhost:8000/upload \
  -F "file=@test.pdf" \
  -w "\n%{http_code}\n"

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question?", "top_k": 3}'

# List
curl http://localhost:8000/documents

# Delete
curl -X DELETE http://localhost:8000/documents/test-id
```

### Load Testing

```bash
# Using Apache Bench
ab -n 100 -c 10 -p data.json -T "application/json" \
  http://localhost:8000/query
```

---

## Monitoring

### Prometheus Metrics (Future)

```python
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('api_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def monitor(request: Request, call_next):
    request_count.inc()
    with request_duration.time():
        response = await call_next(request)
    return response
```

### Health Check Alerts

Configure alerts for:
- `/health` returning non-200
- High error rate (5xx responses)
- Slow response times (>5s)

---

## Versioning

API versioning via URL path:

```
v1: http://localhost:8000/v1/query
v2: http://localhost:8000/v2/query
```

---

## Deprecation

When deprecating endpoints:

1. Add deprecation header:
   ```
   Deprecation: true
   Sunset: Sat, 01 Jan 2025 00:00:00 GMT
   ```

2. Return warning in response body

3. Update API documentation
