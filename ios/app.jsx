// App — wires every screen into the iPhone frame.
//
// State machine (high level):
//   signup phase: splash → auth → name → training → home
//   main phase:   tab roots (home / calendar / profile) + a small nav stack
//                 for sub-screens (add a program flow, program detail, past
//                 workout summary)
//
// Workout state (loadedToGlasses) lives at the app level so:
//   * the Train tab icon can pulse when a workout is live
//   * HomeScreen + ProgramViewScreen both reflect the same state without
//     needing to share a parent component

const PROTOTYPE_W = 402;
const PROTOTYPE_H = 874;

const TAB_ROOTS = ['home', 'calendar', 'profile'];

// Tab roots — the bottom-tab pages. Sub-screens stack on top of these.
const SCREENS_WITH_TABBAR = TAB_ROOTS;

// All known screens. If a screen isn't a tab root, hitting back pops it
// off the stack to whatever was underneath.
const SIGNUP_SCREENS = ['splash', 'auth', 'name', 'training'];

function firstWorkoutStep(programId, day = null) {
  const detail = window.getProgramDetail && programId ? window.getProgramDetail(programId) : window.PROGRAM_DETAIL;
  const selectedDay = day || resolveWorkoutDay(programId, null);
  const exercise = getDayExercises(selectedDay, detail)[0];
  if (!exercise) return null;
  return {
    exerciseName: exercise.name,
    exerciseNumber: 1,
    setNumber: 1,
    setCount: Number.parseInt(exercise.sets, 10) || 1,
    repTarget: exercise.reps || null,
    loadTarget: exercise.load || null,
    restSeconds: parseRestSecondsForCoach(exercise.rest),
  };
}

function nextStepForProgram(programId, currentStep, { nextExercise = false, day = null } = {}) {
  const detail = window.getProgramDetail && programId ? window.getProgramDetail(programId) : window.PROGRAM_DETAIL;
  const selectedDay = day || resolveWorkoutDay(programId, null);
  const exercises = getDayExercises(selectedDay, detail);
  if (!exercises.length) return null;
  if (!currentStep) return firstWorkoutStep(programId, selectedDay);

  const currentIndex = exercises.findIndex((exercise) => (
    normalizeCoachName(exercise.name) === normalizeCoachName(currentStep.exerciseName)
  ));
  if (currentIndex < 0) return firstWorkoutStep(programId, selectedDay);
  const currentExercise = exercises[currentIndex] || exercises[0];
  const setCount = Number.parseInt(currentStep.setCount || currentExercise.sets, 10) || 1;
  const setNumber = Number.parseInt(currentStep.setNumber, 10) || 1;

  if (!nextExercise && setNumber < setCount) {
    return { ...currentStep, setNumber: setNumber + 1, setCount };
  }

  const nextIndex = currentIndex + 1;
  if (nextIndex >= exercises.length) return null;
  const next = exercises[nextIndex];
  return {
    exerciseName: next.name,
    exerciseNumber: nextIndex + 1,
    setNumber: 1,
    setCount: Number.parseInt(next.sets, 10) || 1,
    repTarget: next.reps || null,
    loadTarget: next.load || null,
    restSeconds: parseRestSecondsForCoach(next.rest),
  };
}

function resolveWorkoutDay(programId, requestedDay = null) {
  const detail = window.getProgramDetail && programId ? window.getProgramDetail(programId) : window.PROGRAM_DETAIL;
  const days = detail?.days || [];
  if (!days.length) return null;
  if (requestedDay?.id) {
    return days.find((day) => day.id === requestedDay.id) || requestedDay;
  }
  if (requestedDay?.dayNumber) {
    return days.find((day) => Number(day.dayNumber || 0) === Number(requestedDay.dayNumber)) || days[requestedDay.dayNumber - 1] || days[0];
  }
  if (requestedDay?.title) {
    const query = normalizeCoachName(requestedDay.title);
    return days.find((day) => normalizeCoachName(day.title).includes(query) || query.includes(normalizeCoachName(day.title))) || days[0];
  }
  return days[0];
}

function getDayExercises(day, detail) {
  if (day?.blocks?.length) {
    return day.blocks.flatMap((block) => block.exercises || []);
  }
  return detail?.exercises || [];
}

function parseRestSecondsForCoach(rest) {
  const text = String(rest || '').toLowerCase();
  const value = Number.parseInt(text, 10);
  if (!Number.isFinite(value)) return null;
  return text.includes('min') ? value * 60 : value;
}

function findProgramByName(programName) {
  const query = normalizeCoachName(programName);
  if (!query) return null;
  let best = null;
  let bestScore = 0;
  (window.PROGRAMS || []).forEach((program) => {
    const name = normalizeCoachName(program.name || program.title);
    if (!name) return;
    const score = name === query || name.includes(query) || query.includes(name)
      ? 1
      : nameSimilarity(query, name);
    if (score > bestScore) {
      best = program;
      bestScore = score;
    }
  });
  return bestScore >= 0.68 ? best : null;
}

function normalizeCoachName(value) {
  return String(value || '').trim().toLowerCase().replace(/\s+/g, ' ');
}

function nameSimilarity(left, right) {
  if (!left || !right) return 0;
  const leftSet = new Set(left.split(' '));
  const rightWords = right.split(' ');
  const overlap = rightWords.filter((word) => leftSet.has(word)).length;
  return overlap / Math.max(leftSet.size, rightWords.length, 1);
}

// Fire-and-forget write-back to the Excel program spreadsheet.
// Extracts the per-week day number from the day title (e.g. "FULL BODY 2" → 2).
// Silently skips if week/day can't be determined or the exercise isn't in the sheet.
function logSetToExcel(day, exerciseName, weight) {
  if (!day || !exerciseName || weight == null) return;
  const week = day.weekNumber;
  const titleMatch = /\d+/.exec(String(day.title || ''));
  const dayNum = titleMatch ? Number(titleMatch[0]) : null;
  if (!week || !dayNum) return;
  fetch('/api/workout/log', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ week, day: dayNum, exercise_name: exerciseName, actual_load: weight }),
  }).catch(() => {});
}

function shouldAcknowledgeLongCoachTask(transcript) {
  const text = normalizeCoachName(transcript);
  return /\b(build|create|generate|make|write|program)\b/.test(text)
    && /\b(workout|program|session)\b/.test(text);
}

function App() {
  const auth = useAuth();
  const isNativeApp = Boolean(window.TRAINAR_NATIVE_APP);

  // Where in the flow are we? Start at splash unless there's already a
  // signed-in user with a name — in that case skip straight to home.
  const initialScreen = (() => {
    if (auth.user && auth.user.name && auth.user.trainingProfileComplete) return 'home';
    if (auth.user && auth.user.name) return 'training';
    return 'splash';
  })();
  const [screen, setScreen] = React.useState(initialScreen);

  // Bottom-tab state — only matters when on a tab root.
  const [activeTab, setActiveTab] = React.useState('home');

  // Auth screen mode.
  const [mode, setMode] = React.useState('signup');

  // Workout-active flag. True from "Start workout" → "Finish workout".
  const [loadedToGlasses, setLoadedToGlasses] = React.useState(false);
  const [activeProgramId, setActiveProgramId] = React.useState(null);
  const [activeSessionId, setActiveSessionId] = React.useState(null);
  const [activeWorkoutDay, setActiveWorkoutDay] = React.useState(null);
  const [activeWorkoutStep, setActiveWorkoutStep] = React.useState(null);
  const [lastLoggedSet, setLastLoggedSet] = React.useState(null);
  const [activeRest, setActiveRest] = React.useState(null);
  const activeProgramIdRef = React.useRef(activeProgramId);
  const activeSessionIdRef = React.useRef(activeSessionId);
  const activeWorkoutDayRef = React.useRef(activeWorkoutDay);
  const activeWorkoutStepRef = React.useRef(activeWorkoutStep);
  const lastLoggedSetRef = React.useRef(lastLoggedSet);
  const activeRestRef = React.useRef(activeRest);
  const loadedToGlassesRef = React.useRef(loadedToGlasses);
  const pendingLogConfirmationRef = React.useRef(null);
  const coachTurnIdRef = React.useRef(0);
  const appliedCoachTurnIdRef = React.useRef(0);
  const [selectedProgramId, setSelectedProgramId] = React.useState(null);
  const [selectedProgramFile, setSelectedProgramFile] = React.useState(null);
  const [selectedPastWorkout, setSelectedPastWorkout] = React.useState(window.PAST_WORKOUT || null);
  const [parsedProgram, setParsedProgram] = React.useState(window.PARSED_PROGRAM || null);
  const [parseError, setParseError] = React.useState(null);
  const [saveError, setSaveError] = React.useState(null);
  const [savingProgram, setSavingProgram] = React.useState(false);
  const [dataVersion, setDataVersion] = React.useState(0);
  const [glassesState, setGlassesState] = React.useState(() => ({
    connected: window.TRAINAR_GLASSES_STATE?.connected ?? false,
    battery: window.TRAINAR_GLASSES_STATE?.battery ?? null,
    lastEvent: window.TRAINAR_GLASSES_STATE?.lastEvent ?? null,
  }));
  const [coachResponse, setCoachResponse] = React.useState(null);
  // What the coach last heard — shown in the slim capsule while it's
  // listening / thinking, before the spoken reply lands.
  const [coachTranscript, setCoachTranscript] = React.useState('');
  // True from wakeWordDetected → coach-response arrival. Drives the green
  // "I'm in a coach turn" border around the whole app surface.
  const [wakeActive, setWakeActive] = React.useState(false);

  // Nav stack for the main phase. Pushing a sub-screen records what we
  // were on so the back button knows where to land.
  const [stack, setStack] = React.useState([]);

  const go = (next) => {
    setStack((prev) => [...prev, screen]);
    setScreen(next);
  };

  React.useEffect(() => {
    const onData = () => setDataVersion((version) => version + 1);
    window.addEventListener('trainar:data', onData);
    return () => window.removeEventListener('trainar:data', onData);
  }, []);

  React.useEffect(() => {
    if (auth.pending || !auth.user) return;
    if (!auth.user.name && !['splash', 'auth', 'name'].includes(screen)) {
      setScreen('name');
      return;
    }
    if (screen === 'splash' && auth.user.name && !auth.user.trainingProfileComplete) {
      setScreen('training');
      return;
    }
    if (auth.user.name && !auth.user.trainingProfileComplete && !['auth', 'name', 'training'].includes(screen)) {
      setScreen('training');
      return;
    }
    if (screen === 'splash' && auth.user.name && auth.user.trainingProfileComplete) {
      setScreen('home');
    }
  }, [auth.pending, auth.user, screen]);

  React.useEffect(() => {
    activeProgramIdRef.current = activeProgramId;
    activeSessionIdRef.current = activeSessionId;
    activeWorkoutDayRef.current = activeWorkoutDay;
    activeWorkoutStepRef.current = activeWorkoutStep;
    lastLoggedSetRef.current = lastLoggedSet;
    activeRestRef.current = activeRest;
    loadedToGlassesRef.current = loadedToGlasses;
  }, [activeProgramId, activeSessionId, activeWorkoutDay, activeWorkoutStep, lastLoggedSet, activeRest, loadedToGlasses]);

  React.useEffect(() => {
    if (!window.buildTrainARHudStateSnapshot) return;
    const hudState = window.buildTrainARHudStateSnapshot({
      programId: activeProgramId,
      day: activeWorkoutDay,
      step: activeWorkoutStep,
      rest: activeRest,
      coachResponse,
    });
    window.TRAINAR_HUD_STATE = hudState;
    window.dispatchEvent(new CustomEvent('trainar:hud-state', { detail: hudState }));
  }, [activeProgramId, activeWorkoutDay, activeWorkoutStep, activeRest, coachResponse]);

  React.useEffect(() => {
    if (auth.pending) return;
    if (!auth.user) {
      if (window.resetTrainarData) window.resetTrainarData();
      return;
    }

    if (window.loadTrainarData) {
      window.loadTrainarData(auth.user.id).catch((err) => {
        console.error('Could not load TrainAR data:', err);
      });
    }

    if (auth.user.name && auth.user.trainingProfileComplete && ['splash', 'auth'].includes(screen)) {
      switchTab('home');
    }
  }, [auth.pending, auth.user && auth.user.id, auth.user && auth.user.name, auth.user && auth.user.trainingProfileComplete]);

  const startParsingFile = (file) => {
    if (!file) return;
    setSelectedProgramFile(file);
    setParseError(null);
    setSaveError(null);
    setStack((prev) => [...prev, screen]);
    setScreen('parsing');
  };

  const back = () => {
    setStack((prev) => {
      const copy = [...prev];
      const last = copy.pop();
      if (last) setScreen(last);
      else setScreen(activeTab); // bail out to the current tab if stack is empty
      return copy;
    });
  };

  const switchTab = (tabId) => {
    setActiveTab(tabId);
    setScreen(tabId);
    setStack([]);
  };

  const restart = () => {
    auth.signOut();
    loadedToGlassesRef.current = false;
    activeProgramIdRef.current = null;
    activeSessionIdRef.current = null;
    activeWorkoutDayRef.current = null;
    activeWorkoutStepRef.current = null;
    lastLoggedSetRef.current = null;
    activeRestRef.current = null;
    setLoadedToGlasses(false);
    setActiveProgramId(null);
    setActiveSessionId(null);
    setActiveWorkoutDay(null);
    setActiveWorkoutStep(null);
    setLastLoggedSet(null);
    setActiveRest(null);
    setSelectedProgramId(null);
    setScreen('splash');
    setStack([]);
    setMode('signup');
  };

  const openProgram = (programId) => {
    const detail = window.getProgramDetail && programId ? window.getProgramDetail(programId) : null;
    setSelectedProgramId(programId || detail?.programId || null);
    setParsedProgram(detail || parsedProgram || window.PROGRAM_DETAIL);
    go('detail');
  };

  const startWorkout = async (programId, programName = null, day = null) => {
    const namedProgram = findProgramByName(programName);
    const nextProgramId = programId || namedProgram?.id || selectedProgramId || (window.PROGRAMS || [])[0]?.id || null;
    const nextDay = resolveWorkoutDay(nextProgramId, day);
    const nextStep = nextStepForProgram(nextProgramId, null, { day: nextDay });
    activeProgramIdRef.current = nextProgramId;
    activeWorkoutDayRef.current = nextDay;
    activeWorkoutStepRef.current = nextStep;
    lastLoggedSetRef.current = null;
    activeRestRef.current = null;
    loadedToGlassesRef.current = true;
    setActiveProgramId(nextProgramId);
    setLoadedToGlasses(true);
    setActiveWorkoutDay(nextDay);
    setActiveWorkoutStep(nextStep);
    setLastLoggedSet(null);
    setActiveRest(null);
    setScreen('running');
    setStack([]);
    if (window.startWorkout) {
      try {
        const sessionId = await window.startWorkout(nextProgramId);
        activeSessionIdRef.current = sessionId;
        setActiveSessionId(sessionId);
      } catch (err) {
        console.error('Could not start workout:', err);
      }
    }
  };

  const finishWorkout = async (sessionIdOverride = null, programIdOverride = null) => {
    const sessionIdToFinish = sessionIdOverride || activeSessionId;
    const programIdToFinish = programIdOverride || activeProgramId;
    const program = (window.PROGRAMS || []).find((item) => item.id === programIdToFinish);
    const optimisticWorkout = {
      id: null,
      date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      name: program?.name || 'Workout',
      totalVolume: 'Syncing',
      duration: 'Syncing',
      sets: 'Syncing',
      rpe: '—',
      exercises: [],
    };
    loadedToGlassesRef.current = false;
    activeWorkoutDayRef.current = null;
    activeWorkoutStepRef.current = null;
    lastLoggedSetRef.current = null;
    activeRestRef.current = null;
    setLoadedToGlasses(false);
    setActiveWorkoutDay(null);
    setActiveWorkoutStep(null);
    setLastLoggedSet(null);
    setActiveRest(null);
    setSelectedPastWorkout(optimisticWorkout);
    setStack([]);
    setScreen('past');
    if (window.finishWorkout && sessionIdToFinish) {
      try {
        const finishedSession = await window.finishWorkout(sessionIdToFinish, programIdToFinish);
        setSelectedPastWorkout(window.PAST_WORKOUT || optimisticWorkout);
      } catch (err) {
        console.error('Could not finish workout:', err);
        setSelectedPastWorkout(window.PAST_WORKOUT || optimisticWorkout);
      }
    } else {
      setSelectedPastWorkout(window.PAST_WORKOUT || optimisticWorkout);
    }
    activeSessionIdRef.current = null;
    setActiveSessionId(null);
  };

  const advanceWorkoutStep = () => {
    const nextStep = nextStepForProgram(activeProgramIdRef.current, activeWorkoutStepRef.current, { day: activeWorkoutDayRef.current });
    activeWorkoutStepRef.current = nextStep;
    lastLoggedSetRef.current = null;
    activeRestRef.current = null;
    setActiveWorkoutStep(nextStep);
    setLastLoggedSet(null);
    setActiveRest(null);
  };

  const skipWorkoutExercise = () => {
    const nextStep = nextStepForProgram(activeProgramIdRef.current, activeWorkoutStepRef.current, {
      nextExercise: true,
      day: activeWorkoutDayRef.current,
    });
    activeWorkoutStepRef.current = nextStep;
    lastLoggedSetRef.current = null;
    activeRestRef.current = null;
    setActiveWorkoutStep(nextStep);
    setLastLoggedSet(null);
    setActiveRest(null);
  };

  const openHudDemo = () => {
    setStack((prev) => [...prev, screen]);
    setScreen('hud');
  };

  React.useEffect(() => {
    const onGlassesState = (event) => {
      setGlassesState(event.detail || {});
    };

    const onGlassesEvent = (event) => {
      const detail = event.detail || {};
      const transcript = String(detail.payload?.transcript || '').toLowerCase();

      if (detail.type === 'wakeWordDetected') {
        // Fresh turn: clear any lingering reply and show the listening capsule.
        setWakeActive(true);
        setCoachTranscript('');
        setCoachResponse(null);
        return;
      }

      if (detail.type !== 'voiceCommand') return;

      if (window.askTrainARCoach && transcript) {
        const clientTurnId = coachTurnIdRef.current + 1;
        coachTurnIdRef.current = clientTurnId;
        // Show what was heard, then a "thinking" capsule while the coach works.
        setWakeActive(true);
        setCoachTranscript(transcript);
        if (shouldAcknowledgeLongCoachTask(transcript)) {
          setCoachResponse({ response: 'Working on it.', processing: true });
          window.dispatchEvent(new CustomEvent('trainar:speak', {
            detail: { text: 'Working on it.' },
          }));
        } else {
          setCoachResponse({ processing: true });
        }
        const currentProgramId = activeProgramIdRef.current;
        const currentSessionId = activeSessionIdRef.current;
        const currentDay = activeWorkoutDayRef.current;
        const currentStep = activeWorkoutStepRef.current;
        const currentRest = activeRestRef.current;
        window.askTrainARCoach(transcript, {
          activeProgramId: currentProgramId,
          clientTurnId,
          currentWorkout: loadedToGlassesRef.current ? {
            programId: currentProgramId,
            sessionId: currentSessionId,
            title: (window.PROGRAMS || []).find((program) => program.id === currentProgramId)?.name,
            day: currentDay,
            step: currentStep,
            rest: currentRest,
          } : null,
          pendingLogConfirmation: pendingLogConfirmationRef.current,
        }).catch((err) => {
          setCoachResponse({ response: err.message || 'Coach assistant failed.' });
          setWakeActive(false);
        });
        return;
      }

      if (transcript.includes('finish') || transcript.includes('end workout')) {
        finishWorkout();
        return;
      }

      if (transcript.includes('start') || transcript.includes('begin workout')) {
        startWorkout(activeProgramId || selectedProgramId || (window.PROGRAMS || [])[0]?.id || null);
      }
    };

    const onCoachResponse = (event) => {
      const detail = event.detail || null;
      if (detail?.actionResult?.needs_confirmation && detail.actionResult.requested_exercise) {
        pendingLogConfirmationRef.current = {
          sessionId: activeSessionIdRef.current,
          programId: activeProgramIdRef.current,
          exerciseName: detail.actionResult.requested_exercise,
          reps: detail.actionResult.reps,
          weight: detail.actionResult.weight,
        };
      } else if (detail?.actionResult?.cleared_pending_confirmation || detail?.uiPatch?.type === 'set_logged') {
        pendingLogConfirmationRef.current = null;
      }
      setCoachResponse(detail);
      setWakeActive(Boolean(detail?.expectsFollowUp));
    };

    const onCoachAction = async (event) => {
      const clientTurnId = Number(event.detail?.clientTurnId || 0);
      if (clientTurnId && clientTurnId < appliedCoachTurnIdRef.current) return;
      if (clientTurnId) appliedCoachTurnIdRef.current = clientTurnId;
      const patch = event.detail?.uiPatch;
      if (!patch || !patch.type) return;

      if (patch.type === 'program_created') {
        const programId = patch.programId || null;
        let detail = null;
        if (window.upsertTrainarProgramCache && (patch.program || patch.detail)) {
          detail = window.upsertTrainarProgramCache(patch.program, patch.detail);
        }
        if (auth.user && window.loadTrainarData) {
          try {
            await window.loadTrainarData(auth.user.id);
          } catch (err) {
            console.error('Could not refresh TrainAR data:', err);
          }
        }
        if (programId) {
          if (window.upsertTrainarProgramCache && (patch.program || patch.detail)) {
            detail = window.upsertTrainarProgramCache(patch.program, patch.detail) || detail;
          }
          detail = detail || (window.getProgramDetail ? window.getProgramDetail(programId) : null);
          setSelectedProgramId(programId);
          setParsedProgram(detail || patch.detail || null);
          setStack((prev) => [...prev, 'home']);
          setScreen('detail');
        }
        return;
      }

      if (patch.type === 'workout_started') {
        if (window.upsertTrainarProgramCache && (patch.program || patch.detail)) {
          window.upsertTrainarProgramCache(patch.program, patch.detail);
        }
        const nextDay = patch.day || resolveWorkoutDay(patch.programId || activeProgramId, null);
        const nextProgramId = patch.programId || activeProgramId;
        const nextStep = patch.step || nextStepForProgram(nextProgramId, null, { day: nextDay });
        activeProgramIdRef.current = nextProgramId;
        activeSessionIdRef.current = patch.sessionId || null;
        activeWorkoutDayRef.current = nextDay;
        activeWorkoutStepRef.current = nextStep;
        lastLoggedSetRef.current = null;
        activeRestRef.current = null;
        loadedToGlassesRef.current = true;
        setActiveProgramId(nextProgramId);
        setActiveSessionId(patch.sessionId || null);
        setActiveWorkoutDay(nextDay);
        setActiveWorkoutStep(nextStep);
        setLastLoggedSet(null);
        setActiveRest(null);
        setLoadedToGlasses(true);
        setScreen('running');
        setStack([]);
        if (auth.user && window.loadTrainarData) {
          window.loadTrainarData(auth.user.id).catch((err) => console.error('Could not refresh TrainAR data:', err));
        }
        return;
      }

      if (patch.type === 'workout_finished') {
        loadedToGlassesRef.current = false;
        activeSessionIdRef.current = null;
        activeWorkoutDayRef.current = null;
        activeWorkoutStepRef.current = null;
        lastLoggedSetRef.current = null;
        activeRestRef.current = null;
        setLoadedToGlasses(false);
        setActiveSessionId(null);
        setActiveWorkoutDay(null);
        setActiveWorkoutStep(null);
        setLastLoggedSet(null);
        setActiveRest(null);
        if (auth.user && window.loadTrainarData) {
          window.loadTrainarData(auth.user.id).catch((err) => console.error('Could not refresh TrainAR data:', err));
        }
        setSelectedPastWorkout(window.PAST_WORKOUT || null);
        setStack([]);
        setScreen('past');
        return;
      }

      if (patch.type === 'set_logged') {
        if (Object.prototype.hasOwnProperty.call(patch, 'step')) {
          activeWorkoutStepRef.current = patch.step || null;
          activeRestRef.current = null;
          setActiveWorkoutStep(patch.step || null);
          setActiveRest(null);
        }
        if (patch.loggedSet) {
          lastLoggedSetRef.current = patch.loggedSet;
          setLastLoggedSet(patch.loggedSet);
        }
        if (auth.user && window.loadTrainarData) {
          window.loadTrainarData(auth.user.id).catch((err) => console.error('Could not refresh TrainAR data:', err));
        }
        return;
      }

      if (patch.type === 'start_workout') {
        startWorkout(patch.programId || activeProgramId || null, patch.programName || null, patch.day || null);
        return;
      }

      if (patch.type === 'finish_workout') {
        finishWorkout(patch.sessionId, patch.programId);
        return;
      }

      if (patch.type === 'log_set') {
        const sessionIdToLog = patch.sessionId || activeSessionId;
        if (!sessionIdToLog || !window.logWorkoutSet) return;
        window.logWorkoutSet(sessionIdToLog, {
          exerciseName: patch.exerciseName,
          reps: patch.reps,
          weight: patch.weight,
          programId: activeProgramIdRef.current,
          currentExerciseName: activeWorkoutStepRef.current?.exerciseName,
        }).then((result) => {
          const logged = {
            exerciseName: result?.exerciseLog?.exercise_name || patch.exerciseName || activeWorkoutStepRef.current?.exerciseName,
            setNumber: result?.set?.set_number || null,
            reps: result?.set?.reps ?? patch.reps,
            weight: result?.set?.load_value ?? patch.weight,
          };
          lastLoggedSetRef.current = logged;
          setLastLoggedSet(logged);
          logSetToExcel(activeWorkoutDayRef.current, logged.exerciseName, logged.weight);
        }).catch((err) => {
          setCoachResponse({ response: err.message || 'Could not log that set.' });
        });
        return;
      }

      if (patch.type === 'exercise_started' || patch.type === 'workout_step_updated') {
        activeWorkoutStepRef.current = patch.step || null;
        lastLoggedSetRef.current = null;
        activeRestRef.current = null;
        setActiveWorkoutStep(patch.step || null);
        setLastLoggedSet(null);
        setActiveRest(null);
        if (patch.step) setScreen('running');
        return;
      }

      if (patch.type === 'rest_started') {
        const nextRest = {
          durationSeconds: patch.durationSeconds || 90,
          startedAt: new Date().toISOString(),
        };
        activeRestRef.current = nextRest;
        if (patch.step) activeWorkoutStepRef.current = patch.step;
        if (patch.step) lastLoggedSetRef.current = null;
        setActiveRest({
          durationSeconds: nextRest.durationSeconds,
          startedAt: nextRest.startedAt,
        });
        if (patch.step) setActiveWorkoutStep(patch.step);
        if (patch.step) setLastLoggedSet(null);
        return;
      }

      if (patch.type === 'start_rest') {
        const nextRest = {
          durationSeconds: patch.durationSeconds || activeWorkoutStepRef.current?.restSeconds || 90,
          startedAt: new Date().toISOString(),
        };
        activeRestRef.current = nextRest;
        setActiveRest({
          durationSeconds: nextRest.durationSeconds,
          startedAt: nextRest.startedAt,
        });
        return;
      }

      if (patch.type === 'start_exercise') {
        const exerciseName = patch.exerciseName || activeWorkoutStepRef.current?.exerciseName;
        const nextStep = {
          ...(activeWorkoutStepRef.current || {}),
          exerciseName,
          setNumber: 1,
          setCount: activeWorkoutStepRef.current?.setCount || 1,
        };
        activeWorkoutStepRef.current = nextStep;
        lastLoggedSetRef.current = null;
        activeRestRef.current = null;
        setActiveWorkoutStep(nextStep);
        setLastLoggedSet(null);
        setActiveRest(null);
        setScreen('running');
        return;
      }

      if (patch.type === 'advance_set') {
        advanceWorkoutStep();
        setActiveRest(null);
        return;
      }

      if (patch.type === 'skip_exercise' || patch.type === 'finish_exercise') {
        skipWorkoutExercise();
        setScreen('running');
      }
    };

    window.addEventListener('trainar:glasses-state', onGlassesState);
    window.addEventListener('trainar:glasses', onGlassesEvent);
    window.addEventListener('trainar:coach-response', onCoachResponse);
    window.addEventListener('trainar:coach-action', onCoachAction);
    return () => {
      window.removeEventListener('trainar:glasses-state', onGlassesState);
      window.removeEventListener('trainar:glasses', onGlassesEvent);
      window.removeEventListener('trainar:coach-response', onCoachResponse);
      window.removeEventListener('trainar:coach-action', onCoachAction);
    };
  }, [activeProgramId, selectedProgramId, activeSessionId, activeWorkoutDay, activeWorkoutStep, activeRest, loadedToGlasses]);

  const openWorkout = async (sessionId) => {
    let workout = null;
    if (window.selectPastWorkout) {
      try {
        workout = await window.selectPastWorkout(sessionId);
      } catch (err) {
        console.error('Could not load workout detail:', err);
      }
    }
    if (workout) {
      setSelectedPastWorkout(workout);
      go('past');
    }
  };

  const deletePastWorkout = async (sessionId) => {
    if (!sessionId || !window.deleteWorkoutSession) return;
    const previousWorkout = selectedPastWorkout;
    setSelectedPastWorkout(null);
    setStack([]);
    setActiveTab('calendar');
    setScreen('calendar');
    try {
      await window.deleteWorkoutSession(sessionId);
    } catch (err) {
      console.error('Could not delete workout:', err);
      setSelectedPastWorkout(previousWorkout);
      setScreen('past');
      setCoachResponse({ response: err.message || 'Could not delete that workout.' });
    }
  };

  const screens = {
    // ── Signup phase ────────────────────────────────────────────
    splash: (
      <SplashScreen
        onSignUp={() => { setMode('signup'); setScreen('auth'); }}
        onSignIn={() => { setMode('login');  setScreen('auth'); }}
      />
    ),
    auth: (
      <AuthScreen
        auth={auth}
        initialMode={mode}
        onContinue={() => setScreen(mode === 'signup' ? 'name' : 'training')}
        onBack={() => setScreen('splash')}
      />
    ),
    name: (
      <NameScreen
        auth={auth}
        onContinue={() => setScreen('training')}
        onBack={() => setScreen('auth')}
      />
    ),
    training: (
      <TrainingProfileScreen
        auth={auth}
        onContinue={() => (stack.length ? back() : switchTab('home'))}
        onBack={() => (stack.length ? back() : setScreen(auth.user && auth.user.name ? 'name' : 'auth'))}
      />
    ),

    // ── Tab roots ───────────────────────────────────────────────
    home: (
      <HomeScreen
        key={`home-${dataVersion}-${activeProgramId || 'none'}`}
        glassesConnected={Boolean(glassesState.connected)}
        glassesBattery={glassesState.battery}
        loadedToGlasses={loadedToGlasses}
        activeProgramId={activeProgramId}
        onAddProgram={() => go('add')}
        onOpenProgram={(programId) => {
          if (loadedToGlasses) setScreen('running');
          else openProgram(programId || activeProgramId || selectedProgramId || (window.PROGRAMS || [])[0]?.id || null);
        }}
        // Quick-start from the round green glasses button stays on home —
        // the screen re-renders into the active hero card.
        onActivate={startWorkout}
        onFinish={finishWorkout}
      />
    ),
    calendar: <CalendarScreen key={`calendar-${dataVersion}`} onOpenWorkout={openWorkout} />,
    profile:  (
      <ProfileScreen
        key={`profile-${dataVersion}-${glassesState.connected ? 'connected' : 'idle'}`}
        user={auth.user}
        glassesState={glassesState}
        onEditTraining={() => go('training')}
      />
    ),

    running: (
      <RunningWorkoutScreen
        key={`running-${dataVersion}-${activeProgramId || 'none'}-${activeWorkoutStep?.exerciseName || 'none'}-${activeWorkoutStep?.setNumber || 1}`}
        programId={activeProgramId}
        sessionId={activeSessionId}
        day={activeWorkoutDay}
        step={activeWorkoutStep}
        lastLoggedSet={lastLoggedSet}
        rest={activeRest}
        onClose={() => switchTab('home')}
        onOpenHud={openHudDemo}
        onFinish={finishWorkout}
        onNextSet={advanceWorkoutStep}
        onSkipExercise={skipWorkoutExercise}
      />
    ),

    hud: (
      <HudDemoScreen
        programId={activeProgramId}
        day={activeWorkoutDay}
        step={activeWorkoutStep}
        rest={activeRest}
        coachResponse={coachResponse}
        onClose={back}
      />
    ),

    // ── Add-program flow (sub-screens of home) ──────────────────
    add: (
      <AddProgramScreen
        onCamera={() => setScreen('camera')}
        onFileSelected={startParsingFile}
        onClose={back}
      />
    ),
    camera: (
      <CameraScreen
        onFileSelected={startParsingFile}
        onClose={() => setScreen('add')}
      />
    ),
    parsing: (
      <ParsingScreen
        file={selectedProgramFile}
        error={parseError}
        onCancel={back}
        onDone={(detail) => {
          setParsedProgram(detail);
          setParseError(null);
          setScreen('review');
        }}
        onFailed={(message) => {
          setParseError(message);
          setScreen('failed');
        }}
      />
    ),
    review: (
      <ReviewScreen
        program={parsedProgram}
        saving={savingProgram}
        error={saveError}
        // After save, take them to the detail view of what they just imported.
        onConfirm={async ({ name } = {}) => {
          const detail = { ...(parsedProgram || window.PARSED_PROGRAM), name: name || parsedProgram?.name };
          setSavingProgram(true);
          setSaveError(null);
          try {
            const programId = await installParsedProgram(detail);
            const savedDetail = (window.getProgramDetail && programId && window.getProgramDetail(programId)) || detail;
            setSelectedProgramId(programId || savedDetail.programId || null);
            setParsedProgram(savedDetail);
            setStack([]);
            setScreen('detail');
          } catch (err) {
            setSaveError(err.message || 'Could not save this program.');
          } finally {
            setSavingProgram(false);
          }
        }}
        onClose={() =>   { setStack([]); setScreen('home'); setActiveTab('home'); }}
      />
    ),
    failed: (
      <FailedScanScreen
        error={parseError}
        onRetry={() => setScreen(selectedProgramFile ? 'parsing' : 'add')}
        onClose={() => { setStack([]); setScreen('home'); setActiveTab('home'); }}
      />
    ),

    // ── Program detail + past workout ───────────────────────────
    detail: (
      <ProgramViewScreen
        key={`detail-${selectedProgramId || parsedProgram?.programId || 'parsed'}-${dataVersion}`}
        program={parsedProgram}
        loadedToGlasses={loadedToGlasses}
        onClose={back}
        onStartWorkout={() => startWorkout(selectedProgramId || parsedProgram?.programId)}
        onFinishWorkout={finishWorkout}
        onDiscard={async () => {
          const programId = selectedProgramId || parsedProgram?.programId || null;
          if (!window.archiveProgram) throw new Error('Program discard is not available.');
          await window.archiveProgram(programId);
          setSelectedProgramId(null);
          setParsedProgram(window.PROGRAM_DETAIL || null);
          setStack([]);
          setScreen('home');
          setActiveTab('home');
        }}
      />
    ),
    past: (
      <PastWorkoutScreen
        key={`past-${selectedPastWorkout?.id || dataVersion}`}
        workout={selectedPastWorkout || window.PAST_WORKOUT}
        onBack={back}
        onDelete={deletePastWorkout}
      />
    ),
  };

  const showTabBar = SCREENS_WITH_TABBAR.includes(screen);
  const showSignoutDev = !SIGNUP_SCREENS.includes(screen);

  const appSurface = (
    <div style={{
      width: '100%',
      height: '100%',
      minHeight: isNativeApp ? '100vh' : 'auto',
      position: 'relative',
      background: screen === 'hud' ? 'transparent' : 'var(--bg)',
      color: 'var(--text-1)',
      overflow: 'hidden',
    }}>
      {screens[screen]}
      {showTabBar && (
        <TabBar active={activeTab} live={loadedToGlasses} onTab={switchTab} />
      )}
      {screen !== 'hud' && (wakeActive || coachResponse?.response || coachResponse?.processing) && (
        <CoachCapsule
          state={
            coachResponse?.response && !coachResponse?.processing
              ? 'result'
              : (coachResponse?.processing ? 'thinking' : 'listening')
          }
          transcript={coachTranscript}
          result={
            coachResponse?.response && !coachResponse?.processing
              ? {
                  text: coachResponse.response,
                  kind: (coachResponse.action || coachResponse.uiPatch) ? 'action' : 'info',
                }
              : null
          }
          sources={coachResponse?.sources || []}
          onClose={() => { setCoachResponse(null); setCoachTranscript(''); setWakeActive(false); }}
        />
      )}
      {wakeActive && <WakeListeningBorder isNativeApp={isNativeApp} />}
    </div>
  );

  return (
    <div style={{
      padding: isNativeApp ? 0 : 32,
      position: 'relative',
      width: isNativeApp ? '100vw' : 'auto',
      height: isNativeApp ? '100vh' : 'auto',
      background: screen === 'hud' ? 'transparent' : 'var(--bg)',
    }}>
      {isNativeApp ? appSurface : (
        <IOSDevice width={PROTOTYPE_W} height={PROTOTYPE_H} dark={true}>
          {appSurface}
        </IOSDevice>
      )}

      {/* Tiny dev affordance — sign out + reset, so the prototype can be
          replayed from splash without clearing localStorage by hand. */}
      {showSignoutDev && !isNativeApp && (
        <button onClick={restart} style={{
          position: 'absolute', top: 8, right: 8,
          padding: '6px 10px', borderRadius: 9999,
          background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
          color: 'rgba(255,255,255,0.7)', fontSize: 11, cursor: 'pointer',
          fontFamily: 'var(--font-sans)',
        }}>Reset prototype</button>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

// Full-bleed lime border that lights up the moment the wake word is heard
// and stays on through the round-trip until the coach response arrives.
// `position: absolute; inset: 0` sits over the whole appSurface; pointer-
// events disabled so it never swallows taps meant for the UI underneath.
const WakeListeningBorder = ({ isNativeApp }) => (
  <div
    aria-hidden="true"
    style={{
      position: 'absolute',
      inset: 0,
      pointerEvents: 'none',
      border: '4px solid var(--accent)',
      boxShadow: 'inset 0 0 28px rgba(197, 242, 62, 0.45)',
      borderRadius: isNativeApp ? 0 : 38,
      zIndex: 9,
    }}
  />
);
