// Browser-global adapter for the same Flask ingestion API used by desktop.
// The API returns the canonical TrainingProgram contract. The iOS prototype
// keeps the same day/block hierarchy, with a flat exercise list only for
// summary counts and home-screen previews.

const DEFAULT_PARSE_ENDPOINT = '/api/programs/parse';
const LOCAL_PARSE_ENDPOINT = 'http://127.0.0.1:5001/api/programs/parse';

function getParseEndpoint() {
  if (window.TRAINAR_PARSE_ENDPOINT) return window.TRAINAR_PARSE_ENDPOINT;
  if (window.location.protocol === 'file:') return LOCAL_PARSE_ENDPOINT;
  return DEFAULT_PARSE_ENDPOINT;
}

async function parseProgramFile(file, { userId, endpoint = getParseEndpoint(), signal } = {}) {
  const body = new FormData();
  body.append('user_id', userId || await getCurrentUserId());
  body.append('program_file', file);

  const response = await fetch(endpoint, {
    method: 'POST',
    body,
    signal,
  });

  const payload = await readJson(response);
  if (!response.ok) {
    throw new Error(getErrorMessage(payload) || `Parser request failed with ${response.status}`);
  }
  if (!payload || typeof payload !== 'object' || !payload.program) {
    throw new Error('Parser response did not include a program.');
  }

  return payload;
}

async function readJson(response) {
  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return { error: text };
  }
}

function getErrorMessage(payload) {
  if (payload && typeof payload === 'object' && typeof payload.error === 'string') {
    return payload.error;
  }
  return null;
}

function canonicalToIOSProgram(program) {
  const weeks = Array.isArray(program.weeks) ? program.weeks : [];
  const dayRefs = weeks.flatMap((week) =>
    (week.days || []).map((day) => ({ weekNumber: week.week_number, day })),
  );
  const days = dayRefs.map(({ weekNumber, day }, dayIndex) => formatDay(day, weekNumber, dayIndex));
  const exercises = days.flatMap((day) => day.blocks.flatMap((block) => block.exercises));
  const totalSets = exercises.reduce((sum, exercise) => sum + numericSetCount(exercise.sets), 0);

  return {
    programId: program.program_id || 'parsed-program',
    name: program.title || 'Parsed program',
    sourceType: program.source_type,
    confidence: program.parse_confidence,
    dayCount: days.length,
    weeks: weeks.length,
    totalSets,
    days,
    exercises,
    canonical: program,
  };
}

function formatDay(day, weekNumber, dayIndex) {
  const rawBlocks = day.blocks || [];
  const assignedKeys = new Set(
    rawBlocks.flatMap((block) => block.exercises || []).map(exerciseKey),
  );

  const blocks = rawBlocks.map((block, blockIndex) => ({
    id: block.block_id || `${day.day_id || dayIndex}-block-${blockIndex}`,
    title: block.title || `Block ${blockIndex + 1}`,
    executionStyle: block.execution_style,
    exercises: (block.exercises || []).map((exercise) => formatExercise(exercise)),
  }));

  const looseExercises = (day.exercises || [])
    .filter((exercise) => !assignedKeys.has(exerciseKey(exercise)))
    .map((exercise) => formatExercise(exercise));
  const allBlocks = [...blocks];
  if (looseExercises.length) {
    allBlocks.push({
      id: `${day.day_id || dayIndex}-main`,
      title: blocks.length ? 'Unassigned' : 'Main',
      executionStyle: 'sequential',
      exercises: looseExercises,
    });
  }

  return {
    id: day.day_id || `day-${dayIndex + 1}`,
    title: day.title || `Day ${dayIndex + 1}`,
    weekNumber,
    notes: day.notes || '',
    blocks: allBlocks,
  };
}

function exerciseKey(exercise) {
  if (exercise.exercise_id) return `id:${exercise.exercise_id}`;
  return [
    exercise.display_name || '',
    exercise.set_count || '',
    exercise.rep_target || '',
    exercise.load_target || '',
  ].join('|').toLowerCase();
}

function formatExercise(exercise) {
  return {
    id: exercise.exercise_id,
    name: exercise.display_name || 'Untitled exercise',
    sets: exercise.set_count || '-',
    reps: exercise.rep_target || '-',
    load: exercise.load_target || '-',
    rest: formatRest(exercise.rest_seconds),
    note: [exercise.notes, ...(exercise.ambiguity_flags || [])].filter(Boolean).join(' · '),
  };
}

function numericSetCount(value) {
  return typeof value === 'number' ? value : 0;
}

function formatRest(seconds) {
  if (!seconds) return '-';
  if (seconds % 60 === 0) return `${seconds / 60} min`;
  return `${seconds} sec`;
}

function programListItemFromDetail(detail) {
  return {
    id: detail.programId || 'parsed-program',
    name: detail.name || 'Parsed program',
    author: 'Imported',
    weeks: detail.weeks || 0,
    daysPerWeek: detail.dayCount || 0,
    type: detail.sourceType || 'Parsed',
    color: '#C5F23E',
    sourceLabel: 'Imported',
    parsedOn: 'Today',
    activeWeek: 1,
    progress: 0,
    description: `${detail.exercises.length} parsed exercises across ${detail.dayCount || 0} days.`,
  };
}

async function installParsedProgram(detail) {
  let savedProgramId = detail.programId;
  if (window.saveProgramToSupabase) {
    savedProgramId = await window.saveProgramToSupabase(detail);
    detail.programId = savedProgramId || detail.programId;
  } else {
    const nextItem = programListItemFromDetail(detail);
    const existing = window.PROGRAMS || [];
    window.PROGRAMS = [nextItem, ...existing.filter((program) => program.id !== nextItem.id)];
    window.PROGRAM_DETAIL = detail;
    window.PARSED_PROGRAM = detail;
  }
  window.dispatchEvent(new CustomEvent('trainar:data'));
  return detail.programId;
}

async function getCurrentUserId() {
  if (!window.trainarSupabase) return 'demo-user';
  const { data } = await window.trainarSupabase.auth.getUser();
  return data.user?.id || 'demo-user';
}

Object.assign(window, {
  parseProgramFile,
  canonicalToIOSProgram,
  installParsedProgram,
});
