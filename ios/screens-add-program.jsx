// Add-program flow screens: Entry → Camera → Parsing → Review (or Failed scan).
//
// The upload/camera entry points post files to the same Flask ingestion API
// used by the desktop app, then adapt the returned TrainingProgram for these
// compact iOS review screens.

// Reuses the Screen wrapper defined in screens-signup.jsx.

// ─────────────────────────────────────────────────────────────
// 1. Entry — pick a source.
// ─────────────────────────────────────────────────────────────
const ACCEPTED_PROGRAM_INPUTS = 'image/*,.pdf,.csv,.xlsx,.xls,.txt';

const AddProgramScreen = ({ onCamera, onFileSelected, onClose }) => {
  const uploadRef = React.useRef(null);

  const handleFiles = (files) => {
    if (!files || !files.length) return;
    onFileSelected && onFileSelected(files[0]);
  };

  return (
    <Screen padTop={64} padBottom={32}>
      <input
        ref={uploadRef}
        type="file"
        accept={ACCEPTED_PROGRAM_INPUTS}
        onChange={(e) => handleFiles(e.target.files)}
        style={{ display: 'none' }}
      />

      <div style={{ padding: '0 20px 16px' }}>
        <button onClick={onClose} className="press" style={{
          width: 36, height: 36, borderRadius: 9999, background: 'var(--surface-1)',
          border: '1px solid var(--hairline)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="arrow-left" size={16} /></button>
      </div>

      <div style={{ padding: '0 20px 16px' }}>
        <h1 style={{ fontSize: 26, fontWeight: 600, letterSpacing: -0.5, margin: 0 }}>
          Add a program
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, marginTop: 4 }}>
          Drop in any program. We'll parse and structure it.
        </p>
      </div>

      <div style={{
        padding: '12px 20px', display: 'flex',
        flexDirection: 'column', gap: 10,
      }}>
        {/* Hero — Take a photo */}
        <button onClick={onCamera} className="press" style={{
          position: 'relative', overflow: 'hidden',
          padding: 22, borderRadius: 'var(--r-card-lg)',
          background: 'var(--hero-bg)',
          border: '1px solid var(--hero-border)',
          color: 'var(--text-1)', textAlign: 'left', cursor: 'pointer',
          fontFamily: 'var(--font-sans)',
        }}>
          <div style={{
            width: 48, height: 48, borderRadius: 14, background: 'var(--accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16,
            position: 'relative',
          }}>
            <Icon name="camera" size={22} stroke="var(--on-accent)" strokeWidth={2} />
          </div>
          <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 4, position: 'relative' }}>
            Take a photo
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.4, position: 'relative' }}>
            Snap your spreadsheet, whiteboard, or coach's notebook.
          </div>
        </button>

        {/* Upload a file */}
        <button onClick={() => uploadRef.current && uploadRef.current.click()} className="press" style={{
          padding: 22, borderRadius: 'var(--r-card-lg)',
          background: 'var(--surface-1)', border: '1px solid var(--hairline)',
          color: 'var(--text-1)', textAlign: 'left', cursor: 'pointer',
          fontFamily: 'var(--font-sans)',
        }}>
          <div style={{
            width: 48, height: 48, borderRadius: 14, background: 'var(--surface-2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16,
            border: '1px solid var(--hairline)',
          }}>
            <Icon name="upload" size={20} />
          </div>
          <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 4 }}>Upload a file</div>
          <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.4 }}>
            PDF, image, spreadsheet, or plain text from your library.
          </div>
        </button>
      </div>
    </Screen>
  );
};

// ─────────────────────────────────────────────────────────────
// 2. Camera — UI over a real camera view.
//
// The rotated "paper" rectangle in the middle is a placeholder for the
// camera feed. When the backend wires up a real camera, swap the paper
// div for a <video> element bound to getUserMedia (or whatever they end
// up using). The rest of the chrome — close, flash, capture — stays.
// ─────────────────────────────────────────────────────────────
const CameraScreen = ({ onFileSelected, onClose }) => {
  const lines = window.PROGRAM_SAMPLE_LINES || [];
  const cameraRef = React.useRef(null);
  const galleryRef = React.useRef(null);

  const handleFiles = (files) => {
    if (!files || !files.length) return;
    onFileSelected && onFileSelected(files[0]);
  };

  return (
    <Screen padTop={0} padBottom={0} style={{
      display: 'flex', flexDirection: 'column', background: 'var(--camera-bg, #000)',
    }}>
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={(e) => handleFiles(e.target.files)}
        style={{ display: 'none' }}
      />
      <input
        ref={galleryRef}
        type="file"
        accept={ACCEPTED_PROGRAM_INPUTS}
        onChange={(e) => handleFiles(e.target.files)}
        style={{ display: 'none' }}
      />

      {/* Viewfinder area — the placeholder lives in here. */}
      <div style={{
        flex: 1, position: 'relative',
        background: 'linear-gradient(180deg, #1a1a1a, #0a0a0a)',
        overflow: 'hidden',
      }}>
        {/* Fake "paper" with rows — looks like a program sheet. */}
        <div style={{
          position: 'absolute', top: 80, left: 30, right: 30, bottom: 120,
          background: '#f4f1ea', borderRadius: 4, padding: 16,
          transform: 'rotate(-2.4deg)',
          boxShadow: '0 30px 60px rgba(0,0,0,0.6)',
          fontFamily: 'var(--font-mono)', fontSize: 9, color: '#3a3a3a',
          lineHeight: 1.6, overflow: 'hidden',
        }}>
          <div style={{ fontWeight: 700, fontSize: 11, marginBottom: 6 }}>FULL BODY</div>
          <div style={{ borderBottom: '1px solid #ccc', marginBottom: 6 }} />
          {lines.map((l, i) => <div key={i}>{l}</div>)}
        </div>

        {/* Top close + flash chips. */}
        <button onClick={onClose} className="press" style={{
          position: 'absolute', top: 60, left: 20,
          width: 40, height: 40, borderRadius: 9999,
          background: 'var(--cam-chip-bg)',
          backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)',
          border: '1px solid var(--cam-chip-border)', color: 'var(--cam-chip-fg)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="x" size={18} stroke="var(--cam-chip-fg)" /></button>
        <button className="press" style={{
          position: 'absolute', top: 60, right: 20,
          width: 40, height: 40, borderRadius: 9999,
          background: 'var(--cam-chip-bg)',
          backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)',
          border: '1px solid var(--cam-chip-border)', color: 'var(--cam-chip-fg)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="flash" size={18} stroke="var(--cam-chip-fg)" /></button>
      </div>

      {/* Bottom controls — gallery, capture, spacer. */}
      <div style={{
        padding: '24px 20px 36px', background: 'var(--camera-bg, #000)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-around',
      }}>
        <button onClick={() => galleryRef.current && galleryRef.current.click()} className="press" style={{
          width: 52, height: 52, borderRadius: 14,
          background: 'var(--surface-2)', border: '1px solid var(--hairline)',
          color: 'var(--text-1)', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}><Icon name="image" size={20} /></button>

        <button onClick={() => cameraRef.current && cameraRef.current.click()} className="press" style={{
          width: 78, height: 78, borderRadius: '50%',
          background: 'transparent',
          border: '3px solid rgba(255,255,255,0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', padding: 4,
        }}>
          <div style={{
            width: '100%', height: '100%', borderRadius: '50%',
            background: 'var(--accent)',
          }} />
        </button>

        {/* Spacer to keep the capture button centered. */}
        <div style={{ width: 52, height: 52 }} />
      </div>
    </Screen>
  );
};

// ─────────────────────────────────────────────────────────────
// 3. Parsing — AI phases animation backed by the real ingestion request.
// ─────────────────────────────────────────────────────────────
const ParsingScreen = ({ file, onDone, onFailed, onCancel }) => {
  const phases = [
    'Reading the source',
    'Identifying exercises',
    'Parsing sets, reps, percentages',
    'Structuring the schedule',
  ];
  const [phase, setPhase] = React.useState(0);
  const [parsedDetail, setParsedDetail] = React.useState(null);
  const [parseError, setParseError] = React.useState(null);
  const [previewUrl, setPreviewUrl] = React.useState(null);

  React.useEffect(() => {
    if (!file) {
      const message = 'Choose a program file before parsing.';
      setParseError(message);
      onFailed && onFailed(message);
      return undefined;
    }

    const controller = new AbortController();
    setPhase(0);
    setParsedDetail(null);
    setParseError(null);

    parseProgramFile(file, { signal: controller.signal })
      .then((payload) => {
        const detail = canonicalToIOSProgram(payload.program);
        setParsedDetail(detail);
      })
      .catch((err) => {
        if (err.name === 'AbortError') return;
        const message = err.message || 'Program parsing failed.';
        setParseError(message);
        onFailed && onFailed(message);
      });

    return () => controller.abort();
  }, [file]);

  React.useEffect(() => {
    if (!file || !file.type || !file.type.startsWith('image/')) {
      setPreviewUrl(null);
      return undefined;
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  React.useEffect(() => {
    if (parseError) return undefined;
    if (parsedDetail && phase >= phases.length - 1) {
      const t = setTimeout(() => onDone && onDone(parsedDetail), 450);
      return () => clearTimeout(t);
    }
    if (phase < phases.length - 1) {
      const t = setTimeout(() => setPhase((current) => Math.min(current + 1, phases.length - 1)), 850);
      return () => clearTimeout(t);
    }
    return undefined;
  }, [phase, parsedDetail, parseError]);

  const lines = window.PROGRAM_SAMPLE_LINES || [];

  return (
    <Screen padTop={64} padBottom={40} style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0 20px 14px' }}>
        <button onClick={onCancel} className="press" style={{
          width: 36, height: 36, borderRadius: 9999, background: 'var(--surface-1)',
          border: '1px solid var(--hairline)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="arrow-left" size={16} /></button>
      </div>

      {/* Tiny preview thumb of the captured page with a sweeping scan line. */}
      <div style={{ padding: '0 20px 24px', display: 'flex', justifyContent: 'center' }}>
        <div style={{
          width: 160, height: 200, borderRadius: 16,
          background: '#f4f1ea', position: 'relative', overflow: 'hidden',
          boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
          padding: 12, fontFamily: 'var(--font-mono)', fontSize: 7, color: '#444',
          lineHeight: 1.5,
        }}>
          {previewUrl ? (
            <img
              src={previewUrl}
              alt={file ? file.name : 'Program preview'}
              style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 8 }}
            />
          ) : (
            <>
              <div style={{ fontWeight: 700, fontSize: 8, marginBottom: 4 }}>
                {file ? file.name.slice(0, 24) : 'PROGRAM SOURCE'}
              </div>
              <div style={{ borderBottom: '1px solid #ccc', marginBottom: 4 }} />
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} style={{ marginBottom: 1 }}>
                  {(lines[i % Math.max(lines.length, 1)] || '').slice(0, 22)}
                </div>
              ))}
            </>
          )}
          <div className="scan-sweep" style={{
            position: 'absolute', left: 0, right: 0, height: 30,
            background: 'linear-gradient(180deg, transparent, rgba(197,242,62,0.6), transparent)',
            top: `${(phase + 1) * 22}%`, transition: 'top 600ms',
          }} />
        </div>
      </div>

      <div style={{ padding: '0 24px', textAlign: 'center', flex: 1 }}>
        <h1 style={{
          fontSize: 24, fontWeight: 600, letterSpacing: -0.4,
          margin: 0, marginBottom: 8,
        }}>Parsing your program</h1>
        <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, marginBottom: 28 }}>
          {file ? file.name : 'Waiting for a source file'}
        </p>

        <div style={{
          display: 'flex', flexDirection: 'column', gap: 8,
          maxWidth: 280, margin: '0 auto',
        }}>
          {phases.map((p, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '12px 14px', borderRadius: 14,
              background: i === phase ? 'rgba(197,242,62,0.06)' : 'transparent',
              border: '1px solid ' + (i === phase ? 'rgba(197,242,62,0.2)' : 'transparent'),
              transition: 'all 300ms',
            }}>
              <div style={{
                width: 18, height: 18, borderRadius: 9999,
                background: i < phase ? 'var(--accent)' : 'transparent',
                border: '1.5px solid ' + (i <= phase ? 'var(--accent)' : 'var(--text-dim)'),
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                position: 'relative', flexShrink: 0,
              }}>
                {i < phase && <Icon name="check" size={11} stroke="var(--on-accent)" strokeWidth={3} />}
                {i === phase && (
                  <div className="spin-ring" style={{
                    position: 'absolute', inset: -3, borderRadius: 9999,
                    border: '2px solid transparent', borderTopColor: 'var(--accent)',
                  }} />
                )}
              </div>
              <span style={{
                fontSize: 13, textAlign: 'left', flex: 1,
                color: i <= phase ? 'var(--text-1)' : 'var(--text-3)',
                fontWeight: i === phase ? 600 : 400,
              }}>{p}</span>
            </div>
          ))}
        </div>

        {parseError && (
          <div style={{
            margin: '20px auto 0', maxWidth: 280, padding: 14,
            borderRadius: 14, background: 'rgba(255,138,122,0.10)',
            border: '1px solid rgba(255,138,122,0.25)',
            color: '#FFB0A5', fontSize: 12, lineHeight: 1.4,
          }}>
            {parseError}
          </div>
        )}
      </div>

      <div style={{ padding: '0 24px', textAlign: 'center' }}>
        <p style={{
          fontSize: 11, color: 'var(--text-3)', margin: 0,
          fontFamily: 'var(--font-mono)',
        }}>PROCESSING THROUGH LOCAL FLASK INGESTION</p>
      </div>
    </Screen>
  );
};

// ─────────────────────────────────────────────────────────────
// 4. Review — confirm parsed program before saving.
// ─────────────────────────────────────────────────────────────
const ReviewScreen = ({ program, saving = false, error = null, onConfirm, onClose }) => {
  const source = program || window.PARSED_PROGRAM || {};
  const days = getProgramDays(source);
  const exercises = getProgramExercises(source);
  const setCount = getProgramSetCount(source);
  const initialName = source.name || 'Powerbuilding 5×';

  const [name, setName] = React.useState(initialName);
  const [editing, setEditing] = React.useState(false);
  const inputRef = React.useRef(null);

  React.useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  React.useEffect(() => {
    setName(initialName);
  }, [initialName]);

  return (
    <Screen padTop={64} padBottom={0} style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ padding: '0 20px 18px' }}>
        <div style={{
          fontSize: 12, color: 'var(--accent)', marginBottom: 6,
          fontFamily: 'var(--font-mono)', letterSpacing: 0.5,
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <Icon name="check" size={11} stroke="var(--accent)" strokeWidth={2.5} />
          PARSED · NAME IT
        </div>
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
          {days.length} days · {exercises.length} lifts · {setCount} sets
        </p>
      </div>

      <ProgramScheduleView source={source} />

      <div style={{
        padding: '14px 20px 24px',
        background: 'var(--bg)',
        borderTop: '1px solid var(--hairline)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant="ghost" onClick={onClose} disabled={saving} style={{ flex: 1 }}>Discard</Button>
          <Button onClick={() => onConfirm && onConfirm({ name })} iconRight="download" disabled={saving} style={{ flex: 2 }}>
            {saving ? 'Saving...' : 'Save program'}
          </Button>
        </div>
        {error && (
          <div style={{ color: '#FF8B7C', fontSize: 12, lineHeight: 1.35, marginTop: 10 }}>
            {error}
          </div>
        )}
      </div>
    </Screen>
  );
};

const ProgramScheduleView = ({ source }) => {
  const days = getProgramDays(source);

  if (!days.length) {
    return (
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '0 20px 20px' }}>
        <Card padding={18}>
          <div style={{ color: 'var(--text-2)', fontSize: 13, lineHeight: 1.45 }}>
            No exercises were returned for this program.
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="no-scrollbar" style={{
      flex: 1, minHeight: 0, overflowY: 'auto',
      padding: '0 20px 20px',
      display: 'flex', flexDirection: 'column', gap: 14,
    }}>
      {days.map((day, dayIndex) => (
        <DaySection key={day.id || dayIndex} day={day} dayIndex={dayIndex} />
      ))}
    </div>
  );
};

const DaySection = ({ day, dayIndex }) => {
  const blocks = day.blocks || [];
  const exercises = blocks.flatMap((block) => block.exercises || []);
  const setCount = exercises.reduce((sum, exercise) => sum + normalizeSetCount(exercise.sets), 0);

  return (
    <section style={{
      background: 'var(--surface-1)',
      border: '1px solid var(--hairline)',
      borderRadius: 'var(--r-card)',
      overflow: 'hidden',
      flexShrink: 0,
    }}>
      <div style={{
        padding: '14px 16px',
        background: 'var(--surface-2)',
        borderBottom: '1px solid var(--hairline)',
      }}>
        <div className="mono" style={{
          fontSize: 10, color: 'var(--accent)', letterSpacing: 0.5,
          textTransform: 'uppercase', marginBottom: 4,
        }}>
          Week {day.weekNumber || 1} · Day {dayIndex + 1}
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ fontSize: 17, fontWeight: 650, lineHeight: 1.2, minWidth: 0 }}>
            {day.title || `Day ${dayIndex + 1}`}
          </div>
          <div className="mono" style={{
            color: 'var(--text-3)', fontSize: 11, whiteSpace: 'nowrap', paddingTop: 2,
          }}>
            {exercises.length} lifts · {setCount} sets
          </div>
        </div>
        {day.notes && (
          <div style={{ marginTop: 8, color: 'var(--text-2)', fontSize: 12, lineHeight: 1.4 }}>
            {day.notes}
          </div>
        )}
      </div>

      {blocks.map((block, blockIndex) => (
        <BlockSection
          key={block.id || blockIndex}
          block={block}
          isLast={blockIndex === blocks.length - 1}
        />
      ))}
    </section>
  );
};

const BlockSection = ({ block, isLast }) => (
  <div style={{
    borderBottom: isLast ? 'none' : '1px solid var(--hairline)',
  }}>
    <div style={{
      padding: '11px 14px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10,
      background: 'rgba(197,242,62,0.045)',
      borderBottom: '1px solid var(--hairline)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        <Icon name="columns" size={13} stroke="var(--accent)" />
        <span style={{
          color: 'var(--text-1)', fontSize: 12.5, fontWeight: 700,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {block.title || 'Main'}
        </span>
      </div>
      {block.executionStyle && (
        <span className="mono" style={{
          fontSize: 9.5, color: 'var(--accent)', whiteSpace: 'nowrap',
          padding: '3px 7px', borderRadius: 999,
          border: '1px solid rgba(197,242,62,0.24)',
          background: 'rgba(197,242,62,0.08)',
        }}>
          {String(block.executionStyle).replace('_', ' ')}
        </span>
      )}
    </div>

    {(block.exercises || []).map((exercise, index) => (
      <MobileExerciseRow
        key={exercise.id || `${block.id}-${index}`}
        exercise={exercise}
        isLast={index === (block.exercises || []).length - 1}
      />
    ))}
  </div>
);

const MobileExerciseRow = ({ exercise, isLast }) => {
  const [open, setOpen] = React.useState(false);
  const hasNote = !!exercise.note;

  return (
    <div style={{
      borderBottom: isLast ? 'none' : '1px solid var(--hairline)',
      background: 'var(--surface-1)',
    }}>
      <button
        onClick={() => hasNote && setOpen(!open)}
        className={hasNote ? 'press' : ''}
        style={{
          width: '100%',
          padding: '13px 14px',
          background: 'transparent',
          border: 'none',
          color: 'var(--text-1)',
          textAlign: 'left',
          fontFamily: 'var(--font-sans)',
          cursor: hasNote ? 'pointer' : 'default',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{
              fontSize: 14.5, fontWeight: 600, lineHeight: 1.25,
              overflowWrap: 'anywhere',
            }}>
              {exercise.name}
            </div>
            <div style={{
              display: 'flex', gap: 6, flexWrap: 'wrap',
              marginTop: 9,
            }}>
              <MetricChip label="sets" value={exercise.sets} accent />
              <MetricChip label="reps" value={exercise.reps} />
              <MetricChip label="load" value={exercise.load} accent={exercise.load && exercise.load !== '-'} />
              {exercise.rest && exercise.rest !== '-' && <MetricChip label="rest" value={exercise.rest} />}
            </div>
          </div>
          {hasNote && (
            <Icon
              name="chevron-down"
              size={14}
              stroke="var(--text-3)"
              style={{ marginTop: 2, transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 180ms ease' }}
            />
          )}
        </div>
      </button>

      {hasNote && (
        <div style={{ maxHeight: open ? 180 : 0, overflow: 'hidden', transition: 'max-height 220ms ease' }}>
          <div style={{
            padding: '0 14px 14px',
            color: 'var(--text-2)',
            fontSize: 12,
            lineHeight: 1.45,
          }}>
            <div className="mono" style={{
              color: 'var(--text-3)', fontSize: 9, textTransform: 'uppercase',
              letterSpacing: 0.5, marginBottom: 5,
            }}>
              Notes
            </div>
            {exercise.note}
          </div>
        </div>
      )}
    </div>
  );
};

const MetricChip = ({ label, value, accent }) => (
  <span style={{
    minWidth: 0,
    maxWidth: '100%',
    display: 'inline-flex',
    alignItems: 'baseline',
    gap: 4,
    padding: '5px 7px',
    borderRadius: 9,
    background: accent ? 'rgba(197,242,62,0.10)' : 'var(--surface-2)',
    border: '1px solid ' + (accent ? 'rgba(197,242,62,0.22)' : 'var(--hairline)'),
  }}>
    <span className="mono" style={{
      color: accent ? 'var(--accent)' : 'var(--text-1)',
      fontSize: 12,
      fontWeight: 700,
      overflowWrap: 'anywhere',
    }}>
      {value || '-'}
    </span>
    <span className="mono" style={{
      color: 'var(--text-3)',
      fontSize: 8.5,
      textTransform: 'uppercase',
      letterSpacing: 0.35,
    }}>
      {label}
    </span>
  </span>
);

function getProgramDays(source) {
  if (Array.isArray(source.days)) return source.days;

  const exercises = Array.isArray(source.exercises) ? source.exercises : [];
  if (!exercises.length) return [];

  return [{
    id: 'day-1',
    title: source.name || 'Imported program',
    weekNumber: 1,
    blocks: [{
      id: 'main',
      title: 'Main',
      executionStyle: 'sequential',
      exercises,
    }],
  }];
}

function getProgramExercises(source) {
  if (Array.isArray(source.exercises)) return source.exercises;
  return getProgramDays(source).flatMap((day) =>
    (day.blocks || []).flatMap((block) => block.exercises || []),
  );
}

function getProgramSetCount(source) {
  if (typeof source.totalSets === 'number') return source.totalSets;
  return getProgramExercises(source).reduce((sum, exercise) => sum + normalizeSetCount(exercise.sets), 0);
}

function normalizeSetCount(value) {
  return typeof value === 'number' ? value : 0;
}

// ─────────────────────────────────────────────────────────────
// 5. Failed scan — when the parser couldn't read the source.
// ─────────────────────────────────────────────────────────────
const FailedScanScreen = ({ error, onRetry, onClose }) => (
  <Screen padTop={56} padBottom={40} style={{ display: 'flex', flexDirection: 'column' }}>
    <div style={{ padding: '0 20px 20px' }}>
      <button onClick={onClose} className="press" style={{
        width: 36, height: 36, borderRadius: 9999, background: 'var(--surface-1)',
        border: '1px solid var(--hairline)', color: 'var(--text-1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
      }}><Icon name="x" size={16} /></button>
    </div>

    <div style={{
      flex: 1, padding: '0 32px',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      textAlign: 'center',
    }}>
      <div style={{
        width: 64, height: 64, borderRadius: 32,
        background: 'rgba(255,138,122,0.10)',
        border: '1px solid rgba(255,138,122,0.25)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: 24,
        fontSize: 30, fontWeight: 700, color: '#FF8A7A', lineHeight: 1,
      }}>!</div>

      <h1 style={{
        fontSize: 24, fontWeight: 600, letterSpacing: -0.4,
        margin: 0, marginBottom: 10,
      }}>Couldn't read this one</h1>
      <p style={{
        fontSize: 14, color: 'var(--text-2)',
        margin: 0, lineHeight: 1.5, maxWidth: 280,
      }}>
        {error || "The image was too blurry or the format didn't match what we recognize. Try again with a clearer shot, or enter it manually."}
      </p>
    </div>

    <div style={{ padding: '20px 20px 0', display: 'flex', flexDirection: 'column', gap: 10 }}>
      <Button onClick={onRetry}>Try again</Button>
      <Button variant="ghost" onClick={onClose}>Back to home</Button>
    </div>
  </Screen>
);

Object.assign(window, {
  AddProgramScreen,
  CameraScreen,
  ParsingScreen,
  ReviewScreen,
  FailedScanScreen,
  ProgramScheduleView,
  getProgramDays,
  getProgramExercises,
  getProgramSetCount,
});
