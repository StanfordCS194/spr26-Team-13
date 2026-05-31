// History tab — Apple Fitness style heatmap + recent sessions list.
// Reads from window.ACTIVITY (84-day intensity 0..3) and window.HISTORY.

const CalendarScreen = ({ onOpenWorkout }) => {
  const sessions = window.TRAINAR_SESSIONS || [];
  const initialMonth = getInitialCalendarMonth(sessions);
  const [visibleMonth, setVisibleMonth] = React.useState(initialMonth);
  const [selectedDay, setSelectedDay] = React.useState(null);
  const monthModel = buildCalendarMonth(sessions, visibleMonth.year, visibleMonth.monthIndex);
  const monthDays = monthModel.days;
  const firstDayOffset = monthModel.firstDayOffset;
  const selectedDaySessions = selectedDay ? (monthModel.sessionsByDay[selectedDay] || []) : [];

  const stats = monthModel.stats || window.ACTIVITY_STATS || {
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
        <button
          onClick={() => { setSelectedDay(null); setVisibleMonth(shiftMonth(visibleMonth, -1)); }}
          className="press"
          style={{
          width: 32, height: 32, borderRadius: 9999,
          background: 'var(--surface-1)', border: '1px solid var(--hairline)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}
        ><Icon name="chevron-left" size={14} /></button>
        <div style={{ fontSize: 16, fontWeight: 600 }}>{monthLabel(visibleMonth)}</div>
        <button
          onClick={() => { setSelectedDay(null); setVisibleMonth(shiftMonth(visibleMonth, 1)); }}
          className="press"
          style={{
          width: 32, height: 32, borderRadius: 9999,
          background: 'var(--surface-1)', border: '1px solid var(--hairline)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}
        ><Icon name="chevron-right" size={14} /></button>
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
          const today = appDateParts(new Date().toISOString());
          const isToday = day === today.day && visibleMonth.monthIndex === today.monthIndex && visibleMonth.year === today.year;
          const cell = intensities[v];
          const daySessions = monthModel.sessionsByDay[day] || [];
          return (
            <button
              key={i}
              onClick={() => {
                if (!v || !daySessions.length) return;
                if (daySessions.length === 1) {
                  onOpenWorkout && onOpenWorkout(daySessions[0].id);
                } else {
                  setSelectedDay(day);
                }
              }}
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
              {daySessions.length > 1 && (
                <div className="mono" style={{
                  position: 'absolute', right: 4, bottom: 3, zIndex: 2,
                  fontSize: 8, color: 'var(--accent)', fontWeight: 700,
                }}>{daySessions.length}</div>
              )}
              {v > 0 && (
                <div style={{ position: 'absolute', inset: 0, background: cell.bg, opacity: 0.5 }} />
              )}
            </button>
          );
        })}
      </div>

      {selectedDaySessions.length > 1 && (
        <div style={{ padding: '0 20px 18px' }}>
          <div style={{
            padding: 14,
            borderRadius: 'var(--r-card)',
            background: 'var(--surface-1)',
            border: '1px solid var(--hairline)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-2)' }}>
                {monthLabel(visibleMonth)} {selectedDay}
              </div>
              <button
                onClick={() => setSelectedDay(null)}
                aria-label="Close day workouts"
                style={{
                  width: 26, height: 26, borderRadius: 9999,
                  border: '1px solid var(--hairline)',
                  background: 'var(--surface-2)',
                  color: 'var(--text-2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer',
                }}
              >
                <Icon name="x" size={13} />
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {selectedDaySessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => onOpenWorkout && onOpenWorkout(session.id)}
                  className="press"
                  style={{
                    width: '100%',
                    padding: '12px 12px',
                    borderRadius: 12,
                    border: '1px solid var(--hairline)',
                    background: 'var(--surface-2)',
                    color: 'var(--text-1)',
                    textAlign: 'left',
                    fontFamily: 'var(--font-sans)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 650 }}>{session.title || 'Workout'}</div>
                  <div className="mono" style={{ fontSize: 10, color: 'var(--text-3)', marginTop: 3 }}>
                    {formatSessionTime(session.started_at || session.created_at)} · {session.total_sets || 0} sets
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

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

function getInitialCalendarMonth(sessions) {
  const latest = sessions
    .map((session) => appDateParts(session.started_at || session.created_at))
    .filter(Boolean)
    .sort((a, b) => b.sortKey.localeCompare(a.sortKey))[0];
  return latest || appDateParts(new Date().toISOString());
}

function buildCalendarMonth(sessions, year, monthIndex) {
  const daysInMonth = new Date(Date.UTC(year, monthIndex + 1, 0)).getUTCDate();
  const firstWeekday = new Date(Date.UTC(year, monthIndex, 1)).getUTCDay();
  const firstDayOffset = (firstWeekday + 6) % 7;
  const days = Array.from({ length: daysInMonth }, () => 0);
  const sessionIds = {};
  const sessionsByDay = {};

  sessions.forEach((session) => {
    const parts = appDateParts(session.started_at || session.created_at);
    if (!parts || parts.year !== year || parts.monthIndex !== monthIndex) return;
    const volume = Number(session.total_volume || 0);
    days[parts.day - 1] = Math.max(
      days[parts.day - 1],
      volume > 20000 ? 3 : session.total_sets > 12 ? 2 : 1,
    );
    if (!sessionIds[parts.day] || parts.sortKey > sessionIds[parts.day].sortKey) {
      sessionIds[parts.day] = { ...session, sortKey: parts.sortKey };
    }
    sessionsByDay[parts.day] = sessionsByDay[parts.day] || [];
    sessionsByDay[parts.day].push({ ...session, sortKey: parts.sortKey });
  });

  Object.keys(sessionsByDay).forEach((day) => {
    sessionsByDay[day].sort((left, right) => right.sortKey.localeCompare(left.sortKey));
  });

  return { days, firstDayOffset, sessionIds, sessionsByDay, stats: buildCalendarStats(sessions, year, monthIndex) };
}

function buildCalendarStats(sessions, year, monthIndex) {
  const monthSessions = sessions.filter((session) => {
    const parts = appDateParts(session.started_at || session.created_at);
    return parts && parts.year === year && parts.monthIndex === monthIndex;
  });
  const totalVolume = monthSessions.reduce((sum, session) => sum + Number(session.total_volume || 0), 0);
  const rpeSessions = monthSessions.filter((session) => Number(session.avg_rpe || 0) > 0);
  const avgRpe = rpeSessions.length
    ? rpeSessions.reduce((sum, session) => sum + Number(session.avg_rpe || 0), 0) / rpeSessions.length
    : 0;
  return {
    sessions: monthSessions.length,
    streak: longestStreak(monthSessions),
    volume: totalVolume >= 1000 ? `${Math.round(totalVolume / 1000)}k` : String(Math.round(totalVolume)),
    rpe: avgRpe ? Number(avgRpe.toFixed(1)) : 0,
  };
}

function longestStreak(sessions) {
  const activeDays = new Set(
    sessions
      .map((session) => appDateParts(session.started_at || session.created_at)?.day)
      .filter(Boolean),
  );
  let best = 0;
  let current = 0;
  for (let day = 1; day <= 31; day++) {
    if (activeDays.has(day)) {
      current += 1;
      best = Math.max(best, current);
    } else {
      current = 0;
    }
  }
  return best;
}

function shiftMonth(month, delta) {
  const date = new Date(Date.UTC(month.year, month.monthIndex + delta, 1));
  return { year: date.getUTCFullYear(), monthIndex: date.getUTCMonth() };
}

function monthLabel(month) {
  return new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' })
    .format(new Date(Date.UTC(month.year, month.monthIndex, 1)));
}

function formatSessionTime(value) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: 'America/Los_Angeles',
  }).format(new Date(value));
}

function appDateParts(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/Los_Angeles',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).formatToParts(date).map((part) => [part.type, part.value]),
  );
  return {
    year: Number(parts.year),
    monthIndex: Number(parts.month) - 1,
    day: Number(parts.day),
    sortKey: date.toISOString(),
  };
}

Object.assign(window, { CalendarScreen });
