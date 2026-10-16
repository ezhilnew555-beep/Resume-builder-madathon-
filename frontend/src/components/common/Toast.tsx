import React, { useEffect } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  title: string;
  message?: string;
}

interface ToastProps {
  toast: ToastMessage | null;
  onClose: () => void;
  duration?: number;
}

export const Toast: React.FC<ToastProps> = ({ toast, onClose, duration = 3500 }) => {
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => {
      onClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [toast, onClose, duration]);

  if (!toast) return null;

  const icons = {
    success: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
    error: <AlertCircle className="w-4 h-4 text-rose-600" />,
    info: <Info className="w-4 h-4 text-indigo-600" />,
  };

  const borders = {
    success: 'border-emerald-200 bg-emerald-50 text-emerald-950',
    error: 'border-rose-200 bg-rose-50 text-rose-950',
    info: 'border-indigo-200 bg-indigo-50 text-indigo-950',
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 max-w-sm animate-in fade-in slide-in-from-bottom-3 duration-200">
      <div
        className={`flex items-start gap-3 p-3.5 rounded-xl border shadow-lg ${borders[toast.type]}`}
      >
        <div className="mt-0.5 shrink-0">{icons[toast.type]}</div>
        <div className="flex-1 text-xs">
          <p className="font-semibold">{toast.title}</p>
          {toast.message && <p className="text-slate-600 mt-0.5">{toast.message}</p>}
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-700 p-0.5 rounded cursor-pointer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
