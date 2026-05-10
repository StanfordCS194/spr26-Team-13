do $$
declare
  demo_user_id uuid;
  p_power uuid;
  p_nsuns uuid;
  p_ppl uuid;
  d uuid;
  b uuid;
  s uuid;
  l uuid;
  workout_date timestamptz;
  offsets integer[] := array[1,3,5,8,10,12,15,17,19,22,24,26,29,31,33,36,38,40,43,45,47,50,52,54,57,59,61,64,66,68,71,73,75,78,80,82];
  names text[] := array['Full Body 1','Full Body 2','Full Body 3','Full Body 4','Full Body 5'];
  i integer;
begin
  select id into demo_user_id
  from auth.users
  where lower(email) = lower('callums.run4yourlife@gmail.com')
  limit 1;

  if demo_user_id is null then
    raise exception 'No Supabase Auth user found for callums.run4yourlife@gmail.com';
  end if;

  insert into public.profiles (id, email, display_name, units, timezone, onboarded_at)
  values (demo_user_id, 'callums.run4yourlife@gmail.com', 'Callum', 'imperial', 'America/Los_Angeles', now() - interval '90 days')
  on conflict (id) do update
  set email = excluded.email,
      display_name = excluded.display_name,
      units = excluded.units,
      timezone = excluded.timezone,
      onboarded_at = excluded.onboarded_at;

  delete from public.personal_records where user_id = demo_user_id and record_type like 'demo_%';
  delete from public.workout_sessions where user_id = demo_user_id and notes = 'Demo seed';
  delete from public.programs where user_id = demo_user_id and source_label = 'Demo seed';
  delete from public.devices where user_id = demo_user_id and serial_number = '8E40-B7C2';

  insert into public.devices (
    user_id, name, model, serial_number, firmware_version, battery_percent,
    connection_status, last_seen_at
  )
  values (
    demo_user_id, 'TrainAR', 'M2', '8E40-B7C2', '1.4.2', 78,
    'connected', now() - interval '8 minutes'
  );

  insert into public.programs (
    user_id, title, author, kind, source_type, source_label, color, description,
    weeks, days_per_week, active_week, progress, parse_confidence, canonical, created_at
  )
  values (
    demo_user_id, 'Powerbuilding 5x', 'J. Nippard', 'Powerbuilding', 'spreadsheet',
    'Demo seed', '#C5F23E',
    '10-week powerbuilding cycle blending heavy strength singles with hypertrophy accessories.',
    10, 5, 6, 0.58, 0.94, '{"demo":true}'::jsonb, now() - interval '82 days'
  )
  returning id into p_power;

  insert into public.programs (
    user_id, title, author, kind, source_type, source_label, color, description,
    weeks, days_per_week, active_week, progress, parse_confidence, canonical, created_at
  )
  values (
    demo_user_id, 'nSuns 5/3/1 LP', 'nSuns', 'Strength', 'text',
    'Demo seed', '#7DD3FC',
    'High-frequency linear progression based on 5/3/1 percentages.',
    0, 5, 0, 0, 0.89, '{"demo":true}'::jsonb, now() - interval '68 days'
  )
  returning id into p_nsuns;

  insert into public.programs (
    user_id, title, author, kind, source_type, source_label, color, description,
    weeks, days_per_week, active_week, progress, parse_confidence, canonical, created_at
  )
  values (
    demo_user_id, 'PPL - Arnold Split', 'Custom', 'Hypertrophy', 'photo',
    'Demo seed', '#FFC462',
    'Push-pull-legs hypertrophy emphasis. 6 days per week, 8-week block.',
    8, 6, 2, 0.18, 0.86, '{"demo":true}'::jsonb, now() - interval '35 days'
  )
  returning id into p_ppl;

  for i in 1..5 loop
    insert into public.program_days (program_id, week_number, day_number, title, notes)
    values (p_power, 1, i, names[i], 'Demo program day')
    returning id into d;

    insert into public.program_blocks (day_id, block_number, title, execution_style)
    values (d, 1, 'Main lifts', 'sequential')
    returning id into b;

    if i = 1 then
      insert into public.program_exercises (block_id, exercise_number, exercise_name, set_count, rep_target, load_target, rest_seconds, notes)
      values
        (b, 1, 'Back Squat (Top Single)', 1, '1', '365 lb', 240, 'Brace hard and move fast.'),
        (b, 2, 'Back Squat', 5, '3', '320 lb', 180, 'Full depth, consistent bar path.'),
        (b, 3, 'Barbell Overhead Press', 3, '8', '115 lb', 120, 'Press up and back.'),
        (b, 4, 'Pin Good Morning', 2, '8-10', '155 lb', 120, 'Controlled hinge.'),
        (b, 5, 'Chest-Supported Row', 4, '8-10', '90 lb', 90, 'Pause at top.');
    elsif i = 2 then
      insert into public.program_exercises (block_id, exercise_number, exercise_name, set_count, rep_target, load_target, rest_seconds, notes)
      values
        (b, 1, 'Barbell Bench Press', 4, '6', '210 lb', 180, 'Quick pause.'),
        (b, 2, 'Pull-Up', 4, '8', 'BW', 120, 'Full hang.'),
        (b, 3, 'Incline Dumbbell Press', 3, '10', '70 lb', 120, 'Smooth eccentric.'),
        (b, 4, 'Tricep Pushdown', 3, '12', '60 lb', 90, 'Lock elbows.'),
        (b, 5, 'Dumbbell Curl', 3, '12', '35 lb', 90, 'No swing.');
    elsif i = 3 then
      insert into public.program_exercises (block_id, exercise_number, exercise_name, set_count, rep_target, load_target, rest_seconds, notes)
      values
        (b, 1, 'Deadlift', 3, '3', '315 lb', 240, 'Pull slack first.'),
        (b, 2, 'Romanian Deadlift', 3, '10', '185 lb', 120, 'Hamstring stretch.'),
        (b, 3, 'Barbell Row', 4, '8', '155 lb', 120, 'Pull to lower chest.'),
        (b, 4, 'Hanging Leg Raise', 3, '12', 'BW', 60, 'Controlled reps.');
    elsif i = 4 then
      insert into public.program_exercises (block_id, exercise_number, exercise_name, set_count, rep_target, load_target, rest_seconds, notes)
      values
        (b, 1, 'Front Squat', 4, '5', '225 lb', 180, 'Tall torso.'),
        (b, 2, 'Close-Grip Bench Press', 4, '8', '185 lb', 150, 'Elbows tucked.'),
        (b, 3, 'Lat Pulldown', 4, '10', '130 lb', 90, 'Drive elbows down.'),
        (b, 4, 'Standing Calf Raise', 3, '15', '180 lb', 90, 'Pause at top.');
    else
      insert into public.program_exercises (block_id, exercise_number, exercise_name, set_count, rep_target, load_target, rest_seconds, notes)
      values
        (b, 1, 'Paused Bench Press', 5, '3', '225 lb', 180, 'Long pause.'),
        (b, 2, 'Back Squat', 4, '6', '275 lb', 180, 'Volume work.'),
        (b, 3, 'Seated Cable Row', 4, '10', '140 lb', 90, 'Neutral grip.'),
        (b, 4, 'Face Pull', 3, '15', '45 lb', 60, 'Rear delts.');
    end if;
  end loop;

  foreach i in array offsets loop
    workout_date := now() - make_interval(days => i);
    insert into public.workout_sessions (
      user_id, program_id, title, status, started_at, finished_at, duration_seconds,
      total_volume, total_sets, avg_rpe, auto_tracked_ratio, notes, created_at
    )
    values (
      demo_user_id, p_power, names[((i % 5) + 1)], 'completed',
      workout_date, workout_date + interval '74 minutes', 4440 + ((i % 7) * 120),
      12000 + ((i % 9) * 1240), 14 + (i % 6), 7.2 + ((i % 8) * 0.2),
      0.82 + ((i % 10) * 0.012), 'Demo seed', workout_date
    )
    returning id into s;
  end loop;

  workout_date := now() - interval '1 day';
  insert into public.workout_sessions (
    user_id, program_id, title, status, started_at, finished_at, duration_seconds,
    total_volume, total_sets, avg_rpe, auto_tracked_ratio, notes, created_at
  )
  values (
    demo_user_id, p_power, 'Full Body 1', 'completed',
    workout_date, workout_date + interval '78 minutes', 4680,
    21640, 18, 8.4, 0.94, 'Demo seed', workout_date
  )
  returning id into s;

  insert into public.workout_exercise_logs (session_id, exercise_number, exercise_name)
  values (s, 1, 'Back Squat (Top Single)') returning id into l;
  insert into public.workout_sets (exercise_log_id, set_number, reps, load_value, load_unit, rpe, status, completed_at)
  values (l, 1, 1, 365, 'lb', 8, 'auto', workout_date + interval '10 minutes');

  insert into public.workout_exercise_logs (session_id, exercise_number, exercise_name)
  values (s, 2, 'Back Squat') returning id into l;
  insert into public.workout_sets (exercise_log_id, set_number, reps, load_value, load_unit, rpe, status, completed_at)
  values
    (l, 1, 3, 320, 'lb', 6, 'auto', workout_date + interval '18 minutes'),
    (l, 2, 3, 320, 'lb', 6, 'auto', workout_date + interval '23 minutes'),
    (l, 3, 3, 320, 'lb', 7, 'auto', workout_date + interval '28 minutes'),
    (l, 4, 3, 320, 'lb', 7, 'auto', workout_date + interval '33 minutes'),
    (l, 5, 3, 320, 'lb', 7, 'manual', workout_date + interval '38 minutes');

  insert into public.workout_exercise_logs (session_id, exercise_number, exercise_name)
  values (s, 3, 'Barbell Overhead Press') returning id into l;
  insert into public.workout_sets (exercise_log_id, set_number, reps, load_value, load_unit, rpe, status, completed_at)
  values
    (l, 1, 8, 115, 'lb', 6, 'auto', workout_date + interval '45 minutes'),
    (l, 2, 8, 115, 'lb', 6, 'auto', workout_date + interval '49 minutes'),
    (l, 3, 8, 115, 'lb', 7, 'auto', workout_date + interval '53 minutes');

  insert into public.workout_exercise_logs (session_id, exercise_number, exercise_name)
  values (s, 4, 'Chest-Supported Row') returning id into l;
  insert into public.workout_sets (exercise_log_id, set_number, reps, load_value, load_unit, rpe, status, completed_at)
  values
    (l, 1, 9, 90, 'lb', 9, 'auto', workout_date + interval '60 minutes'),
    (l, 2, 9, 90, 'lb', 9, 'auto', workout_date + interval '64 minutes'),
    (l, 3, 8, 90, 'lb', 9, 'auto', workout_date + interval '68 minutes'),
    (l, 4, 8, 90, 'lb', 9, 'auto', workout_date + interval '72 minutes');

  insert into public.personal_records (
    user_id, session_id, exercise_name, record_type, value, unit, achieved_at
  )
  values
    (demo_user_id, s, 'Back Squat top single', 'demo_weight_pr', 365, 'lb', workout_date + interval '10 minutes'),
    (demo_user_id, s, 'Total workout volume', 'demo_volume_pr', 21640, 'lb', workout_date + interval '78 minutes');
end $$;
