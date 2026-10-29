import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { CodeChunkResult, IndexStatusResponse } from '../types/review';
import { Database, Search, FolderPlus, Radio, CheckCircle2, AlertCircle, FileCode, Layers } from 'lucide-react';

export const RepositoryIndexPage: React.FC = () => {
  const [directoryPath, setDirectoryPath] = useState('backend/app');
  const [maxFiles, setMaxFiles] = useState(100);
  const [indexing, setIndexing] = useState(false);
  const [indexResult, setIndexResult] = useState<IndexStatusResponse | null>(null);
  const [statusInfo, setStatusInfo] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Search state
  const [query, setQuery] = useState('database query injection OR subprocess');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<CodeChunkResult[]>([]);

  const fetchIndexStatus = async () => {
    try {
      const data = await api.getIndexStatus();
      setStatusInfo(data);
    } catch {
      // silent
    }
  };

  useEffect(() => {
    fetchIndexStatus();
  }, []);

  const handleIndexDirectory = async () => {
    if (!directoryPath.trim()) return;
    try {
      setIndexing(true);
      setError(null);
      const res = await api.indexDirectory(directoryPath.trim(), maxFiles);
      setIndexResult(res);
      await fetchIndexStatus();
    } catch (err: any) {
      setError(err.message || 'Indexing failed');
    } finally {
      setIndexing(false);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    try {
      setSearching(true);
      setError(null);
      const res = await api.searchCodebase(query.trim(), 5);
      setSearchResults(res.results);
    } catch (err: any) {
      setError(err.message || 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Database className="w-5 h-5 text-cyan-400" />
              Qdrant Semantic Code Index & Vector Search
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Index local Python repositories into chunked embeddings to provide semantic context for review agents.
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300">
            <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span>Mode: {statusInfo?.storage_mode || 'Qdrant (Embedded In-Memory)'}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Indexing Form & Diagnostic Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Index Trigger Form (7 columns) */}
        <div className="lg:col-span-7 p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <FolderPlus className="w-4 h-4 text-indigo-400" />
            Index Local Directory
          </h2>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Target Directory Path:</label>
              <input
                type="text"
                value={directoryPath}
                onChange={(e) => setDirectoryPath(e.target.value)}
                placeholder="e.g. backend/app or d:\PROJECT\backend"
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 font-mono text-xs focus:outline-none focus:border-indigo-500"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Excludes .git, venv, .env, node_modules, and sensitive credential files automatically.
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Max Files to Index:</span>
              <input
                type="number"
                min={1}
                max={500}
                value={maxFiles}
                onChange={(e) => setMaxFiles(parseInt(e.target.value) || 100)}
                className="w-20 px-2 py-1 rounded bg-slate-950 border border-slate-700 text-right text-slate-200 font-mono text-xs"
              />
            </div>

            <button
              onClick={handleIndexDirectory}
              disabled={indexing}
              className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-md transition disabled:opacity-50"
            >
              {indexing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  Chunking & Vectorizing Files...
                </>
              ) : (
                <>
                  <Database className="w-4 h-4" />
                  Start Indexing Directory
                </>
              )}
            </button>
          </div>

          {indexResult && (
            <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-xs flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">{indexResult.message}</p>
                <p className="text-[11px] text-emerald-400/80 mt-0.5">
                  Indexed {indexResult.indexed_files} files into {indexResult.total_chunks} vector points.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Index Diagnostics (5 columns) */}
        <div className="lg:col-span-5 p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-cyan-400" />
            Vector Store Status
          </h2>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-750 flex justify-between">
              <span className="text-slate-400">Storage Engine:</span>
              <span className="font-mono text-slate-200">{statusInfo?.storage_mode || 'Qdrant (In-Memory)'}</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-750 flex justify-between">
              <span className="text-slate-400">Total Indexed Chunks:</span>
              <span className="font-mono text-slate-200 font-bold">{statusInfo?.total_chunks || 0}</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-750 flex justify-between">
              <span className="text-slate-400">Embedding Dimension:</span>
              <span className="font-mono text-slate-200">{statusInfo?.dimension || 384}</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-750 flex justify-between">
              <span className="text-slate-400">Embedding Provider:</span>
              <span className="font-mono text-slate-200">{statusInfo?.embedding_provider || 'LocalHashing'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Semantic Vector Search Section */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <Search className="w-4 h-4 text-indigo-400" />
          Semantic Code Search
        </h2>

        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Query concept, symbol, or API usage (e.g. SQL injection, subprocess.run, auth tokens)"
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 font-mono text-xs focus:outline-none focus:border-indigo-500"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </form>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="space-y-3 pt-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Top Retrieved Chunks ({searchResults.length})
            </h3>
            {searchResults.map((r) => (
              <div key={r.chunk_id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                  <span className="text-indigo-400 font-bold flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5" />
                    {r.file_path} (Lines {r.start_line} - {r.end_line})
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    Similarity: {(r.score * 100).toFixed(1)}%
                  </span>
                </div>
                <pre className="p-3 rounded-lg bg-slate-900 border border-slate-850 text-slate-300 font-mono text-xs overflow-x-auto leading-relaxed">
                  {r.content}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
