// Add-program flow screens: Entry → Camera → Parsing → Review.
//
// Frontend only. The camera screen draws chrome over a placeholder where the
// camera feed will eventually render; parsing runs on a fake timer; review
// reads from window.PARSED_PROGRAM. Backend swaps these in later.

// Reuses the Screen wrapper defined in screens-signup.jsx.

// ─────────────────────────────────────────────────────────────
// 1. Entry — pick a source.
// ─────────────────────────────────────────────────────────────
const AddProgramScreen = ({ onCamera, onUpload, onLibrary, onClose }) => (
  <Screen padTop={64} padBottom={32}>
    <div style={{
      padding: '0 20px 16px', display: 'flex',
      alignItems: 'center', justifyContent: 'space-between',
    }}>
      <div>
        <h1 style={{ fontSize: 26, fontWeight: 600, letterSpacing: -0.5, margin: 0 }}>
          Add a program
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, marginTop: 4 }}>
          Drop in any program. We'll parse and structure it.
        </p>
      </div>
      <button onClick={onClose} className="press" style={{
        width: 36, height: 36, borderRadius: 9999, background: 'var(--surface-1)',
        border: '1px solid var(--hairline)', color: 'var(--text-1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
      }}><Icon name="x" size={16} /></button>
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
          position: 'absolute', top: -30, right: -30, width: 120, height: 120,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(197,242,62,0.2), transparent 60%)',
        }} />
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
      <button onClick={onUpload} className="press" style={{
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

      {/* Browse community */}
      <button onClick={onLibrary} className="press" style={{
        padding: 18, borderRadius: 'var(--r-card)',
        background: 'transparent', border: '1px dashed var(--hairline-2)',
        color: 'var(--text-2)', textAlign: 'left', cursor: 'pointer',
        fontFamily: 'var(--font-sans)',
        display: 'flex', alignItems: 'center', gap: 14,
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10, background: 'transparent',
          border: '1px solid var(--hairline)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon name="sparkle" size={18} stroke="var(--text-2)" />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-1)' }}>
            Browse community programs
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>
            5/3/1, nSuns, PPL, Starting Strength…
          </div>
        </div>
        <Icon name="chevron-right" size={16} stroke="var(--text-3)" />
      </button>
    </div>
  </Screen>
);

// ─────────────────────────────────────────────────────────────
// 2. Camera — UI over a real camera view.
//
// The big rotated "paper" rectangle in the middle is a placeholder for
// the camera feed. When the backend wires up a real camera, swap the
// paper div for a <video> element bound to getUserMedia (or whatever
// they end up using). The rest of the chrome — close, flash, reticles,
// hint pill, capture button — stays the same.
// ─────────────────────────────────────────────────────────────
const CameraScreen = ({ onCapture, onClose }) => {
  const lines = window.PROGRAM_SAMPLE_LINES || [];
  return (
    <Screen padTop={0} padBottom={0} style={{
      display: 'flex', flexDirection: 'column', background: '#000',
    }}>
      {/* Viewfinder area — the placeholder lives in here. */}
      <div style={{
        flex: 1, position: 'relative',
        background: 'linear-gradient(180deg, #1a1a1a, #0a0a0a)',
        overflow: 'hidden',
      }}>
        {/* Placeholder for the camera feed — fake "paper" page. */}
        <div style={{
          position: 'absolute', top: 80, left: 30, right: 30, bottom: 120,
          background: '#f4f1ea', borderRadius: 4, padding: 16,
          transform: 'rotate(-2.4deg)',
          boxShadow: '0 30px 60px rgba(0,0,0,0.6)',
          fontFamily: 'var(--font-mono)', fontSize: 9, color: '#3a3a3a',
          lineHeight: 1.6, overflow: 'hidden',
        }}>
          <div style={{ fontWeight: 700, fontSize: 11, marginBottom: 6 }}>
            WEEK 3 — FULL BODY 1
          </div>
          <div style={{ borderBottom: '1px solid #ccc', marginBottom: 6 }} />
          {lines.map((l, i) => <div key={i}>{l}</div>)}
        </div>

        {/* Corner reticles framing the program region. */}
        {[[40, 40], [40, 'auto', 'auto', 40], ['auto', 40, 40, 'auto'], ['auto', 'auto', 40, 40]].map((c, i) => (
          <div key={i} style={{
            position: 'absolute',
            top: c[0], right: c[1], bottom: c[2], left: c[3],
            width: 28, height: 28,
            borderTop:    c[0] !== 'auto' ? '2px solid var(--accent)' : 'none',
            borderBottom: c[2] !== 'auto' ? '2px solid var(--accent)' : 'none',
            borderLeft:   c[3] !== 'auto' ? '2px solid var(--accent)' : 'none',
            borderRight:  c[1] !== 'auto' ? '2px solid var(--accent)' : 'none',
            borderTopLeftRadius:     c[0] !== 'auto' && c[3] !== 'auto' ? 8 : 0,
            borderTopRightRadius:    c[0] !== 'auto' && c[1] !== 'auto' ? 8 : 0,
            borderBottomLeftRadius:  c[2] !== 'auto' && c[3] !== 'auto' ? 8 : 0,
            borderBottomRightRadius: c[2] !== 'auto' && c[1] !== 'auto' ? 8 : 0,
          }} />
        ))}

        {/* AI hint pill. */}
        <div style={{
          position: 'absolute', top: 70, left: 0, right: 0,
          display: 'flex', justifyContent: 'center',
        }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '8px 14px', borderRadius: 9999,
            background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: '1px solid rgba(197,242,62,0.3)',
            color: 'var(--accent)', fontSize: 12, fontWeight: 600,
          }}>
            <Icon name="sparkle" size={14} stroke="var(--accent)" />
            Program detected — hold steady
          </div>
        </div>

        {/* Top close + flash. */}
        <button onClick={onClose} className="press" style={{
          position: 'absolute', top: 60, left: 20,
          width: 40, height: 40, borderRadius: 9999,
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)',
          border: '1px solid rgba(255,255,255,0.15)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="x" size={18} /></button>
        <button className="press" style={{
          position: 'absolute', top: 60, right: 20,
          width: 40, height: 40, borderRadius: 9999,
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)',
          border: '1px solid rgba(255,255,255,0.15)', color: 'var(--text-1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><Icon name="flash" size={18} /></button>
      </div>

      {/* Bottom controls — gallery, capture, flip. */}
      <div style={{
        padding: '24px 20px 36px', background: '#000',
        display: 'flex', alignItems: 'center', justifyContent: 'space-around',
      }}>
        <button className="press" style={{
          width: 52, height: 52, borderRadius: 14,
          background: 'var(--surface-2)', border: '1px solid var(--hairline)',
          color: 'var(--text-1)', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}><Icon name="image" size={20} /></button>

        <button onClick={onCapture} className="press" style={{
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

        <button className="press" style={{
          width: 52, height: 52, borderRadius: 14,
          background: 'var(--surface-2)', border: '1px solid var(--hairline)',
          color: 'var(--text-1)', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}><Icon name="rotate" size={20} /></button>
      </div>
    </Screen>
  );
};

Object.assign(window, { AddProgramScreen, CameraScreen });
