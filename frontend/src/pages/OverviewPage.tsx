import React, { useEffect, useState } from 'react';
import type { MetricsSummary, ReviewSummary } from '../types/review';
import { api } from '../services/api';
import { GateStatusBadge } from '../components/GateStatusBadge';
import { ShieldCheck, ShieldAlert, CheckCircle, Flame, Layers, ArrowUpRight, RefreshCw } from 'lucide-react';

interface Props {
  onSelectReview: (reviewId: string) => void;
  onNewReview: () => void;
}

export const OverviewPage: React.FC<Props> = ({ onSelectReview, onNewReview }) => {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [recentReviews, setRecentReviews] = useState<ReviewSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [m, revs] = await Promise.all([api.getMetrics(), api.listReviews(10)]);
      setMetrics(m);
      setRecentReviews(revs);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const totalReviews = metrics?.total_reviews || 0;
  const passedGates = metrics?.passed_gates || 0;
  const failedGates = metrics?.failed_gates || 0;
  const passRate = totalReviews > 0 ? Math.round((passedGates / totalReviews) * 100) : 100;

  const severityOrder = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];
  const totalFindingsCount = metrics
    ? Object.values(metrics.severity_distribution || {}).reduce((a, b) => a + b, 0)
    : 0;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 bg-gradient-to-r from-slate-900 via-slate-850 to-indigo-950/40 border border-slate-800 rounded-xl shadow-lg">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Enterprise PR Quality Gate & Review Overview</h1>
          <p className="text-sm text-slate-400 mt-1">
            Automated multi-agent inspection with deterministic AST guardrails, Qdrant semantic context, and configurable gate policies.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={onNewReview}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm shadow-md shadow-indigo-600/20 transition"
          >
            Start New Review
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Reviews</span>
            <Layers className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-slate-100">{totalReviews}</div>
          <p className="text-xs text-slate-500 mt-1">Inspected submissions</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Pass Rate</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-emerald-400">{passRate}%</div>
          <p className="text-xs text-slate-500 mt-1">{passedGates} gates passed</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Blocked PRs</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-rose-400">{failedGates}</div>
          <p className="text-xs text-slate-500 mt-1">Violated threshold policy</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Findings</span>
            <Flame className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-amber-400">{totalFindingsCount}</div>
          <p className="text-xs text-slate-500 mt-1">Security, perf & style</p>
        </div>
      </div>

      {/* Distribution Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-4">Findings by Severity</h2>
          <div className="space-y-3">
            {severityOrder.map((sev) => {
              const count = metrics?.severity_distribution?.[sev] || 0;
              const pct = totalFindingsCount > 0 ? Math.round((count / totalFindingsCount) * 100) : 0;
              const barColors: Record<string, string> = {
                CRITICAL: 'bg-red-500',
                HIGH: 'bg-orange-500',
                MEDIUM: 'bg-amber-400',
                LOW: 'bg-blue-400',
                INFO: 'bg-slate-500',
              };
              return (
                <div key={sev}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-300">{sev}</span>
                    <span className="text-slate-400 font-mono">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${barColors[sev] || 'bg-slate-500'} transition-all duration-500`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Category Distribution */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-4">Findings by Category</h2>
          <div className="space-y-3">
            {['SECURITY', 'PERFORMANCE', 'STYLE', 'SYNTAX'].map((cat) => {
              const count = metrics?.category_distribution?.[cat] || 0;
              const pct = totalFindingsCount > 0 ? Math.round((count / totalFindingsCount) * 100) : 0;
              const catColors: Record<string, string> = {
                SECURITY: 'bg-indigo-500',
                PERFORMANCE: 'bg-cyan-500',
                STYLE: 'bg-emerald-500',
                SYNTAX: 'bg-rose-500',
              };
              return (
                <div key={cat}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-300">{cat}</span>
                    <span className="text-slate-400 font-mono">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${catColors[cat] || 'bg-slate-500'} transition-all duration-500`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent Reviews Table */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-200">Recent Review Audit Log</h2>
          <span className="text-xs text-slate-500">Persistent SQLite storage</span>
        </div>

        {recentReviews.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <ShieldCheck className="w-12 h-12 mx-auto text-slate-600 mb-2" />
            <p className="text-sm">No code reviews yet. Submit your first Python code for inspection.</p>
            <button
              onClick={onNewReview}
              className="mt-3 px-4 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold"
            >
              Start Review
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/60 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3 rounded-l-lg">File</th>
                  <th className="px-4 py-3">Quality Gate</th>
                  <th className="px-4 py-3">Scope</th>
                  <th className="px-4 py-3 text-center">Critical</th>
                  <th className="px-4 py-3 text-center">High</th>
                  <th className="px-4 py-3 text-center">Total Issues</th>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3 text-right rounded-r-lg">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {recentReviews.map((r) => (
                  <tr key={r.review_id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3 font-mono text-xs text-slate-200">{r.file_path || 'main.py'}</td>
                    <td className="px-4 py-3">
                      <GateStatusBadge status={r.status} size="sm" />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">{r.scope}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`font-mono text-xs ${r.critical_count > 0 ? 'text-red-400 font-bold' : 'text-slate-500'}`}>
                        {r.critical_count}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`font-mono text-xs ${r.high_count > 0 ? 'text-orange-400 font-bold' : 'text-slate-500'}`}>
                        {r.high_count}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center font-mono text-xs text-slate-300">{r.total_findings}</td>
                    <td className="px-4 py-3 text-xs text-slate-500 font-mono">
                      {new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onSelectReview(r.review_id)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
