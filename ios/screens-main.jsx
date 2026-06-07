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
  glassesBattery = 78,
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
        <GlassesPill connected={glassesConnected} battery={glassesBattery || 78} />
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
              icon="trophy"
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

// ─────────────────────────────────────────────────────────────
// LIVE WORKOUT TRACKER — while a workout is active, makes it clear
// which exercise + which set you're on. The clean WORKOUT/SETS/REPS/
// WEIGHT table matches the inactive program view; the active lift gets
// a hero row + per-set breakdown, finished work reads as done, and the
// coach's weight edits can flash on the real plan (overrides/flashKey).
// ─────────────────────────────────────────────────────────────
const LiveWorkoutList = ({ exercises, pos, overrides = {}, flashKey = null }) => {
  const COLS = '1.6fr 36px 44px 56px 16px';
  const Th = ({ children, right }) => (
    <div className="mono" style={{ fontSize: 9, color: 'var(--text-3)', letterSpacing: 0.6, textTransform: 'uppercase', textAlign: right ? 'right' : 'left' }}>{children}</div>
  );
  return (
    <Card padding={0}>
      {/* Column header — identical to the inactive inspect view. */}
      <div style={{ display: 'grid', gridTemplateColumns: COLS, gap: 8, alignItems: 'center', padding: '10px 14px', borderBottom: '1px solid var(--hairline)' }}>
        <Th>Workout</Th><Th right>Sets</Th><Th right>Reps</Th><Th right>Weight</Th><div />
      </div>

      {exercises.map((ex, i) => {
        const isActive = i === pos.ex;
        const isDone = i < pos.ex;
        const last = i === exercises.length - 1;
        const rowBorder = last ? 'none' : '1px solid var(--hairline)';

        // ── ACTIVE — summary row + per-set tracker, kept inside the table ──
        if (isActive) {
          const liveLoad = overrides[i + '-' + pos.set] || ex.load;
          return (
            <div key={i} className="fade-up" style={{
              borderBottom: rowBorder,
              background: 'var(--hero-bg)',
              boxShadow: 'inset 2px 0 0 var(--accent)',
            }}>
              {/* Summary row */}
              <div style={{ display: 'grid', gridTemplateColumns: COLS, gap: 8, alignItems: 'center', padding: '12px 14px' }}>
                <div style={{ minWidth: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="pulse-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', flexShrink: 0 }} />
                  <div style={{ minWidth: 0 }}>
                    <div className="mono" style={{ fontSize: 8.5, letterSpacing: 0.7, color: 'var(--accent)', lineHeight: 1 }}>NOW LIFTING</div>
                    <div style={{ fontSize: 13, fontWeight: 600, letterSpacing: -0.1, lineHeight: 1.3, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ex.name}</div>
                  </div>
                </div>
                <div className="mono" style={{ fontSize: 12, textAlign: 'right', fontWeight: 700, color: 'var(--text-1)' }}>{pos.set + 1}<span style={{ color: 'var(--text-3)', fontWeight: 400 }}>/{ex.sets}</span></div>
                <div className="mono" style={{ fontSize: 12, color: 'var(--text-2)', textAlign: 'right' }}>{ex.reps}</div>
                <div className="mono" style={{ fontSize: 12, color: 'var(--accent)', textAlign: 'right', fontWeight: 600 }}>{liveLoad}</div>
                <div />
              </div>

              {/* Per-set rows — aligned to the same columns */}
              {Array.from({ length: ex.sets }).map((_, sIdx) => {
                const sDone = sIdx < pos.set;
                const sCurrent = sIdx === pos.set;
                const key = i + '-' + sIdx;
                const load = overrides[key] || ex.load;
                const flashing = flashKey === key;
                return (
                  <div key={sIdx} style={{
                    display: 'grid', gridTemplateColumns: COLS, gap: 8, alignItems: 'center',
                    padding: '9px 14px',
                    borderTop: '1px solid var(--hairline)',
                    background: sCurrent ? 'var(--accent-soft)' : 'transparent',
                    opacity: sDone ? 0.5 : 1,
                    transition: 'background 200ms, opacity 200ms',
                  }}>
                    <div style={{ minWidth: 0, display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 14 }}>
                      <span style={{
                        width: 16, height: 16, borderRadius: 5, flexShrink: 0,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: sDone ? 'transparent' : sCurrent ? 'var(--accent)' : 'var(--surface-3)',
                      }}>
                        {sDone
                          ? <Icon name="check" size={11} stroke="var(--accent)" strokeWidth={2.5} />
                          : <span className="mono" style={{ fontSize: 9.5, fontWeight: 700, color: sCurrent ? 'var(--on-accent)' : 'var(--text-2)' }}>{sIdx + 1}</span>}
                      </span>
                      <span className="mono" style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-1)' }}>{'Set ' + (sIdx + 1)}</span>
                      {sCurrent && (
                        <span className="mono" style={{ fontSize: 8, fontWeight: 700, letterSpacing: 0.6, color: 'var(--accent)' }}>TRACKING</span>
                      )}
                    </div>
                    <div />
                    <div className={'mono' + (flashing ? ' cell-flash' : '')} style={{ fontSize: 12, textAlign: 'right', color: 'var(--text-2)' }}>{ex.reps}</div>
                    <div className={'mono' + (flashing ? ' cell-flash' : '')} style={{ fontSize: 12, textAlign: 'right', fontWeight: 600, color: 'var(--accent)' }}>{load}</div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      {sDone && <Icon name="check" size={12} stroke="var(--text-3)" strokeWidth={2.5} />}
                    </div>
                  </div>
                );
              })}

              {ex.note && (
                <div style={{ padding: '10px 14px 12px 28px', borderTop: '1px solid var(--hairline)' }}>
                  <div className="mono" style={{ fontSize: 9, color: 'var(--text-3)', letterSpacing: 0.5, textTransform: 'uppercase', marginBottom: 4 }}>Notes</div>
                  <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.45 }}>{ex.note}</div>
                </div>
              )}
            </div>
          );
        }

        // ── DONE / UPCOMING — single clean row, same as inspect ──
        return (
          <div key={i} style={{
            display: 'grid', gridTemplateColumns: COLS, gap: 8, alignItems: 'center',
            padding: '13px 14px', borderBottom: rowBorder,
            opacity: isDone ? 0.45 : 1,
          }}>
            <div style={{ minWidth: 0, display: 'flex', alignItems: 'center', gap: 7 }}>
              {isDone && <Icon name="check" size={13} stroke="var(--accent)" strokeWidth={2.5} style={{ flexShrink: 0 }} />}
              <div style={{ fontSize: 13, fontWeight: 500, letterSpacing: -0.1, lineHeight: 1.25, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: isDone ? 'var(--text-2)' : 'var(--text-1)' }}>{ex.name}</div>
            </div>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-2)', textAlign: 'right' }}>{ex.sets}</div>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-2)', textAlign: 'right' }}>{ex.reps}</div>
            <div className="mono" style={{ fontSize: 12, color: isDone ? 'var(--text-3)' : 'var(--accent)', textAlign: 'right', fontWeight: 600 }}>{ex.load}</div>
            <div />
          </div>
        );
      })}
    </Card>
  );
};

const RunningWorkoutScreen = ({
  programId,
  sessionId,
  day,
  step,
  lastLoggedSet,
  rest,
  onClose,
  onOpenHud,
  onFinish,
  onNextSet,
  onSkipExercise,
}) => {
  const program = (window.PROGRAMS || []).find((item) => item.id === programId) || (window.PROGRAMS || [])[0] || {};
  const detail = programId && window.getProgramDetail
    ? (window.getProgramDetail(programId) || window.PROGRAM_DETAIL || { exercises: [] })
    : (window.PROGRAM_DETAIL || { exercises: [] });
  const selectedDay = day?.id
    ? (detail.days || []).find((item) => item.id === day.id) || day
    : (day || (detail.days || [])[0] || null);
  const rawExercises = selectedDay?.blocks?.length
    ? selectedDay.blocks.flatMap((block) => block.exercises || [])
    : (detail.exercises || []);
  // The live tracker draws one row per set, so coerce whatever the backend
  // stored for the count ("5", "5×3", "-") into a concrete number.
  const exercises = rawExercises.map((exercise) => ({
    ...exercise,
    sets: Number.parseInt(exercise.sets, 10) || 1,
  }));
  const currentName = step?.exerciseName || exercises[0]?.name || '';
  const currentIndex = Math.max(0, exercises.findIndex((exercise) => normalizeRunningName(exercise.name) === normalizeRunningName(currentName)));
  const setNumber = Number.parseInt(step?.setNumber, 10) || 1;
  // step goes null once the final set is logged → the whole workout is done.
  const allDone = !step || currentIndex >= exercises.length;
  const pos = allDone
    ? { ex: exercises.length, set: 0 }
    : { ex: currentIndex, set: Math.max(0, setNumber - 1) };

  return (
    <Screen padTop={58} padBottom={132}>
      {/* Header — collapse + HUD demo + live status */}
      <div style={{
        padding: '0 20px 16px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <button onClick={onClose} className="press" style={{
          width: 38, height: 38, borderRadius: 9999,
          background: 'var(--surface-1)', border: '1px solid var(--hairline)',
          color: 'var(--text-1)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon name="chevron-down" size={18} />
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={onOpenHud} className="press" aria-label="HUD demo" title="HUD demo" style={{
            width: 38, height: 38, borderRadius: 9999,
            background: 'var(--surface-1)', border: '1px solid var(--hairline)',
            color: 'var(--text-2)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Icon name="video" size={16} />
          </button>
          <Pill accent>
            <span style={{
              display: 'inline-block', width: 6, height: 6, borderRadius: '50%',
              background: 'var(--accent)', marginRight: 6, boxShadow: '0 0 6px var(--accent)',
            }} />
            Live workout
          </Pill>
        </div>
      </div>

      {/* Title — the program; the active lift is distinguished in the table. */}
      <div style={{ padding: '0 20px 18px' }}>
        <h1 style={{ fontSize: 30, lineHeight: 1.1, fontWeight: 600, letterSpacing: -0.6, margin: 0, marginBottom: 8 }}>
          {program.name || 'Workout'}
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, lineHeight: 1.5 }}>
          {allDone
            ? 'Every set logged — finish when you are ready.'
            : 'Working through your sets — your glasses track each rep automatically.'}
          {selectedDay?.title ? ` · ${selectedDay.title}` : ''}
        </p>
      </div>

      {/* Clean table — matches the inactive program; the current lift + set
          are highlighted, finished work reads as done. */}
      <div style={{ padding: '0 20px' }}>
        <LiveWorkoutList exercises={exercises} pos={pos} />
      </div>

      {/* Bottom controls — two round FABs, single height, bottom-right.
          Log set (check) advances the tracker; the trophy stays grey
          (tappable to finish early) until every set is logged, then turns
          accent-green — at which point only it remains. */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        padding: '16px 20px 24px',
        background: 'linear-gradient(180deg, transparent, var(--bg) 30%)',
        display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 12,
        pointerEvents: 'none',
      }}>
        {!allDone && (
          <button onClick={onNextSet} className="press" aria-label="Log set" title="Log set" style={{
            pointerEvents: 'auto',
            width: 58, height: 58, borderRadius: 9999,
            background: 'var(--accent)', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 6px 16px rgba(0,0,0,0.35)',
          }}>
            <Icon name="check" size={24} stroke="var(--on-accent)" strokeWidth={2.4} />
          </button>
        )}
        <button onClick={() => onFinish && onFinish(sessionId, programId)} className="press" aria-label={allDone ? 'Finish workout' : 'Finish early'} title={allDone ? 'Finish workout' : 'Finish early'} style={{
          pointerEvents: 'auto',
          width: 58, height: 58, borderRadius: 9999, cursor: 'pointer',
          background: allDone ? 'var(--accent)' : 'var(--surface-2)',
          border: allDone ? 'none' : '1px solid var(--hairline-2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: allDone ? '0 6px 18px rgba(0,0,0,0.35), var(--accent-glow)' : '0 4px 12px rgba(0,0,0,0.30)',
          transition: 'background 260ms ease, box-shadow 260ms ease, border-color 260ms ease',
        }}>
          <Icon name="trophy" size={24} stroke={allDone ? 'var(--on-accent)' : 'var(--text-3)'} strokeWidth={2} />
        </button>
      </div>
    </Screen>
  );
};

function normalizeRunningName(value) {
  return String(value || '').toLowerCase().replace(/\s+/g, ' ').trim();
}

Object.assign(window, { HomeScreen, RunningWorkoutScreen });
