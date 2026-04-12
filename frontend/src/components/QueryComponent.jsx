// Author: dhirenkumarsingh
import { useState } from 'react';
import { Send, Loader2, MessageSquare } from 'lucide-react';

export default function QueryComponent({ documents, onQuerySuccess }) {
  const [question, setQuestion] = useState('');
  const [selectedDoc, setSelectedDoc] = useState('');
  const [topK, setTopK] = useState(5);
  const [querying, setQuerying] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setQuerying(true);
    setError(null);
    setResult(null);

    try {
      const { api } = await import('../services/api');
      const response = await api.query(
        question,
        selectedDoc || null,
        parseInt(topK)
      );
      
      const queryEntry = {
        question,
        timestamp: new Date().toLocaleTimeString(),
        ...response
      };
      
      setResult(queryEntry);
      setHistory(prev => [queryEntry, ...prev.slice(0, 9)]);
      setQuestion('');
      
      if (onQuerySuccess) onQuerySuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setQuerying(false);
    }
  };

  const clearHistory = () => {
    setHistory([]);
    setResult(null);
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <MessageSquare className="w-5 h-5 text-indigo-400" />
        Ask Questions
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your documents..."
            rows={3}
            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none"
            disabled={querying}
          />
        </div>

        <div className="flex gap-4 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm text-slate-400 mb-1">
              Filter by Document (optional)
            </label>
            <select
              value={selectedDoc}
              onChange={(e) => setSelectedDoc(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
              disabled={querying}
            >
              <option value="">All Documents</option>
              {documents.map((doc) => (
                <option key={doc.document_id} value={doc.document_id}>
                  {doc.filename} ({doc.num_chunks} chunks)
                </option>
              ))}
            </select>
          </div>

          <div className="w-32">
            <label className="block text-sm text-slate-400 mb-1">Top K</label>
            <select
              value={topK}
              onChange={(e) => setTopK(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
              disabled={querying}
            >
              {[1, 3, 5, 10, 15, 20].map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={!question.trim() || querying}
              className="flex items-center gap-2 px-6 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {querying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Thinking...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Ask
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 animate-fade-in">
          <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-lg p-4 mb-4">
            <p className="text-indigo-300 font-medium mb-2">Q: {result.question}</p>
            <p className="text-slate-200 whitespace-pre-wrap">{result.answer}</p>
          </div>

          {result.sources && result.sources.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-400">
                Sources ({result.sources.length})
              </h4>
              {result.sources.map((source, idx) => (
                <div
                  key={idx}
                  className="bg-slate-700/30 rounded-lg p-3 border border-slate-600/50"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs text-slate-500">
                      Chunk {source.chunk_index + 1}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded">
                      Score: {(source.relevance_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 line-clamp-3">
                    {source.text}...
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {history.length > 0 && !result && (
        <div className="mt-6">
          <div className="flex justify-between items-center mb-3">
            <h4 className="text-sm font-medium text-slate-400">Recent Questions</h4>
            <button
              onClick={clearHistory}
              className="text-xs text-slate-500 hover:text-slate-300"
            >
              Clear
            </button>
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {history.map((item, idx) => (
              <div
                key={idx}
                className="p-3 bg-slate-700/30 rounded-lg text-sm text-slate-400 cursor-pointer hover:bg-slate-700/50"
                onClick={() => setResult(item)}
              >
                <p className="text-slate-300">{item.question}</p>
                <p className="text-xs text-slate-500 mt-1">{item.timestamp}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
