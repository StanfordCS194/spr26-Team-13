// 'entry' → 'parsing' → 'review' state machine.
// Backend is unwired: the selected File is the only thing that flows between screens.

import { useState } from 'react';
import { EntryScreen } from './screens/EntryScreen';

type Step = 'entry' | 'parsing' | 'review';

export default function App() {
  const [step, setStep] = useState<Step>('entry');
  const [, setFile] = useState<File | null>(null);

  const handleFileSelected = (f: File) => {
    setFile(f);
    setStep('parsing');
  };

  if (step === 'entry') {
    return <EntryScreen onFileSelected={handleFileSelected} />;
  }
  // Parsing + Review screens land in subsequent commits/branches.
  return (
    <div style={{ padding: 40, color: 'var(--text-1)' }}>
      <h1 style={{ fontFamily: 'var(--font-sans)' }}>step: {step}</h1>
      <p style={{ color: 'var(--text-2)' }}>Stub — Parsing/Review screens land in next branches.</p>
      <button onClick={() => setStep('entry')}>Back to entry</button>
    </div>
  );
}
