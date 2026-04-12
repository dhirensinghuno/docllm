// Author: dhirenkumarsingh
import { useState, useEffect } from 'react';
import { Brain, Settings } from 'lucide-react';

export default function Header({ apiStatus }) {
  return (
    <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Document Query System</h1>
              <p className="text-xs text-slate-400">AI-powered RAG System</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  apiStatus === 'healthy'
                    ? 'bg-green-400'
                    : apiStatus === 'error'
                    ? 'bg-red-400'
                    : 'bg-yellow-400'
                }`}
              />
              <span className="text-sm text-slate-400">
                API: {apiStatus === 'healthy' ? 'Connected' : apiStatus === 'error' ? 'Error' : 'Checking...'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
