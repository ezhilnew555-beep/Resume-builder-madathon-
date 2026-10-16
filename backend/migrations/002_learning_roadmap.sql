-- ====================================================================
-- CAREERLENS DATABASE MIGRATION: 002_learning_roadmap.sql
-- Phase 10: Personalized Learning Roadmap & Progress Tracking
-- ====================================================================

-- 1. LEARNING ROADMAPS TABLE
CREATE TABLE IF NOT EXISTS public.learning_roadmaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    target_role TEXT NOT NULL,
    target_company TEXT,
    job_description_id UUID REFERENCES public.job_descriptions(id) ON DELETE SET NULL,
    weekly_hours INT NOT NULL DEFAULT 10 CHECK (weekly_hours > 0 AND weekly_hours <= 60),
    target_weeks INT NOT NULL DEFAULT 4 CHECK (target_weeks >= 1 AND target_weeks <= 52),
    roadmap_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. ROADMAP TASKS TABLE (Individual task progress and user notes)
CREATE TABLE IF NOT EXISTS public.roadmap_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    roadmap_id UUID NOT NULL REFERENCES public.learning_roadmaps(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    milestone_week INT NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed')),
    user_notes TEXT,
    custom_resources JSONB DEFAULT '[]'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT uq_roadmap_user_task UNIQUE (user_id, roadmap_id, task_id)
);

-- ====================================================================
-- INDEXES FOR QUERY OPTIMIZATION
-- ====================================================================
CREATE INDEX IF NOT EXISTS idx_learning_roadmaps_user_id ON public.learning_roadmaps(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_roadmaps_job_id ON public.learning_roadmaps(job_description_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_user_id ON public.roadmap_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_roadmap_id ON public.roadmap_tasks(roadmap_id);

-- ====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Strict Isolation: Authenticated students can access only their own roadmap records.
-- ====================================================================

ALTER TABLE public.learning_roadmaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roadmap_tasks ENABLE ROW LEVEL SECURITY;

-- learning_roadmaps Policies
CREATE POLICY "Users can view their own learning roadmaps"
    ON public.learning_roadmaps FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own learning roadmaps"
    ON public.learning_roadmaps FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own learning roadmaps"
    ON public.learning_roadmaps FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own learning roadmaps"
    ON public.learning_roadmaps FOR DELETE
    USING (auth.uid() = user_id);

-- roadmap_tasks Policies
CREATE POLICY "Users can view their own roadmap tasks"
    ON public.roadmap_tasks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own roadmap tasks"
    ON public.roadmap_tasks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own roadmap tasks"
    ON public.roadmap_tasks FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own roadmap tasks"
    ON public.roadmap_tasks FOR DELETE
    USING (auth.uid() = user_id);
