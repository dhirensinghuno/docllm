import { useState } from 'react';
import { Upload, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function UploadComponent({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [uploadToS3, setUploadToS3] = useState(false);
  const [result, setResult] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
        setMessage(null);
        setResult(null);
      } else {
        setMessage({ type: 'error', text: 'Please upload a PDF file' });
      }
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile);
        setMessage(null);
        setResult(null);
      } else {
        setMessage({ type: 'error', text: 'Please upload a PDF file' });
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setMessage(null);

    try {
      const { api } = await import('../services/api');
      const response = await api.uploadDocument(file, uploadToS3);
      setResult(response);
      setMessage({ type: 'success', text: response.message });
      setFile(null);
      if (onUploadSuccess) onUploadSuccess();
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
    } finally {
      setUploading(false);
    }
  };

  const clearFile = () => {
    setFile(null);
    setMessage(null);
    setResult(null);
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Upload className="w-5 h-5 text-indigo-400" />
        Upload Document
      </h2>

      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
          dragActive
            ? 'border-indigo-400 bg-indigo-500/10'
            : 'border-slate-600 hover:border-slate-500'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={uploading}
        />

        {file ? (
          <div className="animate-fade-in">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-400" />
            <p className="text-lg font-medium text-slate-200">{file.name}</p>
            <p className="text-sm text-slate-400 mt-1">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        ) : (
          <div>
            <Upload className="w-12 h-12 mx-auto mb-3 text-slate-500" />
            <p className="text-slate-300">
              Drag & drop a PDF file here, or click to select
            </p>
            <p className="text-sm text-slate-500 mt-2">Only PDF files are supported</p>
          </div>
        )}
      </div>

      {file && (
        <div className="mt-4 flex items-center gap-4">
          <button
            onClick={clearFile}
            className="flex items-center gap-2 px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors"
            disabled={uploading}
          >
            <X className="w-4 h-4" />
            Clear
          </button>

          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={uploadToS3}
              onChange={(e) => setUploadToS3(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-indigo-500 focus:ring-indigo-500"
            />
            Upload to S3
          </label>

          <button
            onClick={handleUpload}
            disabled={uploading}
            className="ml-auto flex items-center gap-2 px-6 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload
              </>
            )}
          </button>
        </div>
      )}

      {message && (
        <div
          className={`mt-4 p-4 rounded-lg flex items-center gap-3 animate-fade-in ${
            message.type === 'success'
              ? 'bg-green-500/10 border border-green-500/30 text-green-400'
              : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {result && (
        <div className="mt-4 p-4 bg-slate-700/50 rounded-lg animate-fade-in">
          <p className="text-sm text-slate-300">
            Document ID: <code className="text-indigo-400">{result.document_id}</code>
          </p>
          <p className="text-sm text-slate-400 mt-1">
            Chunks indexed: {result.num_chunks}
          </p>
        </div>
      )}
    </div>
  );
}
