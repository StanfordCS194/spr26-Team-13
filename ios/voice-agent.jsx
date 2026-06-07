// TrainAR — Voice coach surface.
//
// The coach is activated by VOICE through the AR glasses (wake word), so there
// is deliberately NO mic button or "Hey Coach" tap target on the phone. The
// phone shows nothing until the real wake-word / voice-command events fire from
// the native bridge; then a slim capsule slides up at the bottom. It never dims
// or covers the plan, so when the coach logs a set or edits a weight, that
// change stays visible on the training table right above it.
//
// This file only provides the visuals (Waveform, CapIndicator, CoachCapsule).
// The state that drives them is owned by app.jsx and comes straight from the
// backend coach events (trainar:glasses wakeWordDetected/voiceCommand and
// trainar:coach-response / trainar:coach-action).

// ─────────────────────────────────────────────────────────────
// Waveform — the coach's identity motif: lime bars that breathe.
// ─────────────────────────────────────────────────────────────
const Waveform = ({ phase = 'listening', barW = 2.5, gap = 2.5, height = 15, count = 5, color = 'var(--accent)' }) => {
  const cfg = {
    listening: { dur: 0.7, peaks: [0.5, 0.95, 0.45, 1, 0.6] },
    thinking:  { dur: 1.25, peaks: [0.32, 0.42, 0.3, 0.44, 0.32] },
    idle:      { dur: 0, peaks: [0.35, 0.6, 0.4, 0.62, 0.4] },
  }[phase] || { dur: 0, peaks: [0.4, 0.5, 0.4, 0.5, 0.4] };
  const animated = cfg.dur > 0;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap, height }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={animated ? 'va-bar' : ''} style={{
          width: barW, height, borderRadius: barW, background: color,
          transform: animated ? undefined : `scaleY(${cfg.peaks[i % cfg.peaks.length]})`,
          animationDuration: animated ? `${cfg.dur}s` : undefined,
          animationDelay: animated ? `${(i * cfg.dur) / count - cfg.dur}s` : undefined,
          opacity: phase === 'thinking' ? 0.7 : 1,
        }} />
      ))}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// CapIndicator — round indicator that fronts the capsule:
// listening waveform → thinking spinner → result check / waveform.
// ─────────────────────────────────────────────────────────────
const CapIndicator = ({ state, result }) => {
  const ring = state === 'listening';
  const bg = (state === 'result' && result)
    ? (result.kind === 'action' ? 'var(--accent)' : 'var(--accent-soft)')
    : 'var(--surface-3)';
  return (
    <div style={{ position: 'relative', width: 36, height: 36, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      {ring && [0, 1].map((i) => (
        <span key={i} className="orb-ring" style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '1.5px solid var(--accent)', animationDelay: `${i * 1.1}s` }} />
      ))}
      <div style={{
        width: 36, height: 36, borderRadius: '50%', background: bg,
        border: '1px solid ' + (state === 'result' && result && result.kind === 'info' ? 'rgba(197,242,62,0.4)' : (ring ? 'var(--accent)' : 'var(--hairline-2)')),
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: ring ? '0 0 18px rgba(197,242,62,0.4)' : 'none',
        transition: 'background 240ms',
      }}>
        {state === 'thinking'
          ? <div className="spin-ring" style={{ width: 15, height: 15, borderRadius: '50%', border: '2px solid var(--overlay-3)', borderTopColor: 'var(--accent)' }} />
          : state === 'result' && result
            ? (result.kind === 'action'
                ? <Icon name="check" size={18} stroke="var(--on-accent)" strokeWidth={2.5} />
                : <Waveform phase="idle" height={13} barW={2.5} gap={2.5} count={4} />)
            : <Waveform phase={state === 'listening' ? 'listening' : 'idle'} height={15} barW={2.5} gap={2.5} count={5} />}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// CoachCapsule — the only on-screen coach surface. Appears once the
// wake word fires; slides up as a slim bottom capsule that leaves the
// plan visible above it. States: listening → thinking → result.
//   state      'listening' | 'thinking' | 'result'
//   transcript what was heard (shown while listening/thinking)
//   result     { text, kind: 'action' | 'info' } when answered
// ─────────────────────────────────────────────────────────────
const CoachCapsule = ({ state, transcript = '', result = null, sources = [], onClose, bottomBase = 86 }) => {
  const isResult = state === 'result' && !!result;
  const statusLabel = state === 'listening'
    ? 'LISTENING'
    : state === 'thinking'
      ? 'THINKING'
      : isResult
        ? (result.kind === 'action' ? 'DONE' : 'COACH')
        : 'COACH';
  const accentEdge = isResult
    ? (result.kind === 'action' ? 'var(--accent)' : 'rgba(197,242,62,0.4)')
    : (state === 'listening' ? 'var(--accent)' : 'var(--hairline-2)');

  return (
    <div style={{ position: 'absolute', left: 12, right: 12, bottom: bottomBase, zIndex: 60 }}>
      <div className="capsule-in" style={{
        display: 'flex', alignItems: isResult ? 'flex-start' : 'center', gap: 12,
        padding: '11px 14px', borderRadius: 20,
        background: 'var(--surface-1)',
        border: '1px solid ' + accentEdge,
        boxShadow: '0 14px 36px rgba(0,0,0,0.5)',
      }}>
        <CapIndicator state={state} result={result} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="mono" style={{
            fontSize: 8.5, letterSpacing: 0.9,
            color: isResult ? 'var(--accent)' : 'var(--text-3)',
            display: 'flex', alignItems: 'center', gap: 5, marginBottom: 3,
          }}>
            {(state === 'listening' || isResult) && (
              <span className="pulse-dot" style={{ width: 4, height: 4, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
            )}
            {statusLabel}
          </div>
          {isResult ? (
            <div>
              <div style={{ fontSize: 13.5, lineHeight: 1.35, color: 'var(--text-1)', fontWeight: 500 }}>{result.text}</div>
              {sources.length > 0 && (
                <div style={{ marginTop: 7, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {sources.slice(0, 2).map((source, i) => (
                    <span key={source.key || i} style={{
                      border: '1px solid rgba(197,242,62,0.18)',
                      background: 'rgba(197,242,62,0.06)',
                      color: 'var(--accent)',
                      borderRadius: 999, padding: '3px 7px', whiteSpace: 'nowrap',
                      fontSize: 10,
                    }}>
                      {source.authors} {source.year}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{
              fontSize: 15, lineHeight: 1.3, fontWeight: 500, letterSpacing: -0.2,
              color: transcript ? 'var(--text-1)' : 'var(--text-3)',
              overflow: 'hidden', textOverflow: 'ellipsis',
            }}>
              {transcript || (state === 'thinking' ? 'Thinking…' : 'Listening…')}
              {state === 'listening' && <span className="caret-blink" style={{ color: 'var(--accent)' }}>|</span>}
            </div>
          )}
        </div>
        {isResult && onClose && (
          <button onClick={onClose} aria-label="Dismiss coach" className="press" style={{
            width: 26, height: 26, borderRadius: 13, flexShrink: 0,
            border: '1px solid var(--hairline)', background: 'var(--overlay-1)',
            color: 'var(--text-2)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
          }}>
            <Icon name="x" size={13} />
          </button>
        )}
      </div>
    </div>
  );
};

Object.assign(window, { Waveform, CapIndicator, CoachCapsule });
