// 1240x800 dark window with traffic-light title bar + sidebar slot + content slot.
// Ported from screens-desktop.jsx (DesktopWindow, lines 30-180, plus TrafficLights 16-25).

import type { ReactNode } from 'react';
import { Sidebar, type SidebarNavId } from './Sidebar';

export const DT_W = 1240;
export const DT_H = 800;

function TrafficLights() {
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => (
        <div
          key={c}
          style={{
            width: 12,
            height: 12,
            borderRadius: 9999,
            background: c,
            boxShadow: 'inset 0 0 0 0.5px rgba(0,0,0,0.2)',
          }}
        />
      ))}
    </div>
  );
}

interface DesktopWindowProps {
  title?: string;
  active?: string;
  onNavigate?: (id: SidebarNavId) => void;
  children: ReactNode;
}

export function DesktopWindow({
  title = 'Add a program',
  active = 'add',
  onNavigate,
  children,
}: DesktopWindowProps) {
  return (
    <div
      style={{
        width: DT_W,
        height: DT_H,
        borderRadius: 14,
        overflow: 'hidden',
        background: 'var(--bg)',
        boxShadow:
          '0 0 0 1px rgba(255,255,255,0.06), 0 30px 80px rgba(0,0,0,0.5), 0 12px 32px rgba(0,0,0,0.4)',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: 'var(--font-sans)',
        color: 'var(--text-1)',
      }}
    >
      {/* Title bar */}
      <div
        style={{
          height: 44,
          display: 'flex',
          alignItems: 'center',
          background: 'var(--surface-1)',
          borderBottom: '1px solid var(--hairline)',
          paddingLeft: 16,
          paddingRight: 16,
          gap: 16,
          flexShrink: 0,
        }}
      >
        <TrafficLights />
        <div
          style={{
            flex: 1,
            textAlign: 'center',
            fontSize: 13,
            color: 'var(--text-2)',
            fontWeight: 500,
          }}
        >
          TrainAR · {title}
        </div>
        <div style={{ width: 60 }} />
      </div>

      {/* Body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <Sidebar active={active} onNavigate={onNavigate} />
        <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>{children}</div>
      </div>
    </div>
  );
}
