import type { CSSProperties, ReactNode } from 'react';

interface PillProps {
  children: ReactNode;
  accent?: boolean;
  style?: CSSProperties;
}

export function Pill({ children, accent, style }: PillProps) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        height: 24,
        padding: '0 10px',
        borderRadius: 9999,
        fontSize: 11,
        fontWeight: 500,
        letterSpacing: 0.2,
        background: accent ? 'var(--accent-soft)' : 'var(--overlay-2)',
        color: accent ? 'var(--accent)' : 'var(--text-2)',
        border: '1px solid ' + (accent ? 'rgba(197,242,62,0.3)' : 'var(--hairline)'),
        ...style,
      }}
    >
      {children}
    </span>
  );
}
