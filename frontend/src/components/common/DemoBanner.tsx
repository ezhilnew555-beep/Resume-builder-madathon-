import React from 'react';
import { Info, Sparkles } from 'lucide-react';

interface DemoBannerProps {
  message?: string;
  className?: string;
  phaseNotice?: string;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({
  message = 'Demonstration Mode: The data displayed below reflects synthetic candidate profile benchmarks. Real parsing, OCR, and AI scoring will connect to FastAPI in Phase 2.',
  className = '',
  phaseNotice = 'Phase 1 Frontend Preview',
}) => {
  return (
    <div
      className={`bg-indigo-50/80 border border-indigo-200/80 text-indigo-900 rounded-xl px-4 py-3 flex items-start gap-3 text-xs leading-relaxed ${className}`}
    >
      <div className="p-1 bg-indigo-100 rounded-md text-indigo-700 shrink-0 mt-0.5">
        <Sparkles className="w-3.5 h-3.5" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="font-semibold text-indigo-950 uppercase tracking-wide text-[10px] bg-indigo-200/60 px-1.5 py-0.5 rounded">
            {phaseNotice}
          </span>
          <span className="text-[11px] font-medium text-indigo-700 flex items-center gap-1">
            <Info className="w-3 h-3" /> Sample & Simulated Data
          </span>
        </div>
        <p className="text-slate-700">{message}</p>
      </div>
    </div>
  );
};
