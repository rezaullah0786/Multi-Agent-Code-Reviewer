import React from 'react';
import { ShieldCheck, Code2, Database, GitPullRequest, Settings as SettingsIcon, Radio } from 'lucide-react';
import type { SystemHealth } from '../types/review';

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  health: SystemHealth | null;
  isConnected: boolean;
}

export const Navbar: React.FC<Props> = ({ activeTab, setActiveTab, health, isConnected }) => {
  const tabs = [
    { id: 'overview', label: 'Overview', icon: ShieldCheck },
    { id: 'review', label: 'Code Review', icon: Code2 },
    { id: 'index', label: 'Repository Index', icon: Database },
    { id: 'github', label: 'GitHub PR Gate', icon: GitPullRequest },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-100 text-lg tracking-tight">CodeReviewer</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  LangGraph PR Gate
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">Multi-Agent Enterprise Code Reviewer & PR Quality Gate</p>
            </div>
          </div>

          <nav className="hidden md:flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-800 text-indigo-400 border border-slate-700 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                }`}
              />
              <span className="text-slate-300 font-mono text-[11px] hidden sm:inline">
                {isConnected ? (health?.mode === 'production' ? 'PROD (AI active)' : 'LOCAL (AST demo)') : 'OFFLINE'}
              </span>
            </div>

            {health?.components.vector_store && (
              <span className="hidden lg:inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
                <Radio className="w-3 h-3 text-cyan-400" />
                {health.components.vector_store.storage_mode.includes('Embedded') ? 'Qdrant (In-Memory)' : 'Qdrant (Server)'}
              </span>
            )}
          </div>
        </div>

        {/* Mobile navigation row */}
        <div className="flex md:hidden overflow-x-auto py-2 border-t border-slate-800/80 gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs whitespace-nowrap font-medium ${
                  isActive ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30' : 'text-slate-400'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
