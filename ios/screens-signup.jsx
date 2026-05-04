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
    width: '100%', height: '100%', background: 'var(--bg)',
    paddingTop: padTop, paddingBottom: padBottom,
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

Object.assign(window, { Screen, SplashScreen, AuthScreen });
