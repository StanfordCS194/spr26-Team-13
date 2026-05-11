// App — wires every screen into the iPhone frame.
//
// State machine (high level):
//   signup phase: splash → auth → name → pair → home
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
const SIGNUP_SCREENS = ['splash', 'auth', 'name', 'pair'];

function App() {
  const auth = useAuth();
  const isNativeApp = Boolean(window.TRAINAR_NATIVE_APP);

  // Where in the flow are we? Start at splash unless there's already a
  // signed-in user with a name — in that case skip straight to home.
  const initialScreen = (() => {
    if (auth.user && auth.user.name) return 'home';
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
  const [selectedProgramId, setSelectedProgramId] = React.useState(null);
  const [selectedProgramFile, setSelectedProgramFile] = React.useState(null);
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

    if (auth.user.name && SIGNUP_SCREENS.includes(screen)) {
      switchTab('home');
    }
  }, [auth.pending, auth.user && auth.user.id, auth.user && auth.user.name]);

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
    setLoadedToGlasses(false);
    setActiveProgramId(null);
    setActiveSessionId(null);
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

  const startWorkout = async (programId) => {
    const nextProgramId = programId || selectedProgramId || (window.PROGRAMS || [])[0]?.id || null;
    setActiveProgramId(nextProgramId);
    setLoadedToGlasses(true);
    if (window.startWorkout) {
      try {
        const sessionId = await window.startWorkout(nextProgramId);
        setActiveSessionId(sessionId);
      } catch (err) {
        console.error('Could not start workout:', err);
      }
    }
  };

  const finishWorkout = async () => {
    setLoadedToGlasses(false);
    if (window.finishWorkout && activeSessionId) {
      try {
        await window.finishWorkout(activeSessionId, activeProgramId);
      } catch (err) {
        console.error('Could not finish workout:', err);
      }
    }
    setActiveSessionId(null);
    go('past');
  };

  React.useEffect(() => {
    const onGlassesState = (event) => {
      setGlassesState(event.detail || {});
    };

    const onGlassesEvent = (event) => {
      const detail = event.detail || {};
      const transcript = String(detail.payload?.transcript || '').toLowerCase();

      if (detail.type !== 'voiceCommand') return;

      if (window.askTrainARCoach && transcript) {
        window.askTrainARCoach(transcript, {
          activeProgramId,
          currentWorkout: loadedToGlasses ? {
            programId: activeProgramId,
            sessionId: activeSessionId,
            title: (window.PROGRAMS || []).find((program) => program.id === activeProgramId)?.name,
          } : null,
        }).catch((err) => {
          setCoachResponse({ response: err.message || 'Coach assistant failed.' });
        });
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
      setCoachResponse(event.detail || null);
    };

    window.addEventListener('trainar:glasses-state', onGlassesState);
    window.addEventListener('trainar:glasses', onGlassesEvent);
    window.addEventListener('trainar:coach-response', onCoachResponse);
    return () => {
      window.removeEventListener('trainar:glasses-state', onGlassesState);
      window.removeEventListener('trainar:glasses', onGlassesEvent);
      window.removeEventListener('trainar:coach-response', onCoachResponse);
    };
  }, [activeProgramId, selectedProgramId, activeSessionId, loadedToGlasses]);

  const openWorkout = async (sessionId) => {
    if (window.selectPastWorkout) {
      try {
        await window.selectPastWorkout(sessionId);
      } catch (err) {
        console.error('Could not load workout detail:', err);
      }
    }
    go('past');
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
        onContinue={() => setScreen(mode === 'signup' ? 'name' : 'pair')}
        onBack={() => setScreen('splash')}
      />
    ),
    name: (
      <NameScreen
        auth={auth}
        onContinue={() => setScreen('pair')}
        onBack={() => setScreen('auth')}
      />
    ),
    pair: (
      <PairScreen
        onContinue={() => switchTab('home')}
        onSkip={() => switchTab('home')}
        onBack={() => setScreen(auth.user && auth.user.name ? 'name' : 'auth')}
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
        onOpenProgram={openProgram}
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
        onDiscard={() => {
          if (window.archiveProgram && selectedProgramId) {
            window.archiveProgram(selectedProgramId).catch((err) => console.error('Could not archive program:', err));
          }
          setStack([]);
          setScreen('home');
          setActiveTab('home');
        }}
      />
    ),
    past: <PastWorkoutScreen key={`past-${dataVersion}`} onBack={back} />,
  };

  const showTabBar = SCREENS_WITH_TABBAR.includes(screen);
  const showSignoutDev = !SIGNUP_SCREENS.includes(screen) && screen !== 'pair';

  const appSurface = (
    <div style={{
      width: '100%',
      height: '100%',
      minHeight: isNativeApp ? '100vh' : 'auto',
      position: 'relative',
      background: 'var(--bg)',
      color: 'var(--text-1)',
      overflow: 'hidden',
    }}>
      {screens[screen]}
      {showTabBar && (
        <TabBar active={activeTab} live={loadedToGlasses} onTab={switchTab} />
      )}
      {coachResponse?.response && (
        <CoachOverlay
          response={coachResponse.response}
          onClose={() => setCoachResponse(null)}
        />
      )}
    </div>
  );

  return (
    <div style={{
      padding: isNativeApp ? 0 : 32,
      position: 'relative',
      width: isNativeApp ? '100vw' : 'auto',
      height: isNativeApp ? '100vh' : 'auto',
      background: 'var(--bg)',
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

const CoachOverlay = ({ response, onClose }) => (
  <div style={{
    position: 'absolute',
    left: 18,
    right: 18,
    bottom: 86,
    zIndex: 8,
    padding: 14,
    borderRadius: 18,
    background: 'rgba(20, 24, 18, 0.94)',
    border: '1px solid rgba(197,242,62,0.24)',
    boxShadow: '0 12px 32px rgba(0,0,0,0.45)',
    display: 'flex',
    gap: 12,
    alignItems: 'flex-start',
  }}>
    <div style={{
      width: 30,
      height: 30,
      borderRadius: 15,
      flexShrink: 0,
      background: 'var(--accent-soft)',
      color: 'var(--accent)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <Icon name="sparkle" size={16} />
    </div>
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent)', marginBottom: 3 }}>
        Coach
      </div>
      <div style={{ fontSize: 13, lineHeight: 1.35, color: 'var(--text-1)' }}>
        {response}
      </div>
    </div>
    <button
      onClick={onClose}
      aria-label="Dismiss coach response"
      style={{
        width: 28,
        height: 28,
        borderRadius: 14,
        border: '1px solid var(--hairline)',
        background: 'var(--overlay-1)',
        color: 'var(--text-2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        flexShrink: 0,
      }}
    >
      <Icon name="x" size={14} />
    </button>
  </div>
);
