import React from 'react';

interface ScoreGaugeProps {
  score: number; // 0 - 100
  title: string;
  subtitle?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({
  score,
  title,
  subtitle,
  size = 'md',
  showLabel = true,
}) => {
  const normalized = Math.min(100, Math.max(0, score));

  // Determine stroke color
  const getColor = (val: number) => {
    if (val >= 80) return '#10b981'; // emerald-500
    if (val >= 65) return '#4f46e5'; // indigo-600
    if (val >= 50) return '#f59e0b'; // amber-500
    return '#f43f5e'; // rose-500
  };

  const strokeColor = getColor(normalized);

  const dim = size === 'lg' ? 140 : size === 'md' ? 108 : 80;
  const strokeWidth = size === 'lg' ? 10 : size === 'md' ? 8 : 6;
  const radius = (dim - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalized / 100) * circumference;

  return (
    <div className="flex flex-col items-center text-center">
      <div className="relative inline-flex items-center justify-center" style={{ width: dim, height: dim }}>
        <svg width={dim} height={dim} className="transform -rotate-90">
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            stroke="#f1f5f9"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span
            className={`font-bold font-mono text-slate-900 ${
              size === 'lg' ? 'text-3xl' : size === 'md' ? 'text-2xl' : 'text-lg'
            }`}
          >
            {normalized}
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 -mt-0.5">/ 100</span>
        </div>
      </div>

      {showLabel && (
        <div className="mt-2.5">
          <h4 className="text-xs font-semibold text-slate-800">{title}</h4>
          {subtitle && <p className="text-[11px] text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
      )}
    </div>
  );
};
