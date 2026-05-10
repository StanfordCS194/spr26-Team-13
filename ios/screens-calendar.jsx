// History tab — Apple Fitness style heatmap + recent sessions list.
// Reads from window.ACTIVITY (84-day intensity 0..3) and window.HISTORY.

const CalendarScreen = ({ onOpenWorkout }) => {
  const days = window.ACTIVITY || [];
  // Render April 2026. Supabase-backed data provides this directly; the
  // old 84-day buffer remains as a fallback for static demo mode.
  const monthDays = window.ACTIVITY_MONTH_DAYS || Array.from({ length: 30 }, (_, i) => days[40 + i] || 0);
  const firstDayOffset = 2; // April 1 2026 was a Wed → Mon-first grid offset of 2.

  const stats = window.ACTIVITY_STATS || {
    sessions: monthDays.filter((d) => d > 0).length,
    streak: 4,
    volume: '184k',
    rpe: 7.9,
  };

  const intensities = {
    0: { bg: 'transparent',          dot: 'transparent' },
    1: { bg: 'rgba(197,242,62,0.15)', dot: 'rgba(197,242,62,0.35)' },
    2: { bg: 'rgba(197,242,62,0.35)', dot: 'rgba(197,242,62,0.7)'  },
    3: { bg: 'rgba(197,242,62,0.6)',  dot: 'var(--accent)'         },
  };

  const recent = (window.HISTORY || []).filter((h) => h.sets > 0).slice(0, 5);

  return (
    <Screen padTop={56} padBottom={120}>
      {/* Title + subtitle. */}
      <div style={{ padding: '0 20px 20px' }}>
        <h1 style={{ fontSize: 28, fontWeight: 600, letterSpacing: -0.5, margin: 0 }}>History</h1>
        <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, marginTop: 2 }}>
          Every set the glasses logged.
        </p>
      </div>

      {/* Stats strip. */}
      <div style={{ padding: '0 20px 20px' }}>
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 1,
          background: 'var(--hairline)', border: '1px solid var(--hairline)',
          borderRadius: 18, overflow: 'hidden',
        }}>
          {[
            { l: 'Sessions', v: stats.sessions, c: 'var(--accent)' },
            { l: 'Streak',   v: stats.streak,   c: 'var(--text-1)' },
            { l: 'Volume',   v: stats.volume,   c: 'var(--text-1)' },
            { l: 'Avg RPE',  v: stats.rpe,      c: 'var(--text-1)' },
          ].map((s, i) => (
            <div key={i} style={{ background: 'var(--surface-1)', padding: '12px 8px', textAlign: 'center' }}>
              <div className="mono" style={{ fontSize: 18, fontWeight: 600, color: s.c }}>{s.v}</div>
              <div style={{
                fontSize: 9, color: 'var(--text-3)', marginTop: 2,
                textTransform: 'uppercase', letterSpacing: 0.5,
              }}>{s.l}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Month nav. */}
      <div style={{
        padding: '0 20px 14px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <button className="press" style={{
          width: 32, height: 32, borderRadius: 9999,
          background: 'var(--surface-1)', border: '1px solid var(--hairline)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="chevron-left" size={14} /></button>
        <div style={{ fontSize: 16, fontWeight: 600 }}>April 2026</div>
        <button className="press" style={{
          width: 32, height: 32, borderRadius: 9999,
          background: 'var(--surface-1)', border: '1px solid var(--hairline)', color: 'var(--text-3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="chevron-right" size={14} stroke="var(--text-3)" /></button>
      </div>

      {/* Day-of-week labels. */}
      <div style={{
        padding: '0 20px 8px',
        display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4,
      }}>
        {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => (
          <div key={i} className="mono" style={{
            textAlign: 'center', fontSize: 10, color: 'var(--text-3)', letterSpacing: 0.5,
          }}>{d}</div>
        ))}
      </div>

      {/* Month grid. */}
      <div style={{
        padding: '0 20px 24px',
        display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4,
      }}>
        {Array.from({ length: firstDayOffset }).map((_, i) => <div key={'empty-' + i} />)}
        {monthDays.map((v, i) => {
          const day = i + 1;
          const isToday = day === 27;
          const cell = intensities[v];
          const sessionId = window.TRAINAR_MONTH_SESSION_IDS?.[day]?.id;
          return (
            <button
              key={i}
              onClick={() => v > 0 && onOpenWorkout && onOpenWorkout(sessionId)}
              className={v > 0 ? 'press' : ''}
              style={{
                aspectRatio: '1',
                background: 'var(--surface-1)',
                border: '1px solid ' + (isToday ? 'var(--accent)' : 'var(--hairline)'),
                borderRadius: 10,
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                gap: 3, position: 'relative',
                cursor: v > 0 ? 'pointer' : 'default',
                padding: 0, color: 'var(--text-1)', fontFamily: 'var(--font-sans)',
                overflow: 'hidden',
              }}
            >
              <div className="mono" style={{
                fontSize: 12, fontWeight: isToday ? 700 : 500,
                color: isToday ? 'var(--accent)' : v > 0 ? 'var(--text-1)' : 'var(--text-3)',
                zIndex: 1,
              }}>{day}</div>
              {v > 0 && (
                <div style={{ width: 6, height: 6, borderRadius: 3, background: cell.dot, zIndex: 1 }} />
              )}
              {v > 0 && (
                <div style={{ position: 'absolute', inset: 0, background: cell.bg, opacity: 0.5 }} />
              )}
            </button>
          );
        })}
      </div>

      {/* Recent sessions list. */}
      <div style={{ padding: '0 20px' }}>
        <div style={{
          fontSize: 13, fontWeight: 600, color: 'var(--text-2)',
          marginBottom: 10, padding: '0 4px',
        }}>Recent</div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {recent.map((h, i) => (
            <div
              key={i}
              onClick={() => onOpenWorkout && onOpenWorkout(h.id)}
              className="press"
              style={{
                display: 'flex', alignItems: 'center', gap: 14,
                padding: '14px 16px', borderRadius: 16,
                background: 'var(--surface-1)', border: '1px solid var(--hairline)',
                cursor: 'pointer',
              }}
            >
              <div className="mono" style={{
                width: 38, height: 38, borderRadius: 10,
                background: 'rgba(197,242,62,0.08)', border: '1px solid var(--hairline)',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              }}>
                <div style={{ fontSize: 9, color: 'var(--text-3)', textTransform: 'uppercase' }}>{h.day}</div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{(h.date || '').split(' ')[1]}</div>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 500 }}>{h.name}</div>
                <div className="mono" style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>
                  {h.volume} · {h.duration} · RPE {h.rpe}
                </div>
              </div>
              {h.prs > 0 && (
                <Pill accent>
                  <Icon name="trophy" size={11} stroke="var(--accent)" />{h.prs} PR
                </Pill>
              )}
              <Icon name="chevron-right" size={16} stroke="var(--text-3)" />
            </div>
          ))}
        </div>
      </div>
    </Screen>
  );
};

Object.assign(window, { CalendarScreen });
