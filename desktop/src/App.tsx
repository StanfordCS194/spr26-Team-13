// 'entry' → 'parsing' → 'review' state machine.
// The selected File flows through Parsing where it is previewed locally and sent
// through lib/parseProgram.ts to the Flask Docling + Gemini ingestion API.

import { useState } from 'react';
import { EntryScreen } from './screens/EntryScreen';
import { HistoryScreen } from './screens/HistoryScreen';
import { ParsingScreen } from './screens/ParsingScreen';
import { ReviewScreen } from './screens/ReviewScreen';
import type { SidebarNavId } from './components/Sidebar';
import type { TrainingProgram } from './lib/types';

type Step = 'entry' | 'parsing' | 'review' | 'history';

export default function App() {
  const [step, setStep] = useState<Step>('entry');
  const [file, setFile] = useState<File | null>(null);
  const [program, setProgram] = useState<TrainingProgram | null>(null);

  const handleFileSelected = (f: File) => {
    setFile(f);
    setProgram(null);
    setStep('parsing');
  };

  const handleSave = () => {
    // Save & sync to glasses is a no-op for the demo. Reset for the next take.
    setFile(null);
    setProgram(null);
    setStep('entry');
  };

  const handleNavigate = (id: SidebarNavId) => {
    if (id === 'history') {
      setStep('history');
      return;
    }
    if (id === 'add') {
      setFile(null);
      setProgram(null);
      setStep('entry');
    }
  };

  if (step === 'entry') {
    return <EntryScreen onFileSelected={handleFileSelected} onNavigate={handleNavigate} />;
  }
  if (step === 'parsing' && file) {
    return (
      <ParsingScreen
        file={file}
        onCancel={() => setStep('entry')}
        onNavigate={handleNavigate}
        onDone={(result) => {
          setProgram(result.program);
          setStep('review');
        }}
      />
    );
  }
  if (step === 'review' && program) {
    return <ReviewScreen program={program} onSave={handleSave} onNavigate={handleNavigate} />;
  }
  if (step === 'history') {
    return <HistoryScreen onNavigate={handleNavigate} />;
  }
  return null;
}
