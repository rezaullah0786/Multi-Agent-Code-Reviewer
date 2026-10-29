import React, { useState, useEffect } from 'react';
import type { ReviewRequest, ReviewResponse, ReviewScope } from '../types/review';
import { api } from '../services/api';
import { SeverityBadge } from '../components/SeverityBadge';
import { GateStatusBadge } from '../components/GateStatusBadge';
import {
  Play,
  Sparkles,
  AlertCircle,
  FileCode,
  Sliders,
  Terminal,
  Cpu,
  Info,
  CheckCircle2,
} from 'lucide-react';

interface Props {
  initialReviewId?: string | null;
  onClearInitialReviewId?: () => void;
  isLLMAvailable: boolean;
}

const PRESETS = {
  security: {
    label: 'Security Flaws',
    filename: 'auth_handler.py',
    code: `import os
import subprocess

API_SECRET_KEY = "sk-live-98234098234098234098"

def handle_user_request(user_input, cmd):
    # Unsafe dynamic execution
    result = eval(user_input)
    
    # Dangerous subprocess execution
    subprocess.run("ping " + cmd, shell=True)
    
    # Potential SQL injection
    user_id = user_input
    query = f"SELECT * FROM accounts WHERE id = {user_id}"
    
    return result
`,
  },
  performance: {
    label: 'Performance Bottlenecks',
    filename: 'data_processor.py',
    code: `import time
import re

async def process_batch(items):
    # Inefficient string concatenation in loop
    aggregated = ""
    for item in items:
        aggregated += str(item)
        
        # O(N) membership check repeated in loop
        if item in [10, 20, 30, 40, 50]:
            pass
            
        # Regex compiled inside loop
        pattern = re.compile(r"\\d+")

    # File opened without context manager
    f = open("metrics.log", "a")
    f.write(aggregated)

    # Synchronous blocking call in async function
    time.sleep(2)
    return aggregated
`,
  },
  style: {
    label: 'Readability & Style',
    filename: 'calculator.py',
    code: `def calculateTaxReport(val1, val2, val3, val4, val5, val6, history=[]):
    # Mutable default argument history=[]
    # Function has > 6 arguments
    # Non-snake_case function name
    
    try:
        total = val1 + val2
        history.append(total)
    except:
        # Bare except silently suppressing exceptions
        pass
        
    return history
`,
  },
  clean: {
    label: 'Clean Compliant Code',
    filename: 'payment_service.py',
    code: `from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PaymentDetails:
    amount: float
    currency: str
    recipient: str

class PaymentProcessor:
    def process_payment(self, details: PaymentDetails) -> bool:
        if details.amount <= 0:
            raise ValueError("Amount must be positive")
        return True

    def export_summary(self, filename: str, data: str) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(data)
`,
  },
};

export const CodeReviewPage: React.FC<Props> = ({ initialReviewId, onClearInitialReviewId, isLLMAvailable }) => {
  const [code, setCode] = useState(PRESETS.security.code);
  const [filePath, setFilePath] = useState(PRESETS.security.filename);
  const [scope, setScope] = useState<ReviewScope>('ALL');
  const [enableLLM, setEnableLLM] = useState(false);
  const [blockOnCritical, setBlockOnCritical] = useState(true);
  const [blockOnHigh, setBlockOnHigh] = useState(true);
  const [maxMedium, setMaxMedium] = useState(5);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewResult, setReviewResult] = useState<ReviewResponse | null>(null);

  // Filter states
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');

  useEffect(() => {
    if (initialReviewId) {
      loadReviewById(initialReviewId);
    }
  }, [initialReviewId]);

  const loadReviewById = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getReview(id);
      setReviewResult(res);
      if (res.file_path) setFilePath(res.file_path);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch review');
    } finally {
      setLoading(false);
      if (onClearInitialReviewId) onClearInitialReviewId();
    }
  };

  const handleRunReview = async () => {
    if (!code.trim()) {
      setError('Please provide Python source code to review.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const req: ReviewRequest = {
        code,
        file_path: filePath.trim() || 'main.py',
        scope,
        enable_llm: enableLLM && isLLMAvailable,
        quality_gate_config: {
          block_on_critical: blockOnCritical,
          block_on_high: blockOnHigh,
          max_medium_allowed: maxMedium,
          max_low_allowed: 15,
        },
      };

      const res = await api.submitReview(req);
      setReviewResult(res);
    } catch (err: any) {
      setError(err.message || 'Review execution failed');
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (presetKey: keyof typeof PRESETS) => {
    const p = PRESETS[presetKey];
    setCode(p.code);
    setFilePath(p.filename);
    setReviewResult(null);
    setError(null);
  };

  // Filter findings
  const filteredFindings = (reviewResult?.findings || []).filter((f) => {
    if (selectedCategory !== 'ALL' && f.category !== selectedCategory) return false;
    if (selectedSeverity !== 'ALL' && f.severity !== selectedSeverity) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Configuration & Preset Bar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mr-1 flex items-center gap-1">
            <FileCode className="w-3.5 h-3.5 text-indigo-400" /> Demo Presets:
          </span>
          {(Object.keys(PRESETS) as Array<keyof typeof PRESETS>).map((key) => (
            <button
              key={key}
              onClick={() => loadPreset(key)}
              className="px-2.5 py-1 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            >
              {PRESETS[key].label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 flex-wrap text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <label className="font-semibold text-slate-300">File Name:</label>
            <input
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-200 font-mono text-xs focus:outline-none focus:border-indigo-500"
              placeholder="e.g. main.py"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <label className="font-semibold text-slate-300">Scope:</label>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as ReviewScope)}
              className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Checks</option>
              <option value="SECURITY">Security Only</option>
              <option value="PERFORMANCE">Performance Only</option>
              <option value="STYLE">Style Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Editor & Control Panel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Code Input (8 columns) */}
        <div className="lg:col-span-8 flex flex-col space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="font-mono text-slate-300 flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-indigo-400" />
              Source Code Input (Python 3)
            </span>
            <span>{code.split('\n').length} lines · {code.length} characters</span>
          </div>

          <div className="relative rounded-xl border border-slate-800 bg-slate-950 font-mono text-xs overflow-hidden shadow-inner">
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              rows={18}
              className="w-full p-4 bg-transparent text-slate-200 focus:outline-none font-mono resize-y leading-relaxed selection:bg-indigo-600/30"
              placeholder="# Paste or type Python code here..."
              spellCheck={false}
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Quality Gate Settings & Action Panel (4 columns) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-indigo-400" /> Quality Gate Policy
            </h2>

            <div className="space-y-2 text-xs">
              <label className="flex items-center justify-between p-2 rounded-lg bg-slate-800/60 border border-slate-750 cursor-pointer">
                <span className="text-slate-300">Block on Critical findings</span>
                <input
                  type="checkbox"
                  checked={blockOnCritical}
                  onChange={(e) => setBlockOnCritical(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-0"
                />
              </label>

              <label className="flex items-center justify-between p-2 rounded-lg bg-slate-800/60 border border-slate-750 cursor-pointer">
                <span className="text-slate-300">Block on High findings</span>
                <input
                  type="checkbox"
                  checked={blockOnHigh}
                  onChange={(e) => setBlockOnHigh(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-0"
                />
              </label>

              <div className="p-2 rounded-lg bg-slate-800/60 border border-slate-750 flex items-center justify-between">
                <span className="text-slate-300">Max Medium allowed</span>
                <input
                  type="number"
                  min={0}
                  max={50}
                  value={maxMedium}
                  onChange={(e) => setMaxMedium(parseInt(e.target.value) || 0)}
                  className="w-14 px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-right text-slate-200 font-mono"
                />
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800 space-y-2">
              <label className="flex items-center justify-between p-2 rounded-lg bg-indigo-950/20 border border-indigo-900/40 cursor-pointer">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <div>
                    <div className="text-xs font-semibold text-slate-200">LLM-Assisted Agents</div>
                    <div className="text-[10px] text-slate-400">
                      {isLLMAvailable ? 'OpenAI model configured' : 'API Key not set (runs local AST rules)'}
                    </div>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={enableLLM}
                  onChange={(e) => setEnableLLM(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-0"
                />
              </label>
            </div>

            <button
              onClick={handleRunReview}
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  LangGraph Orchestrating Agents...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  Start Multi-Agent Review
                </>
              )}
            </button>
          </div>

          {/* Agent Stack Card */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-2.5">
            <h3 className="font-bold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Active Workflow Stack
            </h3>
            <ul className="space-y-1.5 text-slate-400">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>Deterministic AST Engine (Security & Perf rules)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                <span>Qdrant Vector Context Retrieval</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                <span>LangGraph Multi-Agent Orchestrator</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span>Pydantic Guardrail Model Validation</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Review Results Section */}
      {reviewResult && (
        <div className="space-y-6 pt-4 border-t border-slate-800">
          {/* Quality Gate Result Banner */}
          <div
            className={`p-6 rounded-xl border ${
              reviewResult.quality_gate.status === 'PASS'
                ? 'bg-emerald-950/20 border-emerald-500/30'
                : 'bg-rose-950/20 border-rose-500/30'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start sm:items-center gap-3">
                <GateStatusBadge status={reviewResult.quality_gate.status} size="lg" />
                <div>
                  <h3 className="text-lg font-bold text-slate-100">{reviewResult.quality_gate.summary}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{reviewResult.quality_gate.explanation}</p>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
                <span>Duration: {reviewResult.execution_metadata.duration_ms || 0}ms</span>
                <span>Findings: {reviewResult.findings.length}</span>
              </div>
            </div>

            {/* Blocking Findings Alert if failed */}
            {reviewResult.quality_gate.blocking_findings.length > 0 && (
              <div className="mt-4 p-3 rounded-lg bg-rose-900/30 border border-rose-800 text-rose-200 text-xs">
                <span className="font-bold">Blocking Issues ({reviewResult.quality_gate.blocking_findings.length}): </span>
                {reviewResult.quality_gate.blocking_findings.map((bf) => bf.title).join(', ')}
              </div>
            )}

            <div className="mt-4 text-[11px] text-slate-500 flex items-center gap-1.5 border-t border-slate-800/60 pt-3">
              <Info className="w-3.5 h-3.5 text-slate-400" />
              <span>{reviewResult.quality_gate.disclaimer}</span>
            </div>
          </div>

          {/* Filter Bar & Findings Grouping */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2 overflow-x-auto">
              <span className="text-xs font-semibold uppercase text-slate-400">Category:</span>
              {['ALL', 'SECURITY', 'PERFORMANCE', 'STYLE', 'SYNTAX'].map((c) => (
                <button
                  key={c}
                  onClick={() => setSelectedCategory(c)}
                  className={`px-3 py-1 rounded text-xs font-medium transition ${
                    selectedCategory === c
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 overflow-x-auto">
              <span className="text-xs font-semibold uppercase text-slate-400">Severity:</span>
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((s) => (
                <button
                  key={s}
                  onClick={() => setSelectedSeverity(s)}
                  className={`px-3 py-1 rounded text-xs font-medium transition ${
                    selectedSeverity === s
                      ? 'bg-slate-700 text-white'
                      : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Findings Cards List */}
          {filteredFindings.length === 0 ? (
            <div className="p-12 text-center rounded-xl bg-slate-900 border border-slate-800 text-slate-400">
              <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-400 mb-2" />
              <p className="text-sm font-semibold text-slate-200">No findings matching the selected filters.</p>
              <p className="text-xs text-slate-500 mt-1">The inspected source code satisfies the criteria.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredFindings.map((finding) => (
                <div
                  key={finding.id}
                  className="p-5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <SeverityBadge severity={finding.severity} />
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {finding.rule_id}
                      </span>
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        {finding.category}
                      </span>
                      <h4 className="font-bold text-slate-100 text-sm">{finding.title}</h4>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                      {finding.file_path && <span>{finding.file_path}</span>}
                      {finding.line_number && (
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-indigo-300 border border-slate-700">
                          Line {finding.line_number}
                        </span>
                      )}
                      <span className="text-[11px] text-slate-500">Src: {finding.source}</span>
                    </div>
                  </div>

                  {finding.snippet && (
                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto">
                      <span className="text-slate-600 mr-2">{finding.line_number || 1} |</span>
                      {finding.snippet}
                    </div>
                  )}

                  <div className="text-xs text-slate-300 leading-relaxed">
                    <p>{finding.explanation}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-900/30 text-xs">
                    <span className="font-semibold text-indigo-300">💡 Suggested Remediation: </span>
                    <span className="text-slate-300">{finding.remediation}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
