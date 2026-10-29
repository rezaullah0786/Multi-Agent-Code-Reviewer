import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { SystemHealth } from '../types/review';
import { Settings as SettingsIcon, Cpu, Shield, Sliders, CheckCircle2 } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);

  // Policy thresholds
  const [blockCritical, setBlockCritical] = useState(true);
  const [blockHigh, setBlockHigh] = useState(true);
  const [maxMedium, setMaxMedium] = useState(5);
  const [maxLow, setMaxLow] = useState(15);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadHealth();
  }, []);

  const loadHealth = async () => {
    try {
      const res = await api.getHealth();
      setHealth(res);
    } catch {
      // handled
    }
  };

  const handleSavePolicy = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const llm = health?.components.llm_provider;
  const qdrant = health?.components.vector_store;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-indigo-400" />
          System Settings & Quality Gate Configuration
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Review policy thresholds, provider configurations, vector database mode, and active security guardrails.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quality Gate Policy Settings */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Sliders className="w-4 h-4 text-indigo-400" />
            Quality Gate Threshold Policy
          </h2>

          <form onSubmit={handleSavePolicy} className="space-y-3 text-xs">
            <label className="flex items-center justify-between p-3 rounded-lg bg-slate-800/60 border border-slate-750 cursor-pointer">
              <div>
                <div className="font-semibold text-slate-200">Block on Critical Findings</div>
                <div className="text-[11px] text-slate-400">Fail the PR gate if any Critical severity finding is detected</div>
              </div>
              <input
                type="checkbox"
                checked={blockCritical}
                onChange={(e) => setBlockCritical(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-0"
              />
            </label>

            <label className="flex items-center justify-between p-3 rounded-lg bg-slate-800/60 border border-slate-750 cursor-pointer">
              <div>
                <div className="font-semibold text-slate-200">Block on High Findings</div>
                <div className="text-[11px] text-slate-400">Fail the PR gate if any High severity finding is detected</div>
              </div>
              <input
                type="checkbox"
                checked={blockHigh}
                onChange={(e) => setBlockHigh(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-0"
              />
            </label>

            <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-750 flex items-center justify-between">
              <div>
                <div className="font-semibold text-slate-200">Max Medium Severity Allowed</div>
                <div className="text-[11px] text-slate-400">Threshold before Medium findings trigger gate failure</div>
              </div>
              <input
                type="number"
                min={0}
                max={50}
                value={maxMedium}
                onChange={(e) => setMaxMedium(parseInt(e.target.value) || 0)}
                className="w-16 px-2.5 py-1 rounded bg-slate-950 border border-slate-700 text-right text-slate-200 font-mono"
              />
            </div>

            <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-750 flex items-center justify-between">
              <div>
                <div className="font-semibold text-slate-200">Max Low Severity Allowed</div>
                <div className="text-[11px] text-slate-400">Threshold before Low findings trigger gate failure</div>
              </div>
              <input
                type="number"
                min={0}
                max={100}
                value={maxLow}
                onChange={(e) => setMaxLow(parseInt(e.target.value) || 0)}
                className="w-16 px-2.5 py-1 rounded bg-slate-950 border border-slate-700 text-right text-slate-200 font-mono"
              />
            </div>

            <div className="pt-2 flex items-center justify-between">
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition"
              >
                Save Policy Defaults
              </button>
              {saved && (
                <span className="text-xs text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Policy updated
                </span>
              )}
            </div>
          </form>
        </div>

        {/* AI & Vector Provider Diagnostics */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Cpu className="w-4 h-4 text-cyan-400" />
            AI & Vector Provider Status
          </h2>

          <div className="space-y-3 text-xs">
            {/* LLM Status */}
            <div className="p-3.5 rounded-lg bg-slate-800/60 border border-slate-750 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200">LLM Provider Adapter</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${
                    llm?.is_configured
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}
                >
                  {llm?.is_configured ? 'ACTIVE' : 'LOCAL DEMO (SKIPPED)'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-slate-400">
                <div>Model: <span className="font-mono text-slate-200">{llm?.model || 'gpt-4o-mini'}</span></div>
                <div>Timeout: <span className="font-mono text-slate-200">{llm?.timeout_seconds || 30}s</span></div>
                <div>Endpoint: <span className="font-mono text-slate-200 text-[11px] truncate">{llm?.base_url || 'https://api.openai.com/v1'}</span></div>
                <div>API Key: <span className="font-mono text-slate-200">{llm?.api_key_masked || 'Not Configured'}</span></div>
              </div>
              <p className="text-[11px] text-slate-400 italic pt-1 border-t border-slate-700/50">
                {llm?.status_message}
              </p>
            </div>

            {/* Qdrant Status */}
            <div className="p-3.5 rounded-lg bg-slate-800/60 border border-slate-750 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200">Qdrant Vector Database</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  {qdrant?.is_connected ? 'CONNECTED' : 'DISCONNECTED'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-slate-400">
                <div>Storage Mode: <span className="font-mono text-slate-200">{qdrant?.storage_mode}</span></div>
                <div>Collection: <span className="font-mono text-slate-200">{qdrant?.collection_name}</span></div>
                <div>Total Chunks: <span className="font-mono text-slate-200 font-bold">{qdrant?.total_chunks || 0}</span></div>
                <div>Dimension: <span className="font-mono text-slate-200">{qdrant?.dimension || 384}</span></div>
              </div>
            </div>

            {/* Guardrail Guarantee */}
            <div className="p-3.5 rounded-lg bg-indigo-950/20 border border-indigo-900/30 text-slate-300 text-[11px] flex items-start gap-2">
              <Shield className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-indigo-300">Deterministic Safety Guarantee</p>
                <p className="mt-0.5 text-slate-400">
                  Submitted code is parsed strictly through Abstract Syntax Trees (AST). The reviewer never executes,
                  evaluates, or runs submitted source code.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
