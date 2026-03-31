import { useState, useEffect } from 'react';
import { FileText, Trash2, RefreshCw, Loader2, Database } from 'lucide-react';

export default function DocumentList({ refreshTrigger, onDocumentsLoaded }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(null);
  const [error, setError] = useState(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const { api } = await import('../services/api');
      const response = await api.listDocuments();
      setDocuments(response.documents || []);
      if (onDocumentsLoaded) onDocumentsLoaded(response.documents || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [refreshTrigger]);

  const handleDelete = async (documentId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    setDeleting(documentId);
    try {
      const { api } = await import('../services/api');
      await api.deleteDocument(documentId);
      setDocuments((prev) => prev.filter((doc) => doc.document_id !== documentId));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-400" />
          Documents
          {documents.length > 0 && (
            <span className="text-sm font-normal text-slate-400">
              ({documents.length})
            </span>
          )}
        </h2>
        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="p-2 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 mx-auto mb-3 text-slate-600" />
          <p className="text-slate-400">No documents uploaded yet</p>
          <p className="text-sm text-slate-500 mt-1">
            Upload a PDF to get started
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {documents.map((doc) => (
            <div
              key={doc.document_id}
              className="flex items-center gap-4 p-4 bg-slate-700/30 rounded-lg border border-slate-600/50 hover:border-slate-500/50 transition-colors group"
            >
              <div className="flex-shrink-0">
                <FileText className="w-8 h-8 text-indigo-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-200 truncate">{doc.filename}</p>
                <p className="text-sm text-slate-400">
                  {doc.num_chunks} chunks indexed
                </p>
                {doc.s3_path && (
                  <p className="text-xs text-slate-500 truncate mt-1">
                    S3: {doc.s3_path}
                  </p>
                )}
              </div>
              <div className="flex-shrink-0">
                <button
                  onClick={() => handleDelete(doc.document_id)}
                  disabled={deleting === doc.document_id}
                  className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                  title="Delete document"
                >
                  {deleting === doc.document_id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
