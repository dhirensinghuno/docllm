import { useState, useEffect } from 'react';
import Header from './components/Header';
import UploadComponent from './components/UploadComponent';
import QueryComponent from './components/QueryComponent';
import DocumentList from './components/DocumentList';

function App() {
  const [apiStatus, setApiStatus] = useState('checking');
  const [documents, setDocuments] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    setApiStatus('checking');
    try {
      const { api } = await import('./services/api');
      await api.healthCheck();
      setApiStatus('healthy');
    } catch (error) {
      console.error('API Health Check Failed:', error);
      setApiStatus('error');
    }
  };

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
  };

  const handleDocumentsLoaded = (docs) => {
    setDocuments(docs);
  };

  return (
    <div className="min-h-screen">
      <Header apiStatus={apiStatus} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {apiStatus === 'error' && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
            <p className="font-medium">Unable to connect to the API server</p>
            <p className="text-sm mt-1">
              Make sure the backend is running at http://localhost:8000
            </p>
            <button
              onClick={checkApiHealth}
              className="mt-3 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-sm transition-colors"
            >
              Retry Connection
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <UploadComponent onUploadSuccess={handleUploadSuccess} />
            <DocumentList 
              refreshTrigger={refreshKey} 
              onDocumentsLoaded={handleDocumentsLoaded}
            />
          </div>

          <div className="lg:sticky lg:top-24 lg:self-start">
            <QueryComponent documents={documents} />
          </div>
        </div>

        <footer className="mt-12 text-center text-sm text-slate-500">
          <p>Document Query System powered by RAG & AI</p>
        </footer>
      </main>
    </div>
  );
}

export default App;
