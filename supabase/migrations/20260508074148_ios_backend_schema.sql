create extension if not exists pgcrypto;

create schema if not exists private;

create or replace function private.set_updated_at()
returns trigger
language plpgsql
set search_path = pg_catalog, pg_temp
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  display_name text,
  units text not null default 'imperial' check (units in ('imperial', 'metric')),
  timezone text not null default 'America/Los_Angeles',
  onboarded_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function private.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public, auth, pg_temp
as $$
begin
  insert into public.profiles (id, email, display_name, onboarded_at)
  values (
    new.id,
    new.email,
    nullif(new.raw_user_meta_data ->> 'display_name', ''),
    case when nullif(new.raw_user_meta_data ->> 'display_name', '') is null then null else now() end
  )
  on conflict (id) do update
  set email = excluded.email,
      updated_at = now();

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function private.handle_new_user();

create table public.devices (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null default 'TrainAR',
  model text,
  serial_number text,
  firmware_version text,
  battery_percent integer check (battery_percent between 0 and 100),
  connection_status text not null default 'disconnected'
    check (connection_status in ('connected', 'disconnected', 'pairing')),
  last_seen_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, serial_number)
);

create table public.programs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  title text not null,
  author text,
  kind text,
  source_type text,
  source_label text,
  source_file_path text,
  color text not null default '#C5F23E',
  description text,
  weeks integer not null default 0 check (weeks >= 0),
  days_per_week integer not null default 0 check (days_per_week >= 0),
  active_week integer not null default 1 check (active_week >= 0),
  progress numeric(5,4) not null default 0 check (progress >= 0 and progress <= 1),
  parse_confidence numeric(5,4) check (parse_confidence is null or (parse_confidence >= 0 and parse_confidence <= 1)),
  canonical jsonb not null default '{}'::jsonb,
  archived_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.program_days (
  id uuid primary key default gen_random_uuid(),
  program_id uuid not null references public.programs(id) on delete cascade,
  week_number integer not null default 1 check (week_number >= 1),
  day_number integer not null check (day_number >= 1),
  title text not null,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (program_id, week_number, day_number)
);

create table public.program_blocks (
  id uuid primary key default gen_random_uuid(),
  day_id uuid not null references public.program_days(id) on delete cascade,
  block_number integer not null check (block_number >= 1),
  title text not null default 'Main',
  execution_style text not null default 'sequential',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (day_id, block_number)
);

create table public.program_exercises (
  id uuid primary key default gen_random_uuid(),
  block_id uuid not null references public.program_blocks(id) on delete cascade,
  exercise_number integer not null check (exercise_number >= 1),
  exercise_name text not null,
  set_count integer check (set_count is null or set_count >= 0),
  rep_target text,
  load_target text,
  rest_seconds integer check (rest_seconds is null or rest_seconds >= 0),
  notes text,
  ambiguity_flags text[] not null default '{}',
  raw jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (block_id, exercise_number)
);

create table public.workout_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  program_id uuid references public.programs(id) on delete set null,
  device_id uuid references public.devices(id) on delete set null,
  title text not null,
  status text not null default 'planned'
    check (status in ('planned', 'in_progress', 'completed', 'abandoned')),
  started_at timestamptz,
  finished_at timestamptz,
  duration_seconds integer check (duration_seconds is null or duration_seconds >= 0),
  total_volume numeric(12,2) not null default 0 check (total_volume >= 0),
  total_sets integer not null default 0 check (total_sets >= 0),
  avg_rpe numeric(4,2) check (avg_rpe is null or (avg_rpe >= 0 and avg_rpe <= 10)),
  auto_tracked_ratio numeric(5,4) check (auto_tracked_ratio is null or (auto_tracked_ratio >= 0 and auto_tracked_ratio <= 1)),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.workout_exercise_logs (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.workout_sessions(id) on delete cascade,
  program_exercise_id uuid references public.program_exercises(id) on delete set null,
  exercise_number integer not null check (exercise_number >= 1),
  exercise_name text not null,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (session_id, exercise_number)
);

create table public.workout_sets (
  id uuid primary key default gen_random_uuid(),
  exercise_log_id uuid not null references public.workout_exercise_logs(id) on delete cascade,
  set_number integer not null check (set_number >= 1),
  reps integer check (reps is null or reps >= 0),
  load_value numeric(10,2) check (load_value is null or load_value >= 0),
  load_unit text not null default 'lb' check (load_unit in ('lb', 'kg', 'bodyweight', 'other')),
  rpe numeric(4,2) check (rpe is null or (rpe >= 0 and rpe <= 10)),
  status text not null default 'auto' check (status in ('auto', 'manual')),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (exercise_log_id, set_number)
);

create table public.personal_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  session_id uuid references public.workout_sessions(id) on delete set null,
  exercise_name text not null,
  record_type text not null default 'estimated_1rm',
  value numeric(12,2) not null,
  unit text not null default 'lb',
  achieved_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index profiles_email_idx on public.profiles (email);
create index devices_user_id_idx on public.devices (user_id);
create index programs_user_id_created_at_idx on public.programs (user_id, created_at desc);
create index program_days_program_id_idx on public.program_days (program_id);
create index program_blocks_day_id_idx on public.program_blocks (day_id);
create index program_exercises_block_id_idx on public.program_exercises (block_id);
create index workout_sessions_user_id_started_at_idx on public.workout_sessions (user_id, started_at desc nulls last, created_at desc);
create index workout_sessions_program_id_idx on public.workout_sessions (program_id);
create index workout_sessions_device_id_idx on public.workout_sessions (device_id);
create index workout_exercise_logs_session_id_idx on public.workout_exercise_logs (session_id);
create index workout_exercise_logs_program_exercise_id_idx on public.workout_exercise_logs (program_exercise_id);
create index workout_sets_exercise_log_id_idx on public.workout_sets (exercise_log_id);
create index personal_records_user_id_achieved_at_idx on public.personal_records (user_id, achieved_at desc);
create index personal_records_session_id_idx on public.personal_records (session_id);

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function private.set_updated_at();

create trigger devices_set_updated_at
before update on public.devices
for each row execute function private.set_updated_at();

create trigger programs_set_updated_at
before update on public.programs
for each row execute function private.set_updated_at();

create trigger program_days_set_updated_at
before update on public.program_days
for each row execute function private.set_updated_at();

create trigger program_blocks_set_updated_at
before update on public.program_blocks
for each row execute function private.set_updated_at();

create trigger program_exercises_set_updated_at
before update on public.program_exercises
for each row execute function private.set_updated_at();

create trigger workout_sessions_set_updated_at
before update on public.workout_sessions
for each row execute function private.set_updated_at();

create trigger workout_exercise_logs_set_updated_at
before update on public.workout_exercise_logs
for each row execute function private.set_updated_at();

create trigger workout_sets_set_updated_at
before update on public.workout_sets
for each row execute function private.set_updated_at();

alter table public.profiles enable row level security;
alter table public.devices enable row level security;
alter table public.programs enable row level security;
alter table public.program_days enable row level security;
alter table public.program_blocks enable row level security;
alter table public.program_exercises enable row level security;
alter table public.workout_sessions enable row level security;
alter table public.workout_exercise_logs enable row level security;
alter table public.workout_sets enable row level security;
alter table public.personal_records enable row level security;

grant usage on schema public to authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;

create policy "profiles_select_own"
on public.profiles for select
to authenticated
using ((select auth.uid()) is not null and id = (select auth.uid()));

create policy "profiles_update_own"
on public.profiles for update
to authenticated
using (id = (select auth.uid()))
with check (id = (select auth.uid()));

create policy "devices_crud_own"
on public.devices for all
to authenticated
using (user_id = (select auth.uid()))
with check (user_id = (select auth.uid()));

create policy "programs_crud_own"
on public.programs for all
to authenticated
using (user_id = (select auth.uid()))
with check (user_id = (select auth.uid()));

create policy "program_days_crud_own"
on public.program_days for all
to authenticated
using (
  exists (
    select 1 from public.programs p
    where p.id = program_days.program_id
      and p.user_id = (select auth.uid())
  )
)
with check (
  exists (
    select 1 from public.programs p
    where p.id = program_days.program_id
      and p.user_id = (select auth.uid())
  )
);

create policy "program_blocks_crud_own"
on public.program_blocks for all
to authenticated
using (
  exists (
    select 1
    from public.program_days d
    join public.programs p on p.id = d.program_id
    where d.id = program_blocks.day_id
      and p.user_id = (select auth.uid())
  )
)
with check (
  exists (
    select 1
    from public.program_days d
    join public.programs p on p.id = d.program_id
    where d.id = program_blocks.day_id
      and p.user_id = (select auth.uid())
  )
);

create policy "program_exercises_crud_own"
on public.program_exercises for all
to authenticated
using (
  exists (
    select 1
    from public.program_blocks b
    join public.program_days d on d.id = b.day_id
    join public.programs p on p.id = d.program_id
    where b.id = program_exercises.block_id
      and p.user_id = (select auth.uid())
  )
)
with check (
  exists (
    select 1
    from public.program_blocks b
    join public.program_days d on d.id = b.day_id
    join public.programs p on p.id = d.program_id
    where b.id = program_exercises.block_id
      and p.user_id = (select auth.uid())
  )
);

create policy "workout_sessions_crud_own"
on public.workout_sessions for all
to authenticated
using (user_id = (select auth.uid()))
with check (user_id = (select auth.uid()));

create policy "workout_exercise_logs_crud_own"
on public.workout_exercise_logs for all
to authenticated
using (
  exists (
    select 1 from public.workout_sessions s
    where s.id = workout_exercise_logs.session_id
      and s.user_id = (select auth.uid())
  )
)
with check (
  exists (
    select 1 from public.workout_sessions s
    where s.id = workout_exercise_logs.session_id
      and s.user_id = (select auth.uid())
  )
);

create policy "workout_sets_crud_own"
on public.workout_sets for all
to authenticated
using (
  exists (
    select 1
    from public.workout_exercise_logs l
    join public.workout_sessions s on s.id = l.session_id
    where l.id = workout_sets.exercise_log_id
      and s.user_id = (select auth.uid())
  )
)
with check (
  exists (
    select 1
    from public.workout_exercise_logs l
    join public.workout_sessions s on s.id = l.session_id
    where l.id = workout_sets.exercise_log_id
      and s.user_id = (select auth.uid())
  )
);

create policy "personal_records_crud_own"
on public.personal_records for all
to authenticated
using (user_id = (select auth.uid()))
with check (user_id = (select auth.uid()));
