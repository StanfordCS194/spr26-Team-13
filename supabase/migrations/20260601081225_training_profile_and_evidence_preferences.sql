alter table public.profiles
  add column if not exists training_goal text,
  add column if not exists training_experience text,
  add column if not exists workout_days_per_week integer check (workout_days_per_week is null or workout_days_per_week between 1 and 7),
  add column if not exists workout_session_minutes integer check (workout_session_minutes is null or workout_session_minutes between 10 and 240),
  add column if not exists available_equipment text[] not null default '{}',
  add column if not exists coach_style text not null default 'direct',
  add column if not exists evidence_preference text not null default 'concise',
  add column if not exists movement_constraints text,
  add column if not exists training_onboarded_at timestamptz;

alter table public.profiles
  drop constraint if exists profiles_training_experience_check,
  add constraint profiles_training_experience_check
    check (
      training_experience is null
      or training_experience in ('beginner', 'intermediate', 'advanced')
    );

alter table public.profiles
  drop constraint if exists profiles_coach_style_check,
  add constraint profiles_coach_style_check
    check (coach_style in ('direct', 'encouraging', 'analytical', 'high_energy'));

alter table public.profiles
  drop constraint if exists profiles_evidence_preference_check,
  add constraint profiles_evidence_preference_check
    check (evidence_preference in ('minimal', 'concise', 'detailed'));
