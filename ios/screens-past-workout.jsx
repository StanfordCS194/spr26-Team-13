// Past workout summary — what you see right after finishing a workout
// or when tapping a previous session from the calendar / history tab.
// Reads from window.PAST_WORKOUT.

const PastWorkoutScreen = ({ workout, onBack }) => {
  const w = workout || window.PAST_WORKOUT || {};

  return (
    <Screen padTop={56} padBottom={40}>
      {/* Top chrome — back + Export. */}
      <div style={{
        padding: '0 20px 18px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <button onClick={onBack} className="press" style={{
          width: 36, height: 36, borderRadius: 9999,
          background: 'var(--surface-1)', border: '1px solid var(--hairline)',
          color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="arrow-left" size={16} /></button>
        <button className="press" style={{
          height: 36, padding: '0 14px', borderRadius: 9999,
          background: 'var(--surface-1)', border: '1px solid var(--hairline)',
          color: 'var(--text-1)', cursor: 'pointer', fontSize: 12, fontWeight: 600,
          fontFamily: 'var(--font-sans)',
          display: 'flex', alignItems: 'center', gap: 6,
        }}><Icon name="upload" size={14} /> Export</button>
      </div>

      {/* Title + auto-tracked badge. */}
      <div style={{ padding: '0 20px 18px' }}>
        <div className="mono" style={{
          fontSize: 11, color: 'var(--text-3)', marginBottom: 4, letterSpacing: 0.5,
        }}>{(w.date || '').toUpperCase()}</div>
        <h1 style={{
          fontSize: 28, fontWeight: 600, letterSpacing: -0.6, margin: 0, marginBottom: 10,
        }}>{w.name || 'Workout'}</h1>
        {typeof w.autoTracked === 'number' && (
          <Pill accent>
            <Icon name="bolt" size={11} stroke="var(--accent)" />
            {Math.round(w.autoTracked * 100)}% auto-tracked
          </Pill>
        )}
      </div>

      {/* Volume hero. */}
      <div style={{ padding: '0 20px 14px' }}>
        <Card style={{ background: 'var(--hero-bg)', border: '1px solid var(--hero-border)' }}>
          <div className="mono" style={{
            fontSize: 11, color: 'var(--accent)',
            textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6,
          }}>Total volume</div>
          <div className="mono" style={{
            fontSize: 44, fontWeight: 600, letterSpacing: -1.5, lineHeight: 1, color: 'var(--text-1)',
          }}>{w.totalVolume || '—'}</div>
          <div style={{
            display: 'flex', gap: 14, marginTop: 18, paddingTop: 14,
            borderTop: '1px solid rgba(197,242,62,0.12)',
          }}>
            {[
              { l: 'Duration', v: w.duration || '—' },
              { l: 'Sets',     v: w.sets ?? '—'    },
              { l: 'Avg RPE',  v: w.rpe ?? '—'     },
            ].map((s, i) => (
              <div key={i} style={{ flex: 1 }}>
                <div className="mono" style={{ fontSize: 16, fontWeight: 600 }}>{s.v}</div>
                <div style={{
                  fontSize: 10, color: 'var(--text-3)', marginTop: 2,
                  textTransform: 'uppercase', letterSpacing: 0.5,
                }}>{s.l}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* PRs — only if any. */}
      {Array.isArray(w.prs) && w.prs.length > 0 && (
        <div style={{ padding: '0 20px 14px' }}>
          <Card padding={16} style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 10, background: 'var(--accent-soft)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Icon name="trophy" size={18} stroke="var(--accent)" />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{
                fontSize: 11, color: 'var(--accent)',
                textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600, marginBottom: 2,
              }}>New PR</div>
              <div style={{ fontSize: 13, color: 'var(--text-1)', lineHeight: 1.4 }}>{w.prs[0]}</div>
            </div>
          </Card>
        </div>
      )}

      {/* Set-by-set breakdown. */}
      <div style={{ padding: '0 20px' }}>
        <div style={{
          fontSize: 13, fontWeight: 600, color: 'var(--text-2)',
          marginBottom: 10, padding: '0 4px',
        }}>Set by set</div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {(w.exercises || []).map((ex, i) => (
            <div key={i} style={{
              background: 'var(--surface-1)', border: '1px solid var(--hairline)',
              borderRadius: 16, padding: '14px 16px',
            }}>
              <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 10 }}>{ex.name}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {(ex.sets || []).map((s, j) => (
                  <div key={j} style={{
                    display: 'grid', gridTemplateColumns: '24px 1fr 1fr 1fr 16px',
                    alignItems: 'center', gap: 8,
                    padding: '6px 0', fontSize: 12,
                  }}>
                    <div className="mono" style={{ color: 'var(--text-3)' }}>{j + 1}</div>
                    <div className="mono" style={{ color: 'var(--text-1)' }}>{s.reps} reps</div>
                    <div className="mono" style={{ color: 'var(--text-1)', textAlign: 'right' }}>{s.load}</div>
                    <div className="mono" style={{ color: 'var(--text-2)', textAlign: 'right' }}>RPE {s.rpe}</div>
                    <div
                      title={s.status === 'auto' ? 'Auto-tracked' : 'Manual'}
                      style={{
                        width: 8, height: 8, borderRadius: 4, marginLeft: 'auto',
                        background: s.status === 'auto' ? 'var(--accent)' : 'var(--text-3)',
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div style={{
          marginTop: 14, padding: '10px 14px', borderRadius: 10,
          background: 'var(--surface-1)', border: '1px solid var(--hairline)',
          fontSize: 11, color: 'var(--text-3)',
          display: 'flex', alignItems: 'center', gap: 14,
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: 4, background: 'var(--accent)' }} /> Auto
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: 4, background: 'var(--text-3)' }} /> Manual entry
          </span>
        </div>
      </div>
    </Screen>
  );
};

Object.assign(window, { PastWorkoutScreen });
