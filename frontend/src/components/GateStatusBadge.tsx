import React from 'react';
import type { GateStatus } from '../types/review';
import { CheckCircle2, XCircle, AlertTriangle, AlertOctagon } from 'lucide-react';

interface Props {
  status: GateStatus | string;
  size?: 'sm' | 'md' | 'lg';
}

export const GateStatusBadge: React.FC<Props> = ({ status, size = 'md' }) => {
  const st = status.toUpperCase();

  const getStyle = () => {
    switch (st) {
      case 'PASS':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: <CheckCircle2 className={size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-6 h-6' : 'w-4 h-4'} />,
        };
      case 'FAIL':
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          icon: <XCircle className={size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-6 h-6' : 'w-4 h-4'} />,
        };
      case 'INCOMPLETE':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: <AlertTriangle className={size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-6 h-6' : 'w-4 h-4'} />,
        };
      default:
        return {
          bg: 'bg-red-500/10 text-red-400 border-red-500/30',
          icon: <AlertOctagon className={size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-6 h-6' : 'w-4 h-4'} />,
        };
    }
  };

  const current = getStyle();
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : size === 'lg' ? 'px-4 py-2 text-base font-bold' : 'px-3 py-1 text-sm font-semibold';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border ${current.bg} ${padding}`}>
      {current.icon}
      <span>{st}</span>
    </span>
  );
};
