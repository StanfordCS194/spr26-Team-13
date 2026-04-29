// App shell — placeholder until DesktopWindow + EntryScreen land.
// Once those exist this file becomes the 'entry' | 'parsing' | 'review' state machine.

export default function App() {
  return (
    <div style={{ padding: 40, color: 'var(--text-1)' }}>
      <h1 style={{ fontFamily: 'var(--font-sans)' }}>TrainAR · scaffold</h1>
      <p style={{ color: 'var(--text-2)' }}>
        Tokens loaded. Next up: window chrome and the Add Program entry screen.
      </p>
    </div>
  );
}
