// Main app screens: Home (Train tab) + the post-workout PastWorkout view.
// History (calendar) and Profile come on their own branches.

// ─────────────────────────────────────────────────────────────
// HOME — Train tab
//
// Two states:
//   * idle               — Add program CTA on top, "Your programs" feed below
//                          (each row has a round green glasses button to send
//                          to glasses)
//   * loadedToGlasses    — hero card for the active program with a Finish
//                          workout button. Other programs dim out.
//
// Data: window.PROGRAMS + window.PROGRAM_DETAIL.
// ─────────────────────────────────────────────────────────────
const HomeScreen = ({
  onAddProgram,
  onOpenProgram,
  onActivate,
  onFinish,
  glassesConnected = true,
  loadedToGlasses = false,
  activeProgramId = null,
}) => {
  const programs  = window.PROGRAMS || [];
  const loadedProgram = activeProgramId
    ? programs.find((program) => program.id === activeProgramId)
    : programs[0];
  const detail = activeProgramId && window.getProgramDetail
    ? (window.getProgramDetail(activeProgramId) || window.PROGRAM_DETAIL || { exercises: [] })
    : (window.PROGRAM_DETAIL || { exercises: [] });
  const exercises = detail.exercises || [];
  const loaded    = loadedToGlasses ? loadedProgram : null;
  const rest      = loadedToGlasses ? programs.filter((program) => program.id !== loaded?.id) : programs;

  return (
    <Screen padTop={56} padBottom={120}>
      {/* Header — title + glasses pill */}
      <div style={{
        padding: '0 20px 18px',
        display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between',
      }}>
        <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: -0.5 }}>Train</div>
        <GlassesPill connected={glassesConnected} battery={78} />
      </div>

      {/* Add program CTA — disabled while a workout is active. */}
      <div style={{ padding: '0 20px 16px' }}>
        <button
          onClick={loadedToGlasses ? undefined : onAddProgram}
          disabled={loadedToGlasses}
          className={loadedToGlasses ? '' : 'press'}
          style={{
            width: '100%', padding: '16px 18px', borderRadius: 'var(--r-card)',
            background: loadedToGlasses ? 'var(--surface-1)' : 'var(--accent)',
            border: loadedToGlasses ? '1px solid var(--hairline)' : 'none',
            color: loadedToGlasses ? 'var(--text-3)' : 'var(--on-accent)',
            textAlign: 'left',
            cursor: loadedToGlasses ? 'not-allowed' : 'pointer',
            opacity: loadedToGlasses ? 0.7 : 1,
            fontFamily: 'var(--font-sans)',
            display: 'flex', alignItems: 'center', gap: 12,
          }}
        >
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: loadedToGlasses ? 'var(--overlay-1)' : 'rgba(0,0,0,0.12)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <Icon
              name="plus" size={20}
              stroke={loadedToGlasses ? 'var(--text-3)' : 'var(--on-accent)'}
              strokeWidth={2.6}
            />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: -0.2 }}>Add program</div>
            <div style={{ fontSize: 11, opacity: 0.75, marginTop: 1 }}>Photo, PDF, or template</div>
          </div>
        </button>
      </div>

      {/* Loaded-to-glasses hero — only when active. */}
      {loaded && (
        <div style={{ padding: '0 20px 18px' }}>
          <div onClick={onOpenProgram} className="press" style={{
            background: 'var(--hero-bg)',
            border: '1px solid var(--accent)',
            borderRadius: 'var(--r-card-lg)', padding: 20, cursor: 'pointer',
            position: 'relative', overflow: 'hidden',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <Pill accent>
                <span style={{
                  display: 'inline-block', width: 6, height: 6, borderRadius: '50%',
                  background: 'var(--accent)', marginRight: 6,
                  boxShadow: '0 0 6px var(--accent)',
                }} />
                Workout in progress
              </Pill>
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-3)', marginBottom: 4 }}>Active program</div>
            <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: -0.6, marginBottom: 4 }}>
              {loaded.name}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 18 }}>
              {loaded.type} · {exercises.length} exercises
            </div>

            {/* First few exercise chips, plus a "+N more" tail. */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 18 }}>
              {exercises.slice(0, 3).map((ex, i) => (
                <div key={i} style={{
                  fontSize: 11, padding: '6px 10px', borderRadius: 9999,
                  background: 'var(--overlay-1)', color: 'var(--text-2)',
                  border: '1px solid var(--hairline)',
                }}>{ex.name.replace(' (Top Single)', '')}</div>
              ))}
              {exercises.length > 3 && (
                <div style={{
                  fontSize: 11, padding: '6px 10px', borderRadius: 9999,
                  background: 'var(--overlay-1)', color: 'var(--text-3)',
                  border: '1px solid var(--hairline)',
                }}>+{exercises.length - 3} more</div>
              )}
            </div>

            <Button
              onClick={(e) => { e.stopPropagation(); onFinish && onFinish(); }}
              icon="check"
              variant="surface"
              style={{
                background: 'var(--surface-2)', color: 'var(--text-1)',
                border: '1px solid var(--accent)',
              }}
            >
              Finish workout
            </Button>
          </div>
        </div>
      )}

      {/* Programs feed — title row. */}
      <div style={{ padding: '0 20px' }}>
        {!loadedToGlasses && (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            marginBottom: 12, padding: '0 4px',
          }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-2)' }}>Your programs</span>
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>
              {programs.length} SAVED
            </span>
          </div>
        )}
        {loadedToGlasses && rest.length > 0 && (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            marginBottom: 12, padding: '0 4px',
          }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-2)' }}>Other programs</span>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {rest.map((p) => (
            <div
              key={p.id}
              onClick={loadedToGlasses ? undefined : (() => onOpenProgram && onOpenProgram(p.id))}
              className={loadedToGlasses ? '' : 'press'}
              style={{
                padding: 16, borderRadius: 'var(--r-card)',
                background: 'var(--surface-1)', border: '1px solid var(--hairline)',
                cursor: loadedToGlasses ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: 14,
                opacity: loadedToGlasses ? 0.4 : 1,
                pointerEvents: loadedToGlasses ? 'none' : 'auto',
              }}
            >
              <div style={{
                width: 48, height: 48, borderRadius: 14,
                background: 'var(--surface-2)', border: '1px solid var(--hairline)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                <div style={{ width: 10, height: 10, borderRadius: 3, background: p.color }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: -0.2 }}>{p.name}</div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (!loadedToGlasses) onActivate && onActivate(p.id);
                }}
                disabled={loadedToGlasses}
                className={loadedToGlasses ? '' : 'press'}
                aria-label="Send to glasses"
                style={{
                  width: 44, height: 44, borderRadius: '50%',
                  background: 'var(--accent)', border: 'none',
                  color: 'var(--on-accent)',
                  cursor: loadedToGlasses ? 'not-allowed' : 'pointer',
                  flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                <Icon name="glasses" size={20} stroke="var(--on-accent)" strokeWidth={2.2} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </Screen>
  );
};

Object.assign(window, { HomeScreen });
