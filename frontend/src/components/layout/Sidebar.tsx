import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  UploadCloud,
  FileCheck2,
  Briefcase,
  Share2,
  Sparkles,
  Compass,
  FileBarChart,
  Settings,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';
import { Badge } from '../common/Badge';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onCloseMobile }) => {
  const { user } = useAuth();
  const userDisplayName = user?.user_metadata?.full_name || (user?.email ? user.email.split('@')[0] : "Alex Rivera (CS '24)");
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/upload', label: 'Resume Upload', icon: UploadCloud },
    { to: '/review', label: 'Resume Review', icon: FileCheck2 },
    { to: '/job-match', label: 'Company & Job Match', icon: Briefcase },
    { to: '/connections', label: 'Profile Connections', icon: Share2 },
    { to: '/builder', label: 'AI Resume Builder', icon: Sparkles },
    { to: '/roadmap', label: 'Learning Roadmap', icon: Compass },
    { to: '/reports', label: 'Reports & Progress', icon: FileBarChart },
    { to: '/settings', label: 'Settings & Profile', icon: Settings },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-slate-900/40 z-30 lg:hidden backdrop-blur-xs transition-opacity"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand header */}
        <div className="h-16 px-5 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/40">
          <NavLink to="/" className="flex items-center gap-2.5 text-white focus:outline-none">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                CareerLens
              </span>
              <span className="text-[10px] text-slate-400 block -mt-1 font-mono">
                Employability v1.0
              </span>
            </div>
          </NavLink>

          <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            Demo
          </span>
        </div>

        {/* Current candidate mini-summary */}
        <div className="px-4 py-3 border-b border-slate-800/60 bg-slate-900/60">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-slate-400 font-medium">Readiness Index</span>
            <span className="text-emerald-400 font-mono font-bold">78 / 100</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-emerald-500 h-full rounded-full" style={{ width: '78%' }} />
          </div>
          <div className="flex items-center justify-between mt-2 text-[11px] text-slate-400">
            <span className="truncate max-w-[130px]" title={userDisplayName}>{userDisplayName}</span>
            <Badge variant="success" size="sm">Nearly Ready</Badge>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Main Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-sm font-semibold'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/80'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon
                        className={`w-4 h-4 transition-colors ${
                          isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                        }`}
                      />
                      <span>{item.label}</span>
                    </div>
                    {isActive ? (
                      <ChevronRight className="w-3.5 h-3.5 text-white/70" />
                    ) : null}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Bottom system status */}
        <div className="p-3.5 border-t border-slate-800 bg-slate-950/60 text-xs">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-[11px]">Backend API</span>
            </span>
            <span className="text-[10px] font-mono text-slate-400">Mock Mode</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-normal">
            FastAPI parser & Supabase DB link in Phase 2.
          </p>
        </div>
      </aside>
    </>
  );
};
