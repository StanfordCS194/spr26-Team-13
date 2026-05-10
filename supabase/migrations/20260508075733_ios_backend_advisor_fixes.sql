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

create index if not exists workout_sessions_device_id_idx
on public.workout_sessions (device_id);

create index if not exists workout_exercise_logs_program_exercise_id_idx
on public.workout_exercise_logs (program_exercise_id);

create index if not exists personal_records_session_id_idx
on public.personal_records (session_id);

revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
