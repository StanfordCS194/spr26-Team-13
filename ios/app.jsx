// App — wires the signup screens into the iPhone frame.
//
// Tiny state machine: 'splash' → 'auth' → 'name' → 'pair' → 'done'.
// `mode` decides whether the auth screen opens in signup or sign-in mode.

const PROTOTYPE_W = 402;
const PROTOTYPE_H = 874;

function App() {
  const auth = useAuth();
  const [screen, setScreen] = React.useState('splash');
  const [mode, setMode] = React.useState('signup');

  // If a returning user already has a name, skip ahead to "done" on first render.
  // Easy to remove once the rest of the app exists to land them in.
  React.useEffect(() => {
    if (auth.user && auth.user.name && screen === 'splash') setScreen('done');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const restart = () => {
    auth.signOut();
    setScreen('splash');
    setMode('signup');
  };

  const screens = {
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
        onContinue={() => setScreen('done')}
        onSkip={() => setScreen('done')}
        onBack={() => setScreen(auth.user && auth.user.name ? 'name' : 'auth')}
      />
    ),
    done: <DoneScreen auth={auth} onRestart={restart} />,
  };

  return (
    <div style={{ padding: 32 }}>
      <IOSDevice width={PROTOTYPE_W} height={PROTOTYPE_H} dark={true}>
        <div style={{ width: '100%', height: '100%', position: 'relative', background: 'var(--bg)', color: 'var(--text-1)' }}>
          {screens[screen]}
        </div>
      </IOSDevice>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
