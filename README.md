# Document Query System (RAG)

AI-powered Document Query System using Retrieval Augmented Generation (RAG) for PDF document analysis and question answering.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Logging](#logging)

---

## Overview

This is a full-stack RAG (Retrieval Augmented Generation) system that allows you to:
- Upload PDF documents
- Ask questions about the documents
- Get AI-powered answers with source citations

### Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + FastAPI |
| Frontend | React + Vite + Tailwind CSS |
| Vector Database | FAISS (local) / Pinecone (cloud) |
| LLM | OpenAI GPT / Ollama (local) |
| Embeddings | OpenAI / Ollama |
| Cloud Storage | AWS S3 |
| Deployment | AWS Lambda + API Gateway |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client (Browser)                               │
│                        React Frontend (Port 3000)                       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTP/REST
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend (Port 8000)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │   Upload     │  │    Query     │  │   Document   │                 │
│  │   Endpoint   │  │   Endpoint   │  │   Manager    │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└────────┬─────────────────┬─────────────────┬─────────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│   Document      │ │    Vector      │ │     LLM       │
│   Processor    │ │    Store       │ │    Handler    │
│   (PyPDF2)    │ │   (FAISS)     │ │   (Ollama)    │
└────────────────┘ └────────────────┘ └────────────────┘
```

---

## Prerequisites

### Required Software

1. **Python 3.10+**
   ```bash
   python --version
   ```

2. **Node.js 18+**
   ```bash
   node --version
   ```

3. **npm or yarn**
   ```bash
   npm --version
   ```

4. **Git**
   ```bash
   git --version
   ```

### Optional: Ollama (for local LLM)

For local LLM functionality without OpenAI API:
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows - Download from https://ollama.com/download
```

---

## Quick Start

### Option 1: With Ollama (Local - Recommended)

```bash
# 1. Navigate to project
cd Docllm

# 2. Install Ollama models
ollama pull nomic-embed-text    # For embeddings
ollama pull llama3:8b          # For LLM

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Start backend (Terminal 1)
python main.py

# 6. Start frontend (Terminal 2)
cd frontend
npm run dev
```

### Option 2: With OpenAI API

```bash
# 1. Set OpenAI API key
export OPENAI_API_KEY=sk-your-key

# 2. Install dependencies
pip install -r requirements.txt

# 3. Update .env file
# Set USE_OPENAI=true
# Set OPENAI_API_KEY=your-key

# 4. Start server
python main.py
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Detailed Setup

### Backend Setup

#### 1. Clone and Navigate
```bash
cd Docllm
```

#### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
```

#### 5. Run the Server
```bash
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Document Query System starting up...
INFO:     Vector DB: faiss
INFO:     LLM: Ollama
```

---

### Frontend Setup

#### 1. Navigate to Frontend Directory
```bash
cd frontend
```

#### 2. Install Dependencies
```bash
npm install
```

#### 3. Configure API URL
Create `.env` file in `frontend/` directory:
```bash
VITE_API_URL=http://localhost:8000
```

#### 4. Start Development Server
```bash
npm run dev
```

Expected output:
```
  VITE v5.0.0  ready in 500 ms

  ➜  Local:   http://localhost:3000/
```

#### 5. Build for Production
```bash
npm run build
npm run preview
```

---

### Ollama Setup

#### 1. Install Ollama
**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from https://ollama.com/download

#### 2. Start Ollama Service
```bash
ollama serve
```

#### 3. Pull Required Models
```bash
# Embedding model (for document vectors)
ollama pull nomic-embed-text

# LLM model (for generating answers)
ollama pull llama3:8b

# Verify models installed
ollama list
```

Expected output:
```
NAME                ID          SIZE      MODIFIED
nomic-embed-text    0a109f42    274 MB    ...
llama3:8b           365c0bd3    4.7 GB    ...
```

#### 4. Test Ollama
```bash
# Test generation
curl http://localhost:11434/api/generate \
  -d '{"model":"llama3:8b","prompt":"Hello","stream":false}'

# Test embeddings
curl http://localhost:11434/api/embeddings \
  -d '{"model":"nomic-embed-text","prompt":"test"}'
```

---

## Configuration

### Environment Variables (.env file)

Create a `.env` file in the project root:

```env
# =============================================================================
# LLM Configuration
# =============================================================================

# Use OpenAI (true) or Ollama (false)
USE_OPENAI=false

# OpenAI Settings (if USE_OPENAI=true)
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-3.5-turbo

# Ollama Settings (if USE_OPENAI=false)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# =============================================================================
# Embedding Configuration
# =============================================================================

# For OpenAI: text-embedding-3-small, text-embedding-ada-002
# For Ollama: nomic-embed-text, all-minilm, etc.
EMBEDDING_MODEL=nomic-embed-text

# =============================================================================
# Vector Store Configuration
# =============================================================================

# Options: faiss (local), pinecone (cloud)
VECTOR_DB=faiss

# Pinecone Settings (if VECTOR_DB=pinecone)
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX=document-query-system
PINECONE_ENVIRONMENT=us-east-1

# =============================================================================
# AWS Configuration (Optional)
# =============================================================================

AWS_REGION=us-east-1
S3_BUCKET=your-s3-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# =============================================================================
# Document Processing
# =============================================================================

# Text chunk size (characters)
CHUNK_SIZE=1000

# Overlap between chunks
CHUNK_OVERLAP=200

# =============================================================================
# Server Configuration
# =============================================================================

HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### Configuration Options

| Variable | Description | Options |
|----------|-------------|---------|
| `USE_OPENAI` | Use OpenAI or local Ollama | `true` / `false` |
| `VECTOR_DB` | Vector database backend | `faiss` / `pinecone` |
| `EMBEDDING_MODEL` | Embedding model to use | `nomic-embed-text`, `text-embedding-3-small` |
| `OLLAMA_MODEL` | Ollama LLM model | `llama3:8b`, `qwen3.5`, `gemma:2b` |

---

## API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "vector_db": "faiss",
  "llm_type": "Ollama"
}
```

---

#### 2. Upload Document

```http
POST /upload
Content-Type: multipart/form-data
```

**Parameters:**
| Field | Type | Required | Description |
|--------|------|----------|-------------|
| `file` | File | Yes | PDF file to upload |
| `upload_to_s3` | Boolean | No | Upload to S3 (default: false) |

**Example (curl):**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "document_id": "abc123-def456-...",
  "filename": "document.pdf",
  "status": "success",
  "message": "Successfully indexed 5 chunks"
}
```

---

#### 3. Query Documents

```http
POST /query
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "What is the main topic?",
  "document_id": "optional-filter-by-doc-id",
  "top_k": 5
}
```

**Parameters:**
| Field | Type | Required | Description |
|--------|------|----------|-------------|
| `question` | String | Yes | Question to ask |
| `document_id` | String | No | Filter by specific document |
| `top_k` | Integer | No | Number of sources (default: 5, max: 20) |

**Example (curl):**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "top_k": 5}'
```

**Response:**
```json
{
  "answer": "The main topic is...",
  "sources": [
    {
      "text": "Document content preview...",
      "document_id": "abc123",
      "chunk_index": 0,
      "relevance_score": 0.95
    }
  ],
  "document_id": null
}
```

---

#### 4. List Documents

```http
GET /documents
```

**Response:**
```json
{
  "documents": [
    {
      "document_id": "abc123",
      "filename": "document.pdf",
      "num_chunks": 5,
      "s3_path": null
    }
  ],
  "total": 1
}
```

---

#### 5. Delete Document

```http
DELETE /documents/{document_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Document abc123-def456 deleted"
}
```

---

### API Documentation UI

FastAPI automatically generates interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Project Structure

```
Docllm/
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── Header.jsx
│   │   │   ├── UploadComponent.jsx
│   │   │   ├── QueryComponent.jsx
│   │   │   └── DocumentList.jsx
│   │   ├── services/
│   │   │   └── api.js          # API client
│   │   ├── App.jsx             # Main app component
│   │   └── main.jsx            # Entry point
│   ├── package.json
│   └── vite.config.js
├── main.py                     # FastAPI application
├── rag_service.py              # Core RAG logic
├── document_processor.py       # PDF processing
├── embeddings.py               # Embedding generation
├── vector_store.py             # Vector database
├── llm_handler.py              # LLM integration
├── s3_storage.py              # AWS S3 operations
├── config.py                  # Configuration
├── models.py                  # Data models
├── lambda_handler.py          # AWS Lambda handler
├── requirements.txt           # Python dependencies
├── template.yaml              # AWS SAM template
├── docker-compose.yml         # Docker setup
├── Dockerfile                 # Container build
├── start.bat                  # Windows startup script
├── start.sh                   # Linux/Mac startup script
├── .env                      # Environment variables
├── logs/
│   └── app.log              # Application logs
└── data/
    └── faiss_index/         # Local vector store data
```

---

## Deployment

### Option 1: Local Development

```bash
# Start backend
python main.py

# Start frontend (separate terminal)
cd frontend
npm run dev
```

### Option 2: Docker Compose

```bash
docker-compose up --build
```

### Option 3: AWS Lambda Deployment

#### Prerequisites
- AWS CLI configured
- AWS SAM CLI installed
- AWS credentials configured

#### Deploy with SAM
```bash
# Build the application
sam build

# Deploy to AWS
sam deploy --guided
```

---

## Troubleshooting

### Common Issues

#### 1. Ollama Connection Error

**Error:** `Cannot connect to Ollama`

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama
ollama serve
```

#### 2. Embedding Model Not Found

**Error:** `model "nomic-embed-text" not found`

**Solution:**
```bash
# Pull the embedding model
ollama pull nomic-embed-text

# Verify installation
ollama list
```

#### 3. Import Errors (Python)

**Error:** `ModuleNotFoundError`

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

#### 4. Port Already in Use

**Error:** `Port 8000 is already in use`

**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Linux/Mac
lsof -i :8000
kill -9 <process_id>
```

#### 5. CORS Error in Browser

**Solution:**
- Ensure frontend proxy is configured in `vite.config.js`
- Or enable CORS in backend (already enabled for all origins)

#### 6. S3 Upload Fails

**Solution:**
- Check AWS credentials in .env file
- Ensure bucket exists and has proper permissions

### Reset Vector Store

To reset all indexed documents:
```bash
# Stop the server
# Delete the vector store data
rm -rf data/faiss_index/

# Restart the server
python main.py
```

---

## Logging

### Log File Location
```
logs/app.log
```

### Log Format
```
2024-01-15 10:30:45,123 - module_name - LEVEL - message
```

### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General operational information
- `WARNING`: Potential issues
- `ERROR`: Errors that need attention
- `CRITICAL`: Critical system failures

### View Logs in Real-Time

**Linux/Mac:**
```bash
tail -f logs/app.log
```

**Windows:**
```bash
type logs\app.log
```

---

## API Client Examples

### Python
```python
import requests

API_URL = "http://localhost:8000"

# Upload document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{API_URL}/upload", files=files)
    print(response.json())

# Query
response = requests.post(
    f"{API_URL}/query",
    json={"question": "What is this about?", "top_k": 5}
)
print(response.json()["answer"])
```

### JavaScript
```javascript
const API_URL = "http://localhost:8000";

// Upload
const formData = new FormData();
formData.append("file", fileInput.files[0]);

const uploadRes = await fetch(`${API_URL}/upload`, {
  method: "POST",
  body: formData
});

// Query
const queryRes = await fetch(`${API_URL}/query`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({
    question: "What is this about?",
    top_k: 5
  })
});

const data = await queryRes.json();
console.log(data.answer);
```

### curl
```bash
# Health check
curl http://localhost:8000/health

# Upload
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "top_k": 5}'
```

---

## Performance Tips

1. **Use GPU**: Ollama runs faster with GPU acceleration
2. **Smaller Chunks**: Reduce `CHUNK_SIZE` for faster processing
3. **Limit Documents**: Too many large documents can slow down queries
4. **Use SSD**: Vector store performs better on SSD storage
5. **Pre-load Models**: Keep Ollama running to avoid model loading delays

---

## Security Notes

1. **Never commit `.env` file** to version control
2. **Use environment variables** for production secrets
3. **Enable HTTPS** for production deployments
4. **Implement authentication** for public-facing APIs
5. **Validate file uploads** to prevent malicious files
6. **Rate limiting** should be implemented for production

---

## License

MIT License

---

## Support

For issues and feature requests:
- Create an issue on GitHub
- Check troubleshooting section
- Review logs at `logs/app.log`

---

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Ollama](https://ollama.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [OpenAI](https://openai.com/)
