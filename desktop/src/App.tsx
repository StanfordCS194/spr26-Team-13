// 'entry' → 'parsing' → 'review' state machine.
// Backend is unwired: the selected File flows through to Parsing where it gets
// previewed and faux-processed. parseProgram() is a single mockable seam in
// lib/parseProgram.ts when real wiring lands.

import { useState } from 'react';
import { EntryScreen } from './screens/EntryScreen';
import { ParsingScreen } from './screens/ParsingScreen';

type Step = 'entry' | 'parsing' | 'review';

export default function App() {
  const [step, setStep] = useState<Step>('entry');
  const [file, setFile] = useState<File | null>(null);

  const handleFileSelected = (f: File) => {
    setFile(f);
    setStep('parsing');
  };

  if (step === 'entry') {
    return <EntryScreen onFileSelected={handleFileSelected} />;
  }
  if (step === 'parsing' && file) {
    return <ParsingScreen file={file} onDone={() => setStep('review')} />;
  }
  // Review screen lands in the next branch.
  return (
    <div style={{ padding: 40, color: 'var(--text-1)' }}>
      <h1 style={{ fontFamily: 'var(--font-sans)' }}>step: {step}</h1>
      <p style={{ color: 'var(--text-2)' }}>Stub — Review screen lands in app/desktop-add-program-review.</p>
      <button onClick={() => setStep('entry')}>Back to entry</button>
    </div>
  );
}
