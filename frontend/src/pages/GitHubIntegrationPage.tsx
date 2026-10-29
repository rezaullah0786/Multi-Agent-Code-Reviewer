import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { GitHubPRReviewEventResponse } from '../types/review';
import { GateStatusBadge } from '../components/GateStatusBadge';
import { GitPullRequest, ShieldCheck, Key, Lock, AlertCircle, Copy, Play } from 'lucide-react';

export const GitHubIntegrationPage: React.FC = () => {
  const [statusData, setStatusData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // PR Simulator State
  const [patchCode, setPatchCode] = useState(
    `import os\n\ndef process_user_file(file_name):\n    # Unsafe shell command construction\n    os.system("cat " + file_name)\n`
  );
  const [patchFile, setPatchFile] = useState('src/file_utils.py');
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<GitHubPRReviewEventResponse | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await api.getGitHubStatus();
      setStatusData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load GitHub integration status');
    }
  };

  const handleSimulatePR = async () => {
    try {
      setSimulating(true);
      setError(null);
      const res = await api.simulateGitHubWebhook(patchCode, patchFile);
      setSimulationResult(res);
    } catch (err: any) {
      setError(err.message || 'PR simulation failed');
    } finally {
      setSimulating(false);
    }
  };

  const copyWebhookUrl = () => {
    const url = `${window.location.origin}/api/v1/webhooks/github`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <GitPullRequest className="w-5 h-5 text-indigo-400" />
              GitHub Pull Request Webhook Quality Gate
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Automated PR gate inspection with HMAC-SHA256 signature verification and inline review comments.
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300">
            <span
              className={`w-2 h-2 rounded-full ${
                statusData?.dry_run_mode ? 'bg-amber-400' : 'bg-emerald-400'
              }`}
            />
            <span>{statusData?.dry_run_mode ? 'Mode: DRY-RUN (Safe Demo)' : 'Mode: LIVE (Publishing)'}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Integration Diagnostics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase">
            <Key className="w-4 h-4 text-indigo-400" />
            <span>Webhook Secret Verification</span>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span
              className={`text-sm font-bold ${
                statusData?.webhook_secret_configured ? 'text-emerald-400' : 'text-slate-400'
              }`}
            >
              {statusData?.webhook_secret_configured ? 'Configured (HMAC Active)' : 'Optional (Permissive in demo)'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 font-mono">GITHUB_WEBHOOK_SECRET</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase">
            <Lock className="w-4 h-4 text-cyan-400" />
            <span>GitHub Publishing Token</span>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span
              className={`text-sm font-bold ${
                statusData?.github_token_configured ? 'text-emerald-400' : 'text-slate-400'
              }`}
            >
              {statusData?.github_token_configured ? 'Configured' : 'Unset (Dry-run mode)'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 font-mono">GITHUB_TOKEN</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Replay Protection</span>
          </div>
          <div className="mt-2 text-sm font-bold text-emerald-400">Active</div>
          <p className="text-[11px] text-slate-500 mt-1">Deduplicates delivery UUIDs</p>
        </div>
      </div>

      {/* Webhook Configuration Guide */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
          Webhook Configuration Instructions
        </h2>

        <div className="space-y-3 text-xs text-slate-300">
          <p>To connect a GitHub repository to this PR Quality Gate:</p>
          <ol className="list-decimal list-inside space-y-2 text-slate-400">
            <li>
              Go to your GitHub repository <span className="font-mono text-slate-300">Settings &gt; Webhooks &gt; Add webhook</span>.
            </li>
            <li className="flex items-center gap-2">
              <span>Payload URL:</span>
              <code className="px-2 py-0.5 rounded bg-slate-950 font-mono text-indigo-300 border border-slate-800">
                {window.location.origin}/api/v1/webhooks/github
              </code>
              <button
                onClick={copyWebhookUrl}
                className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1 text-[11px]"
              >
                <Copy className="w-3 h-3" />
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </li>
            <li>
              Content type: <span className="font-mono text-slate-300">application/json</span>.
            </li>
            <li>
              Secret: Enter the secret defined in <span className="font-mono text-slate-300">GITHUB_WEBHOOK_SECRET</span>.
            </li>
            <li>
              Events: Select <span className="font-mono text-slate-300">Let me select individual events</span> and check <span className="font-mono text-slate-300">Pull requests</span>.
            </li>
          </ol>
        </div>
      </div>

      {/* Interactive PR Webhook Simulator */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Play className="w-4 h-4 text-indigo-400" />
            Pull Request Webhook Simulator (Dry-Run Test)
          </h2>
          <span className="text-xs text-slate-500 font-mono">Exercises webhook handler without requiring live webhook</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-400 mb-1">Changed File Path:</label>
            <input
              type="text"
              value={patchFile}
              onChange={(e) => setPatchFile(e.target.value)}
              className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 font-mono text-xs focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1">PR Diff / Added Code:</label>
          <textarea
            value={patchCode}
            onChange={(e) => setPatchCode(e.target.value)}
            rows={6}
            className="w-full p-3 rounded-lg bg-slate-950 border border-slate-700 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500 leading-relaxed"
          />
        </div>

        <button
          onClick={handleSimulatePR}
          disabled={simulating}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center gap-2 transition disabled:opacity-50"
        >
          {simulating ? 'Evaluating Webhook Payload...' : 'Send Simulated PR Webhook Event'}
        </button>

        {/* Simulation Output */}
        {simulationResult && (
          <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <GateStatusBadge status={simulationResult.gate_status} size="sm" />
                <span className="text-xs font-bold text-slate-200">
                  PR #{simulationResult.pr_number} Evaluation ({simulationResult.dry_run ? 'Dry-Run' : 'Live'})
                </span>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {simulationResult.comments_generated.length} review comments generated
              </span>
            </div>

            <p className="text-xs text-slate-400">{simulationResult.message}</p>

            {simulationResult.comments_generated.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <span className="text-[11px] font-bold uppercase text-slate-400">Inline Review Comments:</span>
                {simulationResult.comments_generated.map((c, i) => (
                  <div key={i} className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
                    <div className="font-mono text-[11px] text-indigo-300 font-bold">
                      {c.path}:{c.line}
                    </div>
                    <pre className="text-slate-300 whitespace-pre-wrap font-sans text-xs">{c.body}</pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
