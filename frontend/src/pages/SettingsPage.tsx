import React, { useState, useEffect } from 'react';
import {
  Save,
  CheckCircle2,
  Database,
  LogIn,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Toast } from '../components/common/Toast';
import type { ToastMessage } from '../components/common/Toast';
import { apiService } from '../services/api';
import type { StudentProfile } from '../types';
import { useAuth } from '../context/AuthContext';
import { POPULAR_ROLES } from '../data/suggestions';

export const SettingsPage: React.FC = () => {
  const { user, isConfigured, getAccessToken, openAuthModal } = useAuth();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  useEffect(() => {
    async function loadProfile() {
      // Baseline defaults
      const mockData = await apiService.getStudentProfile();
      
      // If user is logged in, try loading real profile from Supabase
      if (user && isConfigured) {
        try {
          const token = await getAccessToken();
          if (token) {
            const live = await apiService.fetchUserProfileLive(token);
            const profileData = live?.profile || live;
            
            // Check for locally cached auxiliary fields (phone, location, gradYear, etc.)
            let localData: Partial<StudentProfile> = {};
            try {
              const saved = localStorage.getItem(`careerlens_profile_${user.id}`);
              if (saved) localData = JSON.parse(saved);
            } catch {
              // Ignore parse errors
            }

            if (profileData && (profileData.id || profileData.full_name || profileData.education || profileData.target_role)) {
              let degree = localData.degree || '';
              let university = profileData.education || localData.university || '';
              if (university.includes(' - ')) {
                const parts = university.split(' - ');
                degree = parts[0];
                university = parts.slice(1).join(' - ');
              }

              setProfile({
                ...mockData,
                phone: '',
                location: '',
                graduationYear: '',
                ...localData,
                fullName: profileData.full_name ?? (localData.fullName || user.user_metadata?.full_name || ''),
                targetRole: profileData.target_role ?? (localData.targetRole || ''),
                university: university,
                degree: degree,
                email: profileData.email || user.email || localData.email || '',
              });
              return;
            }
          }
        } catch (err) {
          console.warn('Could not load profile from Supabase, using local defaults:', err);
        }
      }
      
      setProfile(mockData);
    }
    loadProfile();
  }, [user, isConfigured]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setIsSaving(true);
    try {
      if (user && isConfigured) {
        const token = await getAccessToken();
        if (token) {
          const updatedEducation = profile.degree ? `${profile.degree} - ${profile.university}` : profile.university;
          await apiService.updateUserProfileLive(token, {
            full_name: profile.fullName,
            education: updatedEducation,
            target_role: profile.targetRole,
          });
          try {
            localStorage.setItem(`careerlens_profile_${user.id}`, JSON.stringify(profile));
          } catch {
            // Ignore storage errors
          }
          setProfile({ ...profile });
          setToast({
            id: Math.random().toString(),
            type: 'success',
            title: 'Profile Synced to Supabase',
            message: 'Your profile changes have been persisted to PostgreSQL via authenticated RLS.',
          });
          return;
        }
      }

      const updated = await apiService.updateStudentProfile(profile);
      setProfile(updated);
      setToast({
        id: Math.random().toString(),
        type: 'info',
        title: 'Preferences Saved (Client State)',
        message: isConfigured
          ? 'Saved locally. Sign in with Supabase to persist changes to PostgreSQL.'
          : 'Saved in client state. Configure Supabase credentials to enable PostgreSQL persistence.',
      });
    } catch (err: any) {
      setToast({
        id: Math.random().toString(),
        type: 'error',
        title: 'Save Failed',
        message: err.message || 'An error occurred while saving profile.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (!profile) return null;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {user ? (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              <strong>Connected:</strong> Signed in as <code>{user.email}</code>. Changes sync directly to Supabase PostgreSQL with Row Level Security.
            </span>
          </div>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">
            RLS Active
          </span>
        </div>
      ) : (
        <div className="p-3.5 bg-indigo-50 border border-indigo-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-indigo-900">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-indigo-600 shrink-0" />
            <span>
              <strong>Phase 3 Database:</strong> {isConfigured ? 'Supabase is configured. Sign in to persist candidate credentials to PostgreSQL.' : 'Supabase credentials pending configuration. Currently using client preview.'}
            </span>
          </div>
          {isConfigured && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => openAuthModal('signin')}
              icon={<LogIn className="w-3.5 h-3.5" />}
            >
              Sign In
            </Button>
          )}
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Candidate Profile & Analysis Settings
          </h2>
          <p className="text-slate-600 text-xs sm:text-sm mt-0.5">
            Configure academic credentials, target career roles, and ATS evaluation strictness.
          </p>
        </div>

        <Button
          type="button"
          onClick={handleSave}
          variant="primary"
          size="md"
          isLoading={isSaving}
          icon={<Save className="w-4 h-4" />}
        >
          Save All Changes
        </Button>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* 1. Academic & Personal Profile */}
        <Card
          title="Student & Contact Information"
          subtitle="Identity and educational background used for resume header and school benchmarks"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={profile.fullName}
                onChange={(e) => setProfile({ ...profile, fullName: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Phone Number
              </label>
              <input
                type="text"
                value={profile.phone}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Location & Relocation
              </label>
              <input
                type="text"
                value={profile.location}
                onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                University / Institution
              </label>
              <input
                type="text"
                value={profile.university}
                onChange={(e) => setProfile({ ...profile, university: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Degree
                </label>
                <input
                  type="text"
                  value={profile.degree}
                  onChange={(e) => setProfile({ ...profile, degree: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Grad Year
                </label>
                <input
                  type="text"
                  value={profile.graduationYear}
                  onChange={(e) => setProfile({ ...profile, graduationYear: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white font-mono"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* 2. Career Interests & Role Targeting */}
        <Card
          title="Career Interests & Job Targeting"
          subtitle="Influences job match recommendations and high-priority skill weightings"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Primary Target Role
              </label>
              <input
                type="text"
                list="settings-role-suggestions"
                value={profile.targetRole}
                onChange={(e) => setProfile({ ...profile, targetRole: e.target.value })}
                placeholder="e.g. Data Analyst, Software Engineer, Data Scientist"
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white"
              />
              <datalist id="settings-role-suggestions">
                {POPULAR_ROLES.map((r) => (
                  <option key={r} value={r} />
                ))}
              </datalist>
              <div className="flex flex-wrap items-center gap-1.5 pt-1.5">
                <span className="text-[10px] text-slate-400 font-medium">Quick Suggestions:</span>
                {['Data Analyst', 'Software Engineer', 'Full Stack Software Engineer', 'Data Scientist', 'AI / Deep Learning Engineer', 'DevOps Engineer'].map((roleSugg) => (
                  <button
                    key={roleSugg}
                    type="button"
                    onClick={() => setProfile({ ...profile, targetRole: roleSugg })}
                    className={`text-[10px] px-2 py-0.5 rounded-md border transition-colors cursor-pointer ${
                      profile.targetRole.toLowerCase() === roleSugg.toLowerCase()
                        ? 'bg-indigo-100 text-indigo-700 border-indigo-300 font-semibold'
                        : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-indigo-50 hover:text-indigo-600'
                    }`}
                  >
                    {roleSugg}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Work Arrangement Preference
                </label>
                <select
                  value={profile.workPreference}
                  onChange={(e) =>
                    setProfile({ ...profile, workPreference: e.target.value as any })
                  }
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white"
                >
                  <option value="Remote">Fully Remote</option>
                  <option value="Hybrid">Hybrid (Remote + In-office)</option>
                  <option value="Onsite">On-site</option>
                  <option value="Flexible">Flexible / Any</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Industries (Comma-separated)
                </label>
                <input
                  type="text"
                  value={profile.preferredIndustries.join(', ')}
                  onChange={(e) =>
                    setProfile({
                      ...profile,
                      preferredIndustries: e.target.value.split(',').map((s) => s.trim()),
                    })
                  }
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* 3. Analysis Preferences & Strictness */}
        <Card
          title="Audit Strictness & Preferences"
          subtitle="Configure how rigorous CareerLens evaluates your qualifications"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-2">
                ATS Scoring Thresholds
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  {
                    id: 'Lenient',
                    title: 'Lenient / Entry',
                    desc: 'Focuses on fundamental section completeness and basic keyword matches.',
                  },
                  {
                    id: 'Standard ATS',
                    title: 'Standard ATS (Recommended)',
                    desc: 'Enforces impact quantifiers, standard typography, and core skill verifications.',
                  },
                  {
                    id: 'Strict BigTech',
                    title: 'Strict BigTech Tier',
                    desc: 'Rigorous penalty for missing metrics, vague action verbs, or unverified claims.',
                  },
                ].map((tier) => (
                  <div
                    key={tier.id}
                    onClick={() =>
                      setProfile({ ...profile, scoringStrictness: tier.id as any })
                    }
                    className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                      profile.scoringStrictness === tier.id
                        ? 'border-indigo-600 bg-indigo-50/50 ring-1 ring-indigo-600'
                        : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100/60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-slate-900">{tier.title}</span>
                      {profile.scoringStrictness === tier.id && (
                        <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 leading-normal">{tier.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <div>
                <span className="font-semibold text-slate-800 block">
                  Weekly Progress & Skill Alert Digest
                </span>
                <span className="text-[11px] text-slate-500">
                  Receive recommendations when new matching opportunities or skill gaps arise.
                </span>
              </div>
              <input
                type="checkbox"
                checked={profile.emailAlerts}
                onChange={(e) => setProfile({ ...profile, emailAlerts: e.target.checked })}
                className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 cursor-pointer"
              />
            </div>
          </div>
        </Card>
      </form>

      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
};
