// Title row that sits above each step's body, ported from screens-desktop.jsx (lines 220-235).

import type { ReactNode } from 'react';
import { StepIndicator, type Step } from './StepIndicator';

interface ContentHeaderProps {
  title: string;
  subtitle: string;
  step: Step;
  right?: ReactNode;
}

export function ContentHeader({ title, subtitle, step, right }: ContentHeaderProps) {
  return (
    <div
      style={{
        padding: '24px 36px 20px',
        borderBottom: '1px solid var(--hairline)',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        gap: 20,
      }}
    >
      <div>
        <h1
          style={{
            fontSize: 28,
            fontWeight: 600,
            letterSpacing: -0.6,
            margin: 0,
            marginBottom: 4,
          }}
        >
          {title}
        </h1>
        <div style={{ fontSize: 14, color: 'var(--text-2)' }}>{subtitle}</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        {right}
        <StepIndicator step={step} />
      </div>
    </div>
  );
}
