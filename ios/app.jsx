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
        glassesConnected={true}
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
    profile:  <ProfileScreen key={`profile-${dataVersion}`} user={auth.user} />,

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

  return (
    <div style={{ padding: 32, position: 'relative' }}>
      <IOSDevice width={PROTOTYPE_W} height={PROTOTYPE_H} dark={true}>
        <div style={{ width: '100%', height: '100%', position: 'relative', background: 'var(--bg)', color: 'var(--text-1)' }}>
          {screens[screen]}
          {showTabBar && (
            <TabBar active={activeTab} live={loadedToGlasses} onTab={switchTab} />
          )}
        </div>
      </IOSDevice>

      {/* Tiny dev affordance — sign out + reset, so the prototype can be
          replayed from splash without clearing localStorage by hand. */}
      {showSignoutDev && (
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
