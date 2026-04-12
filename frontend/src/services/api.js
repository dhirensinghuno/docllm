// Author: dhirenkumarsingh
const API_BASE = import.meta.env.VITE_API_URL || '/api';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      headers: {
        ...options.headers,
      },
      ...options,
    };

    if (options.body instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'An error occurred');
      }
      
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  async healthCheck() {
    return this.request('/health');
  }

  async uploadDocument(file, uploadToS3 = false) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('upload_to_s3', uploadToS3);

    return this.request('/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async query(question, documentId = null, topK = 5) {
    return this.request('/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        document_id: documentId,
        top_k: topK,
      }),
    });
  }

  async listDocuments() {
    return this.request('/documents');
  }

  async deleteDocument(documentId) {
    return this.request(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  }
}

export const api = new ApiService();
export default api;
