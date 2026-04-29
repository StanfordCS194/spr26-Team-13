// 'entry' → 'parsing' → 'review' state machine.
// Backend is unwired: the selected File flows through Parsing where it gets
// previewed and faux-processed; Review reads its rows from data/sample.ts.
// parseProgram() in lib/parseProgram.ts is the single seam for real wiring.

import { useState } from 'react';
import { EntryScreen } from './screens/EntryScreen';
import { ParsingScreen } from './screens/ParsingScreen';
import { ReviewScreen } from './screens/ReviewScreen';

type Step = 'entry' | 'parsing' | 'review';

export default function App() {
  const [step, setStep] = useState<Step>('entry');
  const [file, setFile] = useState<File | null>(null);

  const handleFileSelected = (f: File) => {
    setFile(f);
    setStep('parsing');
  };

  const handleSave = () => {
    // Save & sync to glasses is a no-op for the demo. Reset for the next take.
    setFile(null);
    setStep('entry');
  };

  if (step === 'entry') {
    return <EntryScreen onFileSelected={handleFileSelected} />;
  }
  if (step === 'parsing' && file) {
    return <ParsingScreen file={file} onDone={() => setStep('review')} />;
  }
  if (step === 'review') {
    return <ReviewScreen onSave={handleSave} />;
  }
  return null;
}
