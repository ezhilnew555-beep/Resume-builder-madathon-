import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Menu,
  Bell,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  User,
  ExternalLink,
  ChevronDown,
  LogIn,
  LogOut,
  Database,
  Bot,
} from 'lucide-react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { AIAssistantDrawer } from '../assistant/AIAssistantDrawer';
import { apiService } from '../../services/api';
import type { HealthCheckResult } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isConfigured, openAuthModal, signOut } = useAuth();

  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [apiHealth, setApiHealth] = useState<HealthCheckResult | null>(null);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function checkBackend() {
      const res = await apiService.getHealthStatus();
      if (mounted) {
        setApiHealth(res);
      }
    }
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // Map route to title
  const getPageTitle = (pathname: string) => {
    switch (pathname) {
      case '/':
        return { title: 'Career Readiness Dashboard', category: 'Overview' };
      case '/upload':
        return { title: 'Resume Upload & Extraction Stage', category: 'Ingestion' };
      case '/review':
        return { title: 'Interactive Resume Findings Review', category: 'ATS Audit' };
      case '/job-match':
        return { title: 'Company & Job Description Matcher', category: 'Target Alignment' };
      case '/connections':
        return { title: 'Verified Profile Connections', category: 'Integrations' };
      case '/builder':
        return { title: 'AI-Guided Resume Studio', category: 'Editing & Builder' };
      case '/roadmap':
        return { title: 'Curated Skill & Learning Roadmap', category: 'Career Growth' };
      case '/reports':
        return { title: 'Evaluation Reports & Progression', category: 'Analytics' };
      case '/settings':
        return { title: 'Candidate Profile & Preferences', category: 'Configuration' };
      default:
        return { title: 'CareerLens Analyzer', category: 'Portal' };
    }
  };

  const current = getPageTitle(location.pathname);

  const userDisplayName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Alex Rivera';
  const userRole = user ? 'Authenticated Student' : 'Demo Candidate';
  const initials = userDisplayName
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  return (
    <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-20 flex items-center justify-between px-4 sm:px-6">
      {/* Left section: mobile hamburger & title */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="p-2 -ml-1 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg lg:hidden cursor-pointer"
          aria-label="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-semibold text-indigo-600 uppercase tracking-wider hidden sm:inline">
              {current.category}
            </span>
            <span className="text-slate-300 hidden sm:inline">/</span>
            <h1 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
              {current.title}
            </h1>
          </div>
        </div>
      </div>

      {/* Right section: mode pill, quick upload action, notifications, user avatar */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Backend API status */}
        {apiHealth?.connected ? (
          <Badge variant="success" size="sm" className="hidden md:inline-flex" title="Connected to FastAPI REST API">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse inline-block mr-1" />
            FastAPI {apiHealth.version || 'v1.0.0'} Online
          </Badge>
        ) : apiHealth && !apiHealth.connected ? (
          <Badge variant="danger" size="sm" className="hidden md:inline-flex" title="FastAPI backend is offline">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 inline-block mr-1" />
            API Offline (Port 8000)
          </Badge>
        ) : (
          <Badge variant="warning" size="sm" className="hidden md:inline-flex">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse inline-block mr-1" />
            Checking API...
          </Badge>
        )}

        {/* Database configuration status */}
        {isConfigured ? (
          <Badge variant="success" size="sm" className="hidden lg:inline-flex">
            <Database className="w-3 h-3 mr-1 text-emerald-600" />
            Supabase DB Active
          </Badge>
        ) : (
          <button
            type="button"
            onClick={() => openAuthModal('signin')}
            className="cursor-pointer"
          >
            <Badge variant="outline" size="sm" className="hidden lg:inline-flex hover:border-indigo-400">
              <Database className="w-3 h-3 mr-1 text-amber-500" />
              Configure DB & Auth
            </Badge>
          </button>
        )}

        {/* AI Assistant button */}
        <Button
          size="sm"
          variant="outline"
          icon={<Bot className="w-3.5 h-3.5 text-indigo-600" />}
          onClick={() => setIsAssistantOpen(true)}
          className="hidden sm:inline-flex"
        >
          AI Assistant
        </Button>

        {/* Auth sign in button if not logged in */}
        {!user && (
          <Button
            size="sm"
            variant="outline"
            icon={<LogIn className="w-3.5 h-3.5 text-indigo-600" />}
            onClick={() => openAuthModal('signin')}
            className="hidden sm:inline-flex"
          >
            Sign In
          </Button>
        )}

        <Button
          size="sm"
          variant="primary"
          icon={<UploadCloud className="w-3.5 h-3.5" />}
          onClick={() => navigate('/upload')}
          className="hidden sm:inline-flex"
        >
          Upload Resume
        </Button>

        {/* Notifications toggle */}
        <div className="relative">
          <button
            type="button"
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowUserMenu(false);
            }}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg relative cursor-pointer"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-indigo-600 ring-2 ring-white" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800">System Notifications</span>
                <span className="text-[10px] text-indigo-600 font-medium">3 unread</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
                <div className="p-3 text-xs hover:bg-slate-50 flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-800">Benchmark Ready</p>
                    <p className="text-[11px] text-slate-500">Alex Rivera resume scored 78/100 across 14 ATS parameters.</p>
                    <span className="text-[10px] text-slate-400 mt-1 block">15m ago</span>
                  </div>
                </div>
                <div className="p-3 text-xs hover:bg-slate-50 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-800">Skill Gap Alert</p>
                    <p className="text-[11px] text-slate-500">FinTech role requires Kubernetes & Kafka. Add hands-on project proof.</p>
                    <span className="text-[10px] text-slate-400 mt-1 block">1h ago</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User profile menu */}
        <div className="relative">
          <button
            type="button"
            onClick={() => {
              setShowUserMenu(!showUserMenu);
              setShowNotifications(false);
            }}
            className="flex items-center gap-2 p-1.5 hover:bg-slate-100 rounded-lg cursor-pointer"
          >
            <div className="w-7 h-7 rounded-full bg-indigo-600 text-white font-semibold text-xs flex items-center justify-center">
              {initials}
            </div>
            <div className="text-left hidden lg:block leading-tight">
              <span className="text-xs font-semibold text-slate-800 block truncate max-w-[120px]">
                {userDisplayName}
              </span>
              <span className="text-[10px] text-slate-500 block">{userRole}</span>
            </div>
            <ChevronDown className="w-3 h-3 text-slate-400 hidden lg:block" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-slate-200 py-1.5 z-50 animate-in fade-in zoom-in-95 duration-150 text-xs">
              <div className="px-3.5 py-2 border-b border-slate-100">
                <p className="font-semibold text-slate-800 truncate">{userDisplayName}</p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email || 'alex.rivera@example.com (Demo)'}</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  navigate('/settings');
                  setShowUserMenu(false);
                }}
                className="w-full text-left px-3.5 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2 cursor-pointer"
              >
                <User className="w-3.5 h-3.5 text-slate-400" />
                Profile & Settings
              </button>
              <button
                type="button"
                onClick={() => {
                  navigate('/reports');
                  setShowUserMenu(false);
                }}
                className="w-full text-left px-3.5 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2 cursor-pointer"
              >
                <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                My Assessment History
              </button>

              <div className="border-t border-slate-100 my-1 pt-1">
                {user ? (
                  <button
                    type="button"
                    onClick={() => {
                      signOut();
                      setShowUserMenu(false);
                    }}
                    className="w-full text-left px-3.5 py-2 text-rose-600 hover:bg-rose-50 flex items-center gap-2 cursor-pointer font-medium"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    Sign Out
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      openAuthModal('signin');
                      setShowUserMenu(false);
                    }}
                    className="w-full text-left px-3.5 py-2 text-indigo-600 hover:bg-indigo-50 flex items-center gap-2 cursor-pointer font-medium"
                  >
                    <LogIn className="w-3.5 h-3.5" />
                    Sign In to Supabase
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <AIAssistantDrawer
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        resumeId={sessionStorage.getItem('latest_resume_id') || undefined}
      />
    </header>
  );
};
