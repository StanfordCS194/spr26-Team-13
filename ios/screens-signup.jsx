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
                Next, we will tune your training profile.
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
// 4. Training profile - required lightweight personalization.
// ─────────────────────────────────────────────────────────────
const TrainingProfileScreen = ({ auth, onContinue, onBack }) => {
  const existing = auth.user?.trainingProfile || {};
  const [goal, setGoal] = React.useState(existing.trainingGoal || 'strength');
  const [experience, setExperience] = React.useState(existing.trainingExperience || 'beginner');
  const [days, setDays] = React.useState(existing.workoutDaysPerWeek || 3);
  const [minutes, setMinutes] = React.useState(existing.workoutSessionMinutes || 45);
  const [equipment, setEquipment] = React.useState(existing.availableEquipment?.length ? existing.availableEquipment : ['gym']);
  const [coachStyle, setCoachStyle] = React.useState(existing.coachStyle || 'direct');
  const [evidencePreference, setEvidencePreference] = React.useState(existing.evidencePreference || 'concise');
  const [submitting, setSubmitting] = React.useState(false);

  const toggleEquipment = (value) => {
    setEquipment((current) => {
      if (current.includes(value)) return current.filter((item) => item !== value);
      return [...current, value];
    });
  };

  const submit = async () => {
    if (!goal || !experience || !days || !minutes || !equipment.length) return;
    setSubmitting(true);
    const ok = await auth.setTrainingProfile({
      trainingGoal: goal,
      trainingExperience: experience,
      workoutDaysPerWeek: days,
      workoutSessionMinutes: minutes,
      availableEquipment: equipment,
      coachStyle,
      evidencePreference,
      movementConstraints: existing.movementConstraints || '',
    });
    setSubmitting(false);
    if (ok) onContinue();
  };

  return (
    <Screen padTop={56} padBottom={28} style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0 24px 18px' }}>
        <button onClick={onBack} className="press" style={{
          width: 40, height: 40, borderRadius: 9999, background: 'var(--surface-1)',
          border: '1px solid var(--hairline)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
          marginBottom: 22,
        }}><Icon name="arrow-left" size={18} /></button>

        <h1 style={{
          fontSize: 29, lineHeight: 1.12, fontWeight: 600, letterSpacing: -0.7,
          margin: 0, marginBottom: 9,
        }}>Tune your coach</h1>
        <p style={{ fontSize: 14, color: 'var(--text-2)', lineHeight: 1.45, margin: 0 }}>
          These basics shape your first plans and coach answers.
        </p>
      </div>

      <div className="no-scrollbar" style={{
        flex: 1, overflowY: 'auto', padding: '0 24px 16px',
        display: 'flex', flexDirection: 'column', gap: 18,
      }}>
        <ChoiceGroup
          title="Goal"
          value={goal}
          onChange={setGoal}
          options={[
            ['strength', 'Strength'],
            ['hypertrophy', 'Muscle'],
            ['fat_loss', 'Fat loss'],
            ['general_fitness', 'Fitness'],
          ]}
        />

        <ChoiceGroup
          title="Experience"
          value={experience}
          onChange={setExperience}
          options={[
            ['beginner', 'Beginner'],
            ['intermediate', 'Intermediate'],
            ['advanced', 'Advanced'],
          ]}
        />

        <StepperRow
          title="Weekly workouts"
          value={days}
          min={1}
          max={7}
          suffix="days"
          onChange={setDays}
        />

        <StepperRow
          title="Session length"
          value={minutes}
          min={20}
          max={120}
          step={15}
          suffix="min"
          onChange={setMinutes}
        />

        <MultiChoiceGroup
          title="Equipment"
          values={equipment}
          onToggle={toggleEquipment}
          options={[
            ['bodyweight', 'Bodyweight'],
            ['dumbbells', 'Dumbbells'],
            ['barbell', 'Barbell'],
            ['machines', 'Machines'],
            ['bands', 'Bands'],
            ['gym', 'Full gym'],
          ]}
        />

        <ChoiceGroup
          title="Coach style"
          value={coachStyle}
          onChange={setCoachStyle}
          options={[
            ['direct', 'Direct'],
            ['encouraging', 'Encouraging'],
            ['analytical', 'Analytical'],
            ['high_energy', 'High energy'],
          ]}
        />

        <ChoiceGroup
          title="Evidence"
          value={evidencePreference}
          onChange={setEvidencePreference}
          options={[
            ['minimal', 'Minimal'],
            ['concise', 'Concise'],
            ['detailed', 'Detailed'],
          ]}
        />

        {auth.error && (
          <div style={{ color: '#FF8B7C', fontSize: 13, padding: '0 4px' }}>{auth.error}</div>
        )}
      </div>

      <div style={{ padding: '0 24px' }}>
        <Button onClick={submit} iconRight="arrow-right" disabled={submitting || !equipment.length}>
          {submitting ? 'Saving...' : 'Continue'}
        </Button>
      </div>
    </Screen>
  );
};

const ChoiceGroup = ({ title, value, options, onChange }) => (
  <div>
    <div style={{
      fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase',
      letterSpacing: 0.4, fontWeight: 700, marginBottom: 9,
    }}>{title}</div>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {options.map(([id, label]) => (
        <button
          key={id}
          onClick={() => onChange(id)}
          className="press"
          style={choiceButtonStyle(value === id)}
        >{label}</button>
      ))}
    </div>
  </div>
);

const MultiChoiceGroup = ({ title, values, options, onToggle }) => (
  <div>
    <div style={{
      fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase',
      letterSpacing: 0.4, fontWeight: 700, marginBottom: 9,
    }}>{title}</div>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {options.map(([id, label]) => (
        <button
          key={id}
          onClick={() => onToggle(id)}
          className="press"
          style={choiceButtonStyle(values.includes(id))}
        >{label}</button>
      ))}
    </div>
  </div>
);

const StepperRow = ({ title, value, min, max, step = 1, suffix, onChange }) => (
  <div style={{
    minHeight: 58, borderRadius: 16, background: 'var(--surface-1)',
    border: '1px solid var(--hairline)', padding: '0 14px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
  }}>
    <div>
      <div style={{ fontSize: 13, fontWeight: 700 }}>{title}</div>
      <div className="mono" style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 3 }}>
        {value} {suffix}
      </div>
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <button
        onClick={() => onChange(Math.max(min, Number(value) - step))}
        className="press"
        style={stepperButtonStyle}
        aria-label={`Decrease ${title}`}
      ><Icon name="minus" size={16} /></button>
      <button
        onClick={() => onChange(Math.min(max, Number(value) + step))}
        className="press"
        style={stepperButtonStyle}
        aria-label={`Increase ${title}`}
      ><Icon name="plus" size={16} /></button>
    </div>
  </div>
);

const choiceButtonStyle = (selected) => ({
  minHeight: 38,
  padding: '0 13px',
  borderRadius: 9999,
  border: selected ? '1px solid rgba(197,242,62,0.55)' : '1px solid var(--hairline)',
  background: selected ? 'var(--accent-soft)' : 'var(--surface-1)',
  color: selected ? 'var(--accent)' : 'var(--text-2)',
  fontFamily: 'var(--font-sans)',
  fontSize: 13,
  fontWeight: 700,
  cursor: 'pointer',
});

const stepperButtonStyle = {
  width: 34,
  height: 34,
  borderRadius: 9999,
  border: '1px solid var(--hairline)',
  background: 'var(--surface-2)',
  color: 'var(--text-1)',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  cursor: 'pointer',
};

// ─────────────────────────────────────────────────────────────
// 5. Done — placeholder so the flow has somewhere to land.
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

Object.assign(window, { Screen, SplashScreen, AuthScreen, NameScreen, TrainingProfileScreen, DoneScreen });
