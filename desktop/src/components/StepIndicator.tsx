// Source → Parse → Review pill row, ported from screens-desktop.jsx (lines 185-215).

import { Fragment } from 'react';
import { Icon } from './ui/Icon';

export type Step = 0 | 1 | 2;

interface StepIndicatorProps {
  step: Step;
}

export function StepIndicator({ step }: StepIndicatorProps) {
  const steps = [
    { id: 0, name: 'Source' },
    { id: 1, name: 'Parse' },
    { id: 2, name: 'Review' },
  ] as const;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      {steps.map((s, i) => (
        <Fragment key={s.id}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div
              style={{
                width: 22,
                height: 22,
                borderRadius: 9999,
                background: s.id <= step ? 'var(--accent)' : 'var(--surface-2)',
                border: '1px solid ' + (s.id <= step ? 'var(--accent)' : 'var(--hairline-2)'),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 11,
                fontWeight: 700,
                color: s.id <= step ? 'var(--on-accent)' : 'var(--text-3)',
              }}
            >
              {s.id < step ? (
                <Icon name="check" size={12} stroke="var(--on-accent)" strokeWidth={3} />
              ) : (
                s.id + 1
              )}
            </div>
            <div
              style={{
                fontSize: 12,
                color: s.id === step ? 'var(--text-1)' : 'var(--text-3)',
                fontWeight: s.id === step ? 600 : 500,
              }}
            >
              {s.name}
            </div>
          </div>
          {i < steps.length - 1 && (
            <div
              style={{
                width: 36,
                height: 1,
                background: i < step ? 'var(--accent)' : 'var(--hairline)',
              }}
            />
          )}
        </Fragment>
      ))}
    </div>
  );
}
