// Signup flow screens: Splash → Auth → Name.
//
// Each screen is self-contained and takes onContinue/onBack callbacks.
// State (email, password, name) lives in the screen itself; submission
// is delegated to the auth hook passed in from app.jsx.

// ─────────────────────────────────────────────────────────────
// Screen wrapper — gives every screen the safe area + bg.
// ─────────────────────────────────────────────────────────────
const Screen = ({ children, padTop = 60, padBottom = 40, style = {} }) => (
  <div className="no-scrollbar fade-up" style={{
    width: '100%',
    height: window.TRAINAR_NATIVE_APP ? '100dvh' : '100%',
    background: 'var(--bg)',
    paddingTop: window.TRAINAR_NATIVE_APP ? `calc(${padTop}px + env(safe-area-inset-top, 0px))` : padTop,
    paddingBottom: window.TRAINAR_NATIVE_APP ? `calc(${padBottom}px + env(safe-area-inset-bottom, 0px))` : padBottom,
    overflowY: 'auto', position: 'relative',
    fontFamily: 'var(--font-sans)', color: 'var(--text-1)',
    ...style,
  }}>{children}</div>
);

// ─────────────────────────────────────────────────────────────
// 1. Splash — welcome with the glasses visor graphic.
// ─────────────────────────────────────────────────────────────
const SplashScreen = ({ onSignUp, onSignIn }) => (
  <Screen padTop={0} padBottom={0} style={{ display: 'flex', flexDirection: 'column' }}>
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      justifyContent: 'center', alignItems: 'center', position: 'relative',
      background: 'radial-gradient(120% 80% at 50% 30%, rgba(197,242,62,0.18), transparent 60%)',
      paddingTop: 80,
    }}>
      {/* Glasses visor — pure CSS */}
      <div style={{ width: 220, height: 110, position: 'relative', marginBottom: 56 }}>
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '50%',
          border: '1.5px solid var(--accent)',
          boxShadow: '0 0 60px rgba(197,242,62,0.4), inset 0 0 30px rgba(197,242,62,0.15)',
          background: 'linear-gradient(180deg, rgba(197,242,62,0.08), transparent 60%)',
        }} />
        <div style={{
          position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
          fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: 3,
          color: 'rgba(197,242,62,0.7)',
        }}>TRAIN.AR</div>
      </div>

      <div style={{ textAlign: 'center', padding: '0 32px' }}>
        <h1 style={{
          fontSize: 40, lineHeight: 1.05, fontWeight: 600, letterSpacing: -1.2,
          margin: 0, marginBottom: 14,
        }}>
          Train heads-up.<br/>
          <span style={{ color: 'var(--accent)' }}>Eyes on the bar.</span>
        </h1>
        <p style={{
          fontSize: 15, lineHeight: 1.5, color: 'var(--text-2)', margin: 0,
          maxWidth: 300, marginInline: 'auto',
        }}>
          Your program lives in your AR glasses. The phone is just for setup.
        </p>
      </div>
    </div>

    <div style={{ padding: '0 24px 40px', display: 'flex', flexDirection: 'column', gap: 10 }}>
      <Button onClick={onSignUp} iconRight="arrow-right">Get started</Button>
      <button onClick={onSignIn} className="press" style={{
        background: 'transparent', border: 'none', color: 'var(--text-2)',
        fontSize: 14, padding: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
      }}>I already have an account</button>
    </div>
  </Screen>
);

// ─────────────────────────────────────────────────────────────
// 2. Auth — email + password, signup/login toggle.
// ─────────────────────────────────────────────────────────────
const AuthScreen = ({ auth, initialMode = 'signup', onContinue, onBack }) => {
  const [mode, setMode] = React.useState(initialMode);
  const [email, setEmail] = React.useState('');
  const [pw, setPw] = React.useState('');
  const [show, setShow] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);

  const strength = scorePassword(pw);
  const strengthLabel = ['', 'Weak', 'Fair', 'Good', 'Strong'][strength];

  const submit = async () => {
    setSubmitting(true);
    const fn = mode === 'signup' ? auth.signUp : auth.signIn;
    const ok = await fn({ email, password: pw });
    setSubmitting(false);
    if (ok) onContinue();
  };

  const ctaDisabled = !email || !pw || submitting;

  return (
    <Screen padTop={64} padBottom={32} style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0 24px' }}>
        <button onClick={onBack} className="press" style={{
          width: 40, height: 40, borderRadius: 9999, background: 'var(--surface-1)',
          border: '1px solid var(--hairline)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
          marginBottom: 32,
        }}><Icon name="arrow-left" size={18} /></button>

        <h1 style={{ fontSize: 30, lineHeight: 1.1, fontWeight: 600, letterSpacing: -0.8, margin: 0, marginBottom: 12 }}>
          {mode === 'signup' ? 'Create your account' : 'Welcome back'}
        </h1>
        <p style={{ fontSize: 14, lineHeight: 1.5, color: 'var(--text-2)', margin: 0, marginBottom: 28 }}>
          {mode === 'signup'
            ? "We'll sync this account to your glasses so your programs follow you everywhere."
            : 'Sign in to pick up where you left off.'}
        </p>

        <Field
          label="Email"
          icon="mail"
          type="email"
          value={email}
          onChange={setEmail}
          placeholder="you@example.com"
        />

        <Field
          label="Password"
          type={show ? 'text' : 'password'}
          value={pw}
          onChange={setPw}
          placeholder="At least 8 characters"
          trailing={
            <button onClick={() => setShow(!show)} style={{
              background: 'transparent', border: 'none', color: 'var(--text-3)',
              cursor: 'pointer', display: 'flex', alignItems: 'center',
            }}><Icon name={show ? 'eye-off' : 'eye'} size={18} stroke="var(--text-3)" /></button>
          }
        />

        {mode === 'signup' && pw && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '-4px 4px 16px' }}>
            <div style={{ display: 'flex', gap: 3, flex: 1 }}>
              {[1, 2, 3, 4].map((i) => (
                <div key={i} style={{
                  flex: 1, height: 3, borderRadius: 2,
                  background: i <= strength ? 'var(--accent)' : 'var(--overlay-3)',
                }} />
              ))}
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-3)', minWidth: 40, textAlign: 'right' }}>
              {strengthLabel}
            </span>
          </div>
        )}

        {auth.error && (
          <div style={{
            fontSize: 13, color: '#FF8B7C', marginBottom: 12, padding: '0 4px',
          }}>{auth.error}</div>
        )}

        <Button onClick={submit} iconRight="arrow-right" disabled={ctaDisabled}>
          {submitting
            ? (mode === 'signup' ? 'Creating account…' : 'Signing in…')
            : (mode === 'signup' ? 'Create account' : 'Sign in')}
        </Button>

        <button
          onClick={() => setMode(mode === 'signup' ? 'login' : 'signup')}
          className="press"
          style={{
            width: '100%', background: 'transparent', border: 'none', color: 'var(--text-2)',
            fontSize: 13, padding: 16, marginTop: 8, cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}
        >
          {mode === 'signup' ? 'Already have an account? Sign in' : 'New here? Create an account'}
        </button>
      </div>

      <div style={{ flex: 1 }} />

      <div style={{ padding: '0 24px', textAlign: 'center' }}>
        <p style={{ fontSize: 11, color: 'var(--text-3)', lineHeight: 1.5, margin: 0 }}>
          By continuing you agree to our Terms and Privacy Policy.
        </p>
      </div>
    </Screen>
  );
};

// ─────────────────────────────────────────────────────────────
// 3. Name — "what should we call you?"
// ─────────────────────────────────────────────────────────────
const NameScreen = ({ auth, onContinue, onBack }) => {
  const [name, setName] = React.useState('');
  const [submitting, setSubmitting] = React.useState(false);

  const submit = async () => {
    if (!name.trim()) return;
    setSubmitting(true);
    const ok = await auth.setName(name.trim());
    setSubmitting(false);
    if (ok) onContinue();
  };

  return (
    <Screen padTop={64} padBottom={32} style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0 24px', marginBottom: 32 }}>
        <button onClick={onBack} className="press" style={{
          width: 40, height: 40, borderRadius: 9999, background: 'var(--surface-1)',
          border: '1px solid var(--hairline)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="arrow-left" size={18} /></button>
      </div>

      <div style={{ flex: 1, padding: '0 24px' }}>
        <div className="fade-up">
          <h1 style={{
            fontSize: 30, lineHeight: 1.15, fontWeight: 600, letterSpacing: -0.7,
            margin: 0, marginBottom: 10,
          }}>What should we call you?</h1>
          <p style={{ fontSize: 14, color: 'var(--text-2)', margin: 0, marginBottom: 32 }}>
            Just a first name is fine — we'll use it on the glasses too.
          </p>

          <label style={{
            display: 'block', fontSize: 11, color: 'var(--text-3)', marginBottom: 8,
            letterSpacing: 0.4, textTransform: 'uppercase', fontWeight: 600,
          }}>First name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
            placeholder="Alex"
            style={{
              width: '100%', height: 60, padding: '0 18px', borderRadius: 16,
              background: 'var(--surface-1)', border: '1px solid var(--hairline)',
              color: 'var(--text-1)', fontSize: 18, fontFamily: 'var(--font-sans)', fontWeight: 500,
              outline: 'none',
            }}
          />

          <Card padding={16} style={{ marginTop: 24, display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10, background: 'var(--accent-soft)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Icon name="bolt" size={18} stroke="var(--accent)" />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>Quick setup</div>
              <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>
                Next, we'll pair your glasses. Takes about 30 seconds.
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div style={{ padding: '24px 24px 0' }}>
        <Button onClick={submit} iconRight="arrow-right" disabled={!name.trim() || submitting}>
          {submitting ? 'Saving…' : 'Continue'}
        </Button>
      </div>
    </Screen>
  );
};

// ─────────────────────────────────────────────────────────────
// 4. Done — placeholder so the flow has somewhere to land. Real
//    next step is glasses pairing, owned by a different ticket.
// ─────────────────────────────────────────────────────────────
const DoneScreen = ({ auth, onAddProgram, onRestart }) => (
  <Screen padTop={0} padBottom={0} style={{ display: 'flex', flexDirection: 'column' }}>
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: '0 32px',
      textAlign: 'center',
    }}>
      <div style={{
        width: 88, height: 88, borderRadius: '50%',
        background: 'var(--accent)', display: 'flex',
        alignItems: 'center', justifyContent: 'center', marginBottom: 28,
        boxShadow: '0 0 60px rgba(197,242,62,0.4)',
      }}>
        <Icon name="check" size={44} stroke="var(--on-accent)" strokeWidth={2.5} />
      </div>
      <h1 style={{ fontSize: 30, fontWeight: 600, letterSpacing: -0.7, margin: 0, marginBottom: 12 }}>
        You're in{auth.user && auth.user.name ? `, ${auth.user.name}` : ''}.
      </h1>
      <p style={{ fontSize: 14, color: 'var(--text-2)', margin: 0, maxWidth: 280 }}>
        Add your first program to get going. The home screen comes later.
      </p>
    </div>
    <div style={{ padding: '0 24px 40px', display: 'flex', flexDirection: 'column', gap: 10 }}>
      <Button onClick={onAddProgram} iconRight="arrow-right">Add a program</Button>
      <Button variant="ghost" onClick={onRestart}>Restart flow</Button>
    </div>
  </Screen>
);

// ─────────────────────────────────────────────────────────────
// 4. Pair glasses — placeholder.
//
// We don't actually talk to glasses yet. The whole screen is fake-timer
// driven so the visual flow matches the design. When a real bluetooth/
// pairing layer exists, swap the setTimeout calls for real callbacks.
// ─────────────────────────────────────────────────────────────
const PairScreen = ({ onContinue, onSkip, onBack }) => {
  const [phase, setPhase] = React.useState('searching'); // searching → found → connected

  // Pretend to scan for glasses, then "discover" one.
  React.useEffect(() => {
    const t = setTimeout(() => setPhase('found'), 1600);
    return () => clearTimeout(t);
  }, []);

  const pair = () => {
    setPhase('connected');
    if (window.pairDemoDevice) {
      window.pairDemoDevice().catch((err) => console.error('Could not save paired device:', err));
    }
    setTimeout(onContinue, 1100);
  };

  const connected = phase === 'connected';

  return (
    <Screen padTop={64} padBottom={32} style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0 24px' }}>
        <button onClick={onBack} className="press" style={{
          width: 40, height: 40, borderRadius: 9999, background: 'var(--surface-1)',
          border: '1px solid var(--hairline)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
          marginBottom: 24,
        }}><Icon name="arrow-left" size={18} /></button>

        <h1 style={{
          fontSize: 28, lineHeight: 1.15, fontWeight: 600, letterSpacing: -0.6,
          margin: 0, marginBottom: 10,
        }}>Pair your glasses</h1>
        <p style={{ fontSize: 14, color: 'var(--text-2)', margin: 0, marginBottom: 32 }}>
          Make sure your glasses are powered on and within 3 feet.
        </p>
      </div>

      {/* Big concentric indicator. */}
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        position: 'relative',
      }}>
        <div style={{
          width: 240, height: 240, borderRadius: '50%',
          border: '1px solid ' + (connected ? 'var(--accent)' : 'var(--hairline-2)'),
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          position: 'relative',
          boxShadow: connected ? '0 0 80px rgba(197,242,62,0.5)' : 'none',
          transition: 'all 600ms',
        }}>
          {phase === 'searching' && (
            <div className="spin-ring" style={{
              position: 'absolute', inset: -1, borderRadius: '50%',
              border: '2px solid transparent', borderTopColor: 'var(--accent)',
            }} />
          )}
          <div style={{
            width: 130, height: 130, borderRadius: '50%',
            background: connected ? 'var(--accent)' : 'var(--surface-1)',
            border: '1px solid ' + (connected ? 'var(--accent)' : 'var(--hairline)'),
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 400ms',
          }}>
            {connected
              ? <Icon name="check"   size={56} stroke="var(--on-accent)" strokeWidth={2.5} />
              : <Icon name="glasses" size={56} stroke="var(--text-1)"   strokeWidth={1.5} />}
          </div>
        </div>
      </div>

      <div style={{ padding: '0 24px 0', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {phase === 'searching' && (
          <Card style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className="pulse-dot" style={{
              width: 8, height: 8, borderRadius: 4, background: 'var(--accent)',
            }} />
            <div style={{ fontSize: 14, color: 'var(--text-2)' }}>Searching for nearby glasses…</div>
          </Card>
        )}

        {phase === 'found' && (
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{
                width: 44, height: 44, borderRadius: 12, background: 'var(--surface-2)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Icon name="glasses" size={22} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 15, fontWeight: 600 }}>TrainAR · M2</div>
                <div style={{
                  fontSize: 11, color: 'var(--text-3)', marginTop: 2,
                  fontFamily: 'var(--font-mono)',
                }}>SN · 8E40·B7C2 · -54 dBm</div>
              </div>
              <Button size="sm" onClick={pair} style={{ width: 'auto' }}>Pair</Button>
            </div>
          </Card>
        )}

        {connected && (
          <Card style={{
            background: 'var(--accent-soft)', border: '1px solid rgba(197,242,62,0.3)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <Icon name="check" size={20} stroke="var(--accent)" strokeWidth={2.5} />
              <div style={{ fontSize: 14, color: 'var(--accent)', fontWeight: 600 }}>
                Paired — finishing setup…
              </div>
            </div>
          </Card>
        )}

        <button onClick={onSkip} className="press" style={{
          background: 'transparent', border: 'none', color: 'var(--text-2)',
          fontSize: 13, padding: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        }}>I'll do this later</button>
      </div>
    </Screen>
  );
};

Object.assign(window, { Screen, SplashScreen, AuthScreen, NameScreen, PairScreen, DoneScreen });
