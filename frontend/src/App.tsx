import { useEffect, useState } from 'react';
import { api } from './services/api';
import type { SystemHealth } from './types/review';
import { Navbar } from './components/Navbar';
import { OverviewPage } from './pages/OverviewPage';
import { CodeReviewPage } from './pages/CodeReviewPage';
import { RepositoryIndexPage } from './pages/RepositoryIndexPage';
import { GitHubIntegrationPage } from './pages/GitHubIntegrationPage';
import { SettingsPage } from './pages/SettingsPage';
import { ShieldCheck, GitBranch, Cpu, Database } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
      setIsConnected(true);
    } catch {
      setIsConnected(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectReview = (reviewId: string) => {
    setSelectedReviewId(reviewId);
    setActiveTab('review');
  };

  const handleNewReview = () => {
    setSelectedReviewId(null);
    setActiveTab('review');
  };

  const isLLMAvailable = health?.components.llm_provider.is_configured ?? false;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-600/30">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        isConnected={isConnected}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <OverviewPage
            onSelectReview={handleSelectReview}
            onNewReview={handleNewReview}
          />
        )}

        {activeTab === 'review' && (
          <CodeReviewPage
            initialReviewId={selectedReviewId}
            onClearInitialReviewId={() => setSelectedReviewId(null)}
            isLLMAvailable={isLLMAvailable}
          />
        )}

        {activeTab === 'index' && <RepositoryIndexPage />}

        {activeTab === 'github' && <GitHubIntegrationPage />}

        {activeTab === 'settings' && <SettingsPage />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
            <span className="font-semibold text-slate-400">
              Multi-Agent Enterprise Code Reviewer & PR Quality Gate
            </span>
            <span className="font-mono text-[11px] text-slate-600">v1.0.0</span>
          </div>

          <div className="flex items-center gap-4 text-[11px] font-mono text-slate-500">
            <span className="flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" /> LangGraph Orchestration
            </span>
            <span className="flex items-center gap-1">
              <Database className="w-3.5 h-3.5 text-cyan-400" /> Qdrant Semantic Context
            </span>
            <span className="flex items-center gap-1">
              <GitBranch className="w-3.5 h-3.5 text-emerald-400" /> Deterministic AST Guardrails
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
