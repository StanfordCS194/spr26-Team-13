// Program detail / view screen.
//
// Same flat exercise table as the Review screen but with a different chrome:
// back button + Saved/In-progress pill + trash icon up top, sticky CTA at the
// bottom that flips between "Start workout" and "Finish workout" depending on
// whether this program is currently loaded to the glasses.

const ProgramViewScreen = ({
  program,
  loadedToGlasses = false,
  onClose,
  onStartWorkout,
  onFinishWorkout,
  onDiscard,
}) => {
  const source = program || window.PROGRAM_DETAIL || {};
  const exercises = source.exercises || [];

  // Pull a friendly name. Falls back to the first program in PROGRAMS if the
  // detail object doesn't have one — same as the prototype.
  const fallbackProgram = (window.PROGRAMS || [])[0];
  const initialName = source.name || (fallbackProgram && fallbackProgram.name) || 'Powerbuilding 5×';

  const [openRow, setOpenRow] = React.useState(null);
  const [name, setName] = React.useState(initialName);
  const [editing, setEditing] = React.useState(false);
  const [confirmDiscard, setConfirmDiscard] = React.useState(false);
  const inputRef = React.useRef(null);

  React.useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  return (
    <Screen padTop={64} padBottom={130}>
      {/* Top chrome — back / status pill / discard. */}
      <div style={{
        padding: '0 20px 16px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <button onClick={onClose} className="press" style={{
          width: 36, height: 36, borderRadius: 9999,
          background: 'var(--surface-1)', border: '1px solid var(--hairline)',
          color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="arrow-left" size={16} /></button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {loadedToGlasses ? (
            <Pill accent>
              <span style={{
                display: 'inline-block', width: 6, height: 6, borderRadius: '50%',
                background: 'var(--accent)', marginRight: 6,
                boxShadow: '0 0 6px var(--accent)',
              }} />
              Workout in progress
            </Pill>
          ) : (
            <Pill>Saved</Pill>
          )}
          <button
            onClick={loadedToGlasses ? undefined : () => setConfirmDiscard(true)}
            disabled={loadedToGlasses}
            className={loadedToGlasses ? '' : 'press'}
            aria-label="Discard program"
            style={{
              width: 36, height: 36, borderRadius: 9999,
              background: 'var(--surface-1)', border: '1px solid var(--hairline)',
              color: 'var(--text-2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: loadedToGlasses ? 'not-allowed' : 'pointer',
              opacity: loadedToGlasses ? 0.4 : 1,
            }}
          ><Icon name="trash" size={15} /></button>
        </div>
      </div>

      {/* Discard confirm sheet. */}
      {confirmDiscard && (
        <div
          style={{
            position: 'absolute', inset: 0, zIndex: 50,
            background: 'rgba(0,0,0,0.55)',
            backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)',
            display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
          }}
          onClick={() => setConfirmDiscard(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: 'calc(100% - 24px)', margin: '0 12px 24px', padding: 22,
              background: 'var(--surface-1)', border: '1px solid var(--hairline)',
              borderRadius: 'var(--r-card)',
              display: 'flex', flexDirection: 'column', gap: 16,
            }}
          >
            <div>
              <div style={{ fontSize: 17, fontWeight: 600, letterSpacing: -0.3, marginBottom: 6 }}>
                Discard this program?
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.45 }}>
                {name} will be removed from your library. Past workout history is kept.
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                onClick={() => { setConfirmDiscard(false); onDiscard && onDiscard(); }}
                className="press"
                style={{
                  width: '100%', padding: '14px 16px', borderRadius: 9999,
                  background: '#FF8A7A', border: 'none', color: '#1A0A07',
                  fontSize: 15, fontWeight: 600, letterSpacing: -0.2, cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                }}
              >Discard program</button>
              <button
                onClick={() => setConfirmDiscard(false)}
                className="press"
                style={{
                  width: '100%', padding: '14px 16px', borderRadius: 9999,
                  background: 'transparent', border: '1px solid var(--hairline)', color: 'var(--text-1)',
                  fontSize: 15, fontWeight: 500, letterSpacing: -0.2, cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                }}
              >Keep</button>
            </div>
          </div>
        </div>
      )}

      {/* Title + tap-to-rename. */}
      <div style={{ padding: '0 20px 18px' }}>
        {editing ? (
          <input
            ref={inputRef}
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => setEditing(false)}
            onKeyDown={(e) => { if (e.key === 'Enter') setEditing(false); }}
            style={{
              width: '100%',
              fontSize: 30, fontWeight: 600, letterSpacing: -0.6,
              background: 'transparent',
              border: 'none', outline: 'none',
              borderBottom: '2px solid var(--accent)',
              color: 'var(--text-1)', margin: 0, marginBottom: 8,
              padding: '0 0 4px',
              fontFamily: 'var(--font-sans)',
            }}
          />
        ) : (
          <h1
            onClick={() => setEditing(true)}
            className="press"
            style={{
              fontSize: 30, fontWeight: 600, letterSpacing: -0.6, margin: 0, marginBottom: 8,
              cursor: 'text',
              display: 'inline-flex', alignItems: 'center', gap: 10,
            }}
          >
            <span>{name || 'Untitled program'}</span>
            <Icon name="edit" size={16} stroke="var(--text-3)" />
          </h1>
        )}
        <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, lineHeight: 1.5 }}>
          {exercises.length} lifts · tap title to rename
        </p>
      </div>

      {/* Exercise table — same component shape as ReviewScreen. */}
      <div style={{ padding: '0 20px' }}>
        <Card padding={0}>
          {exercises.map((ex, i) => {
            const isOpen = openRow === i;
            const hasNote = !!ex.note;
            return (
              <div key={i} style={{
                borderBottom: i < exercises.length - 1 ? '1px solid var(--hairline)' : 'none',
              }}>
                <div
                  onClick={() => hasNote && setOpenRow(isOpen ? null : i)}
                  className={hasNote ? 'press' : ''}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1.6fr 36px 44px 56px 16px',
                    gap: 8, alignItems: 'center',
                    padding: '13px 14px',
                    cursor: hasNote ? 'pointer' : 'default',
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <div style={{
                      fontSize: 13, fontWeight: 500, letterSpacing: -0.1, lineHeight: 1.25,
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {ex.name}
                    </div>
                  </div>
                  <div className="mono" style={{ fontSize: 12, color: 'var(--text-2)', textAlign: 'right' }}>{ex.sets}</div>
                  <div className="mono" style={{ fontSize: 12, color: 'var(--text-2)', textAlign: 'right' }}>{ex.reps}</div>
                  <div className="mono" style={{ fontSize: 12, color: 'var(--accent)', textAlign: 'right', fontWeight: 600 }}>{ex.load}</div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    {hasNote ? (
                      <Icon
                        name="chevron-down"
                        size={13}
                        stroke="var(--text-3)"
                        style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 180ms ease' }}
                      />
                    ) : (
                      <span style={{ width: 13, height: 13, display: 'block' }} />
                    )}
                  </div>
                </div>

                {hasNote && (
                  <div style={{ maxHeight: isOpen ? 200 : 0, overflow: 'hidden', transition: 'max-height 220ms ease' }}>
                    <div style={{
                      padding: '10px 14px 14px 14px',
                      fontSize: 12, color: 'var(--text-2)', lineHeight: 1.45,
                      borderTop: '1px solid var(--hairline)',
                    }}>
                      <div className="mono" style={{
                        fontSize: 9, color: 'var(--text-3)', letterSpacing: 0.5,
                        textTransform: 'uppercase', marginBottom: 4,
                      }}>Notes</div>
                      {ex.note}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </Card>
      </div>

      {/* Sticky CTA — Start vs Finish workout. */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        padding: '16px 20px 24px',
        background: 'linear-gradient(180deg, transparent, var(--bg) 30%)',
      }}>
        {loadedToGlasses ? (
          <Button
            onClick={onFinishWorkout}
            icon="check"
            variant="surface"
            style={{ background: 'var(--surface-2)', color: 'var(--text-1)', border: '1px solid var(--accent)' }}
          >
            Finish workout
          </Button>
        ) : (
          <Button onClick={onStartWorkout} icon="glasses">
            Start workout
          </Button>
        )}
      </div>
    </Screen>
  );
};

Object.assign(window, { ProgramViewScreen });
