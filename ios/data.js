// Supabase-backed data adapter for the iOS prototype.
// Screens still read window.PROGRAMS, PROGRAM_DETAIL, HISTORY, ACTIVITY, and
// PAST_WORKOUT so the UI can stay lightweight while the backend becomes real.

(function () {
  const client = () => window.trainarSupabase;

  window.PROGRAMS = [];
  window.PROGRAM_DETAIL = { exercises: [], days: [] };
  window.PARSED_PROGRAM = window.PROGRAM_DETAIL;
  window.HISTORY = [];
  window.ACTIVITY = Array.from({ length: 84 }, () => 0);
  window.ACTIVITY_MONTH_DAYS = Array.from({ length: 30 }, () => 0);
  window.ACTIVITY_STATS = null;
  window.PAST_WORKOUT = null;
  window.TRAINAR_PROGRAM_DETAILS = {};
  window.TRAINAR_SESSIONS = [];
  window.TRAINAR_PRS = [];
  window.TRAINAR_MONTH_SESSION_IDS = {};
  window.TRAINAR_DEVICES = [];

  window.PROGRAM_SAMPLE_LINES = [
    'Back Squat (Top Single) - 1x1 @ 87.5%',
    'Back Squat - 5x3 @ 77.5%',
    'OHP - 3x8',
    'Pin Good Morning - 2x8-10',
    'Chest-Sup. Row - 4x8-10',
    'Hanging Leg Raise - 3x10',
  ];

  function emitDataChange() {
    window.dispatchEvent(new CustomEvent('trainar:data'));
  }

  function resetTrainarData() {
    window.PROGRAMS = [];
    window.PROGRAM_DETAIL = { exercises: [], days: [] };
    window.PARSED_PROGRAM = window.PROGRAM_DETAIL;
    window.HISTORY = [];
    window.ACTIVITY = Array.from({ length: 84 }, () => 0);
    window.ACTIVITY_MONTH_DAYS = Array.from({ length: 30 }, () => 0);
    window.ACTIVITY_STATS = null;
    window.PAST_WORKOUT = null;
    window.TRAINAR_PROGRAM_DETAILS = {};
    window.TRAINAR_SESSIONS = [];
    window.TRAINAR_PRS = [];
    window.TRAINAR_MONTH_SESSION_IDS = {};
    emitDataChange();
  }

  async function loadTrainarData(userId) {
    if (!client() || !userId) {
      resetTrainarData();
      return;
    }

    const [programsRes, sessionsRes, prsRes, devicesRes] = await Promise.all([
      client()
        .from('programs')
        .select('id,title,author,kind,source_type,source_label,color,description,weeks,days_per_week,active_week,progress,parse_confidence,canonical,created_at,archived_at')
        .is('archived_at', null)
        .order('created_at', { ascending: false }),
      client()
        .from('workout_sessions')
        .select('id,program_id,title,status,started_at,finished_at,duration_seconds,total_volume,total_sets,avg_rpe,auto_tracked_ratio,notes,created_at')
        .order('started_at', { ascending: false, nullsFirst: false })
        .limit(120),
      client()
        .from('personal_records')
        .select('id,session_id,exercise_name,record_type,value,unit,achieved_at')
        .order('achieved_at', { ascending: false })
        .limit(50),
      client()
        .from('devices')
        .select('id,name,model,serial_number,firmware_version,battery_percent,connection_status,last_seen_at')
        .order('last_seen_at', { ascending: false, nullsFirst: false }),
    ]);

    throwIfError(programsRes.error);
    throwIfError(sessionsRes.error);
    throwIfError(prsRes.error);
    throwIfError(devicesRes.error);

    const programs = programsRes.data || [];
    const details = await loadProgramDetails(programs);
    const sessions = sessionsRes.data || [];
    const prs = prsRes.data || [];

    window.TRAINAR_PROGRAM_DETAILS = details;
    window.TRAINAR_SESSIONS = sessions;
    window.TRAINAR_PRS = prs;
    window.PROGRAMS = programs.map((program) => programListItem(program, details[program.id]));
    window.PROGRAM_DETAIL = details[programs[0]?.id] || { exercises: [], days: [] };
    window.PARSED_PROGRAM = window.PROGRAM_DETAIL;
    window.TRAINAR_DEVICES = devicesRes.data || [];
    window.HISTORY = sessions.map((session) => sessionListItem(session, prs));
    window.ACTIVITY = buildActivity(sessions);
    window.ACTIVITY_MONTH_DAYS = buildMonthActivity(sessions, 2026, 3);
    window.TRAINAR_MONTH_SESSION_IDS = buildMonthSessionIds(sessions, 2026, 3);
    window.ACTIVITY_STATS = buildMonthStats(sessions, 2026, 3);
    const pastSession = getHighlightedPastSession(sessions);
    window.PAST_WORKOUT = pastSession ? await loadPastWorkout(pastSession, prs) : null;
    emitDataChange();
  }

  async function loadProgramDetails(programs) {
    const programIds = programs.map((program) => program.id);
    if (!programIds.length) return {};

    const daysRes = await client()
      .from('program_days')
      .select('id,program_id,week_number,day_number,title,notes')
      .in('program_id', programIds)
      .order('week_number')
      .order('day_number');
    throwIfError(daysRes.error);

    const days = daysRes.data || [];
    const dayIds = days.map((day) => day.id);
    const blocksRes = dayIds.length
      ? await client()
        .from('program_blocks')
        .select('id,day_id,block_number,title,execution_style')
        .in('day_id', dayIds)
        .order('block_number')
      : { data: [] };
    throwIfError(blocksRes.error);

    const blocks = blocksRes.data || [];
    const blockIds = blocks.map((block) => block.id);
    const exercisesRes = blockIds.length
      ? await client()
        .from('program_exercises')
        .select('id,block_id,exercise_number,exercise_name,set_count,rep_target,load_target,rest_seconds,notes,ambiguity_flags,raw')
        .in('block_id', blockIds)
        .order('exercise_number')
      : { data: [] };
    throwIfError(exercisesRes.error);

    const exercises = exercisesRes.data || [];
    const blocksByDay = groupBy(blocks, 'day_id');
    const exercisesByBlock = groupBy(exercises, 'block_id');
    const daysByProgram = groupBy(days, 'program_id');

    return Object.fromEntries(programs.map((program) => {
      const detailDays = (daysByProgram[program.id] || []).map((day) => {
        const dayBlocks = (blocksByDay[day.id] || []).map((block) => ({
          id: block.id,
          title: block.title,
          executionStyle: block.execution_style,
          exercises: (exercisesByBlock[block.id] || []).map(exerciseFromRow),
        }));

        return {
          id: day.id,
          title: day.title,
          weekNumber: day.week_number,
          notes: day.notes || '',
          blocks: dayBlocks,
        };
      });
      const flatExercises = detailDays.flatMap((day) => day.blocks.flatMap((block) => block.exercises));

      return [program.id, {
        programId: program.id,
        name: program.title,
        sourceType: program.source_type,
        confidence: program.parse_confidence,
        dayCount: detailDays.length,
        weeks: program.weeks,
        totalSets: flatExercises.reduce((sum, exercise) => sum + normalizeSetCount(exercise.sets), 0),
        days: detailDays,
        exercises: flatExercises,
        canonical: program.canonical || {},
      }];
    }));
  }

  async function saveProgramToSupabase(detail) {
    const { data: authData, error: authError } = await client().auth.getUser();
    throwIfError(authError);
    const user = authData.user;
    if (!user) throw new Error('Sign in before saving a program.');

    const days = getDetailDays(detail);
    const exercises = getDetailExercises(detail);
    const weekNumbers = days.map((day) => Number(day.weekNumber || 1));
    const weeks = Number(detail.weeks) || Math.max(0, ...weekNumbers, 0);
    const daysPerWeek = days.reduce((max, day) => {
      const count = days.filter((candidate) => Number(candidate.weekNumber || 1) === Number(day.weekNumber || 1)).length;
      return Math.max(max, count);
    }, 0);

    const programInsert = {
      user_id: user.id,
      title: detail.name || 'Parsed program',
      author: detail.author || 'Imported',
      kind: detail.sourceType || 'Parsed',
      source_type: detail.sourceType || 'imported',
      source_label: 'Imported',
      color: '#C5F23E',
      description: `${exercises.length} parsed exercises across ${days.length || 1} days.`,
      weeks,
      days_per_week: daysPerWeek || days.length || 1,
      active_week: 1,
      progress: 0,
      parse_confidence: typeof detail.confidence === 'number' ? detail.confidence : null,
      canonical: detail.canonical || {},
    };

    const { data: program, error: programError } = await client()
      .from('programs')
      .insert(programInsert)
      .select('id,title,author,kind,source_type,source_label,color,description,weeks,days_per_week,active_week,progress,parse_confidence,canonical,created_at,archived_at')
      .single();
    throwIfError(programError);

    const normalizedDays = days.length ? days : [{
      title: detail.name || 'Imported program',
      weekNumber: 1,
      notes: '',
      blocks: [{ title: 'Main', executionStyle: 'sequential', exercises }],
    }];

    for (const [dayIndex, day] of normalizedDays.entries()) {
      const { data: dayRow, error: dayError } = await client()
        .from('program_days')
        .insert({
          program_id: program.id,
          week_number: Number(day.weekNumber || 1),
          day_number: dayIndex + 1,
          title: day.title || `Day ${dayIndex + 1}`,
          notes: day.notes || null,
        })
        .select('id')
        .single();
      throwIfError(dayError);

      const blocks = day.blocks?.length ? day.blocks : [{ title: 'Main', executionStyle: 'sequential', exercises: day.exercises || [] }];
      for (const [blockIndex, block] of blocks.entries()) {
        const { data: blockRow, error: blockError } = await client()
          .from('program_blocks')
          .insert({
            day_id: dayRow.id,
            block_number: blockIndex + 1,
            title: block.title || 'Main',
            execution_style: block.executionStyle || 'sequential',
          })
          .select('id')
          .single();
        throwIfError(blockError);

        const exerciseRows = (block.exercises || []).map((exercise, exerciseIndex) => ({
          block_id: blockRow.id,
          exercise_number: exerciseIndex + 1,
          exercise_name: exercise.name || 'Untitled exercise',
          set_count: typeof exercise.sets === 'number' ? exercise.sets : null,
          rep_target: stringifyTarget(exercise.reps),
          load_target: stringifyTarget(exercise.load),
          rest_seconds: parseRestSeconds(exercise.rest),
          notes: exercise.note || null,
          ambiguity_flags: [],
          raw: exercise,
        }));

        if (exerciseRows.length) {
          const { error: exerciseError } = await client().from('program_exercises').insert(exerciseRows);
          throwIfError(exerciseError);
        }
      }
    }

    await loadTrainarData(user.id);
    return program.id;
  }

  async function archiveProgram(programId) {
    if (!programId) return;
    const { error } = await client()
      .from('programs')
      .update({ archived_at: new Date().toISOString() })
      .eq('id', programId);
    throwIfError(error);

    const { data } = await client().auth.getUser();
    if (data.user) await loadTrainarData(data.user.id);
  }

  async function pairDemoDevice() {
    const { data: authData, error: authError } = await client().auth.getUser();
    throwIfError(authError);
    if (!authData.user) return null;

    const { data, error } = await client()
      .from('devices')
      .upsert({
        user_id: authData.user.id,
        name: 'TrainAR',
        model: 'M2',
        serial_number: '8E40-B7C2',
        firmware_version: '1.4.2',
        battery_percent: 78,
        connection_status: 'connected',
        last_seen_at: new Date().toISOString(),
      }, { onConflict: 'user_id,serial_number' })
      .select('id,name,model,serial_number,firmware_version,battery_percent,connection_status,last_seen_at')
      .single();
    throwIfError(error);

    window.TRAINAR_DEVICES = [data];
    emitDataChange();
    return data;
  }

  async function startWorkout(programId) {
    const { data: authData, error: authError } = await client().auth.getUser();
    throwIfError(authError);
    if (!authData.user) throw new Error('Sign in before starting a workout.');

    const program = window.PROGRAMS.find((item) => item.id === programId);
    const { data, error } = await client()
      .from('workout_sessions')
      .insert({
        user_id: authData.user.id,
        program_id: programId || null,
        title: program?.name || 'Workout',
        status: 'in_progress',
        started_at: new Date().toISOString(),
      })
      .select('id')
      .single();
    throwIfError(error);
    return data.id;
  }

  async function finishWorkout(sessionId, programId) {
    if (!sessionId) return null;
    const detail = window.getProgramDetail(programId) || window.PROGRAM_DETAIL || { exercises: [] };
    const exercises = getDetailExercises(detail);
    const totalSets = exercises.reduce((sum, exercise) => sum + normalizeSetCount(exercise.sets), 0);
    const startedAt = new Date(Date.now() - 45 * 60 * 1000);
    const finishedAt = new Date();

    const { data: session, error } = await client()
      .from('workout_sessions')
      .update({
        status: 'completed',
        started_at: startedAt.toISOString(),
        finished_at: finishedAt.toISOString(),
        duration_seconds: Math.round((finishedAt - startedAt) / 1000),
        total_sets: totalSets,
        total_volume: 0,
        avg_rpe: null,
        auto_tracked_ratio: null,
      })
      .eq('id', sessionId)
      .select('id,program_id,title,status,started_at,finished_at,duration_seconds,total_volume,total_sets,avg_rpe,auto_tracked_ratio,created_at')
      .single();
    throwIfError(error);

    const { data: authData } = await client().auth.getUser();
    if (authData.user) await loadTrainarData(authData.user.id);
    return session;
  }

  async function loadPastWorkout(session, prs) {
    const logsRes = await client()
      .from('workout_exercise_logs')
      .select('id,exercise_number,exercise_name,notes')
      .eq('session_id', session.id)
      .order('exercise_number');
    throwIfError(logsRes.error);

    const logs = logsRes.data || [];
    const logIds = logs.map((log) => log.id);
    const setsRes = logIds.length
      ? await client()
        .from('workout_sets')
        .select('exercise_log_id,set_number,reps,load_value,load_unit,rpe,status')
        .in('exercise_log_id', logIds)
        .order('set_number')
      : { data: [] };
    throwIfError(setsRes.error);

    const setsByLog = groupBy(setsRes.data || [], 'exercise_log_id');
    const sessionPrs = (prs || []).filter((pr) => pr.session_id === session.id);

    return {
      id: session.id,
      date: formatSessionDate(session.started_at || session.created_at),
      name: session.title || 'Workout',
      totalVolume: formatVolume(session.total_volume),
      duration: formatDuration(session.duration_seconds),
      sets: session.total_sets,
      autoTracked: session.auto_tracked_ratio,
      rpe: session.avg_rpe,
      prs: sessionPrs.map((pr) => `${pr.exercise_name} - ${pr.value} ${pr.unit}`),
      exercises: logs.map((log) => ({
        name: log.exercise_name,
        sets: (setsByLog[log.id] || []).map((set) => ({
          reps: set.reps ?? '-',
          load: set.load_value == null ? '-' : `${Number(set.load_value)} ${set.load_unit}`,
          rpe: set.rpe ?? '-',
          status: set.status,
        })),
      })),
    };
  }

  async function selectPastWorkout(sessionId) {
    const session = (window.TRAINAR_SESSIONS || []).find((item) => item.id === sessionId)
      || getHighlightedPastSession(window.TRAINAR_SESSIONS || []);
    if (!session) return null;
    window.PAST_WORKOUT = await loadPastWorkout(session, window.TRAINAR_PRS || []);
    emitDataChange();
    return window.PAST_WORKOUT;
  }

  function getHighlightedPastSession(sessions) {
    return sessions.find((session) => {
      const date = new Date(session.started_at || session.created_at);
      return session.notes === 'Demo seed'
        && date.getFullYear() === 2026
        && date.getMonth() === 3
        && date.getDate() === 20;
    }) || sessions[0] || null;
  }

  function getProgramDetail(programId) {
    return window.TRAINAR_PROGRAM_DETAILS[programId] || null;
  }

  function programListItem(program, detail) {
    return {
      id: program.id,
      name: program.title,
      author: program.author || 'Imported',
      weeks: program.weeks || 0,
      daysPerWeek: program.days_per_week || detail?.dayCount || 0,
      type: program.kind || program.source_type || 'Program',
      color: program.color || '#C5F23E',
      sourceLabel: program.source_label || 'Imported',
      parsedOn: shortDate(program.created_at),
      activeWeek: program.active_week || 1,
      progress: Number(program.progress || 0),
      description: program.description || '',
    };
  }

  function sessionListItem(session, prs) {
    const started = session.started_at || session.created_at;
    return {
      id: session.id,
      date: shortDate(started),
      day: dayName(started),
      name: session.title || 'Workout',
      volume: formatVolume(session.total_volume),
      duration: formatDuration(session.duration_seconds),
      sets: session.total_sets || 0,
      prs: (prs || []).filter((pr) => pr.session_id === session.id).length,
      rpe: session.avg_rpe || 0,
    };
  }

  function exerciseFromRow(row) {
    return {
      id: row.id,
      name: row.exercise_name,
      sets: row.set_count ?? '-',
      reps: row.rep_target || '-',
      load: row.load_target || '-',
      rest: formatRest(row.rest_seconds),
      note: [row.notes, ...(row.ambiguity_flags || [])].filter(Boolean).join(' - '),
    };
  }

  function buildActivity(sessions) {
    const days = Array.from({ length: 84 }, () => 0);
    const today = new Date();
    sessions.forEach((session) => {
      const date = new Date(session.started_at || session.created_at);
      const diff = Math.floor((startOfDay(today) - startOfDay(date)) / 86400000);
      if (diff >= 0 && diff < 84) {
        const volume = Number(session.total_volume || 0);
        days[83 - diff] = volume > 20000 ? 3 : session.total_sets > 12 ? 2 : 1;
      }
    });
    return days;
  }

  function buildMonthActivity(sessions, year, monthIndex) {
    const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
    const days = Array.from({ length: daysInMonth }, () => 0);
    sessions.forEach((session) => {
      const date = new Date(session.started_at || session.created_at);
      if (date.getFullYear() !== year || date.getMonth() !== monthIndex) return;
      const volume = Number(session.total_volume || 0);
      days[date.getDate() - 1] = Math.max(
        days[date.getDate() - 1],
        volume > 20000 ? 3 : session.total_sets > 12 ? 2 : 1,
      );
    });
    return days;
  }

  function buildMonthSessionIds(sessions, year, monthIndex) {
    return sessions.reduce((ids, session) => {
      const date = new Date(session.started_at || session.created_at);
      if (date.getFullYear() !== year || date.getMonth() !== monthIndex) return ids;
      const day = date.getDate();
      if (!ids[day] || new Date(session.started_at || session.created_at) > new Date(ids[day].started_at || ids[day].created_at)) {
        ids[day] = session;
      }
      return ids;
    }, {});
  }

  function buildMonthStats(sessions, year, monthIndex) {
    const monthSessions = sessions.filter((session) => {
      const date = new Date(session.started_at || session.created_at);
      return date.getFullYear() === year && date.getMonth() === monthIndex;
    });
    const totalVolume = monthSessions.reduce((sum, session) => sum + Number(session.total_volume || 0), 0);
    const rpeSessions = monthSessions.filter((session) => Number(session.avg_rpe || 0) > 0);
    const avgRpe = rpeSessions.length
      ? rpeSessions.reduce((sum, session) => sum + Number(session.avg_rpe || 0), 0) / rpeSessions.length
      : 0;

    return {
      sessions: monthSessions.length,
      streak: longestMonthlyStreak(monthSessions),
      volume: totalVolume >= 1000 ? `${Math.round(totalVolume / 1000)}k` : String(Math.round(totalVolume)),
      rpe: avgRpe ? Number(avgRpe.toFixed(1)) : 0,
    };
  }

  function longestMonthlyStreak(sessions) {
    const activeDays = new Set(sessions.map((session) =>
      new Date(session.started_at || session.created_at).getDate(),
    ));
    let best = 0;
    let current = 0;
    for (let day = 1; day <= 30; day++) {
      if (activeDays.has(day)) {
        current += 1;
        best = Math.max(best, current);
      } else {
        current = 0;
      }
    }
    return best;
  }

  function groupBy(items, key) {
    return items.reduce((groups, item) => {
      const value = item[key];
      groups[value] = groups[value] || [];
      groups[value].push(item);
      return groups;
    }, {});
  }

  function getDetailDays(detail) {
    if (Array.isArray(detail.days)) return detail.days;
    return [];
  }

  function getDetailExercises(detail) {
    if (Array.isArray(detail.exercises)) return detail.exercises;
    return getDetailDays(detail).flatMap((day) =>
      (day.blocks || []).flatMap((block) => block.exercises || []),
    );
  }

  function normalizeSetCount(value) {
    return typeof value === 'number' ? value : Number.parseInt(value, 10) || 0;
  }

  function stringifyTarget(value) {
    if (value == null || value === '-') return null;
    return String(value);
  }

  function parseRestSeconds(value) {
    if (!value || value === '-') return null;
    const text = String(value).toLowerCase();
    const amount = Number.parseFloat(text);
    if (!Number.isFinite(amount)) return null;
    if (text.includes('min')) return Math.round(amount * 60);
    return Math.round(amount);
  }

  function formatRest(seconds) {
    if (!seconds) return '-';
    if (seconds % 60 === 0) return `${seconds / 60} min`;
    return `${seconds} sec`;
  }

  function shortDate(value) {
    if (!value) return 'Today';
    return new Intl.DateTimeFormat('en-US', { month: 'short', day: '2-digit' }).format(new Date(value));
  }

  function dayName(value) {
    if (!value) return '';
    return new Intl.DateTimeFormat('en-US', { weekday: 'short' }).format(new Date(value));
  }

  function formatSessionDate(value) {
    if (!value) return '';
    const date = new Date(value);
    return `${dayName(value)} - ${shortDate(date)}`;
  }

  function formatDuration(seconds) {
    if (!seconds) return '-';
    return `${Math.round(seconds / 60)}m`;
  }

  function formatVolume(value) {
    const volume = Number(value || 0);
    if (!volume) return '-';
    return `${Math.round(volume).toLocaleString()} lbs`;
  }

  function startOfDay(value) {
    const date = new Date(value);
    date.setHours(0, 0, 0, 0);
    return date;
  }

  function throwIfError(error) {
    if (error) throw error;
  }

  Object.assign(window, {
    loadTrainarData,
    resetTrainarData,
    saveProgramToSupabase,
    archiveProgram,
    pairDemoDevice,
    startWorkout,
    finishWorkout,
    selectPastWorkout,
    getProgramDetail,
  });
})();
