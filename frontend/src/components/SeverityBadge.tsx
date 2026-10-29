import React from 'react';
import type { FindingSeverity } from '../types/review';

interface Props {
  severity: FindingSeverity | string;
  className?: string;
}

export const SeverityBadge: React.FC<Props> = ({ severity, className = '' }) => {
  const sev = severity.toUpperCase();

  const getColors = () => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/15 text-red-400 border-red-500/30';
      case 'HIGH':
        return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      case 'LOW':
        return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
      default:
        return 'bg-slate-500/15 text-slate-300 border-slate-500/30';
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold tracking-wider border ${getColors()} ${className}`}
    >
      {sev}
    </span>
  );
};
