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

Object.assign(window, { AddProgramScreen });
