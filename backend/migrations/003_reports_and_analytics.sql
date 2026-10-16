-- ====================================================================
-- CAREERLENS DATABASE MIGRATION: 003_reports_and_analytics.sql
-- Phase 11: Reports History, Comparison & Progress Analytics
-- ====================================================================

-- 1. EXTEND ANALYSIS REPORTS TABLE
ALTER TABLE public.analysis_reports 
    ADD COLUMN IF NOT EXISTS target_role TEXT,
    ADD COLUMN IF NOT EXISTS report_title TEXT,
    ADD COLUMN IF NOT EXISTS ats_score NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS match_score NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS issues_count INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'completed' CHECK (status IN ('draft', 'completed', 'archived'));

-- 2. CREATE INDEXES FOR OPTIMIZED QUERYING & PAGINATION
CREATE INDEX IF NOT EXISTS idx_analysis_reports_created_at ON public.analysis_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_reports_target_role ON public.analysis_reports(target_role);

-- 3. ENSURE RLS POLICIES ARE COMPLETE & STRICT
-- Note: Row Level Security is already enabled on public.analysis_reports from 001_initial_schema.sql.
-- Verification of policies:
-- - SELECT: auth.uid() = user_id
-- - INSERT: auth.uid() = user_id
-- - UPDATE: auth.uid() = user_id
-- - DELETE: auth.uid() = user_id
