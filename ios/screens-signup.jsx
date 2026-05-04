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

Object.assign(window, { Screen, SplashScreen });
