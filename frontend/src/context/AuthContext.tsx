import React, { createContext, useContext, useEffect, useState } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '../lib/supabase';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isConfigured: boolean;
  authModalOpen: boolean;
  openAuthModal: (mode?: 'signin' | 'signup') => void;
  closeAuthModal: () => void;
  authModalMode: 'signin' | 'signup';
  signInWithEmail: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUpWithEmail: (
    email: string,
    password: string,
    meta?: { full_name?: string; education?: string; target_role?: string }
  ) => Promise<{ error: Error | null; needsEmailVerification?: boolean }>;
  signOut: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);
  const [authModalMode, setAuthModalMode] = useState<'signin' | 'signup'>('signin');

  useEffect(() => {
    if (!supabase || !isSupabaseConfigured) {
      setLoading(false);
      return;
    }

    // 1. Restore active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // 2. Subscribe to auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const openAuthModal = (mode: 'signin' | 'signup' = 'signin') => {
    setAuthModalMode(mode);
    setAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setAuthModalOpen(false);
  };

  const signInWithEmail = async (email: string, password: string) => {
    if (!supabase) {
      return { error: new Error('Supabase Auth is not configured. Add credentials to .env') };
    }
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (!error) {
      closeAuthModal();
    }
    return { error };
  };

  const signUpWithEmail = async (
    email: string,
    password: string,
    meta?: { full_name?: string; education?: string; target_role?: string }
  ) => {
    if (!supabase) {
      return { error: new Error('Supabase Auth is not configured. Add credentials to .env') };
    }
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: meta?.full_name || '',
          education: meta?.education || '',
          target_role: meta?.target_role || '',
        },
      },
    });

    if (error) {
      return { error };
    }

    const needsEmailVerification = !data.session;
    if (!needsEmailVerification) {
      closeAuthModal();
    }
    return { error: null, needsEmailVerification };
  };

  const signOut = async () => {
    if (supabase) {
      await supabase.auth.signOut();
    }
    setUser(null);
    setSession(null);
  };

  const getAccessToken = async (): Promise<string | null> => {
    if (session?.access_token) {
      return session.access_token;
    }
    if (supabase) {
      const { data } = await supabase.auth.getSession();
      return data.session?.access_token || null;
    }
    return null;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        isConfigured: isSupabaseConfigured,
        authModalOpen,
        openAuthModal,
        closeAuthModal,
        authModalMode,
        signInWithEmail,
        signUpWithEmail,
        signOut,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
