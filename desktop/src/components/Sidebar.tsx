// PLACEHOLDER — sidebar chrome ported from screens-desktop.jsx (lines 65-170).
// None of the rows are wired: clicking does nothing, the glasses card is static,
// and recent programs are sample strings. Real wiring lands when other surfaces
// (Train, Programs, History) get built.

import { Icon, type IconName } from './ui/Icon';

interface NavItem {
  id: string;
  icon: IconName;
  label: string;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'home', icon: 'flame', label: 'Train' },
  { id: 'programs', icon: 'dumbbell', label: 'Programs' },
  { id: 'add', icon: 'plus', label: 'Add program' },
  { id: 'history', icon: 'calendar', label: 'History', badge: '42' },
];

const RECENT = [
  { name: 'Powerbuilding 5x', dot: 'var(--accent)' },
  { name: 'Push/Pull/Legs', dot: 'rgba(255,255,255,0.3)' },
  { name: 'Strong Curves', dot: 'rgba(255,255,255,0.3)' },
];

interface SidebarProps {
  active?: string;
}

export function Sidebar({ active = 'add' }: SidebarProps) {
  return (
    <div
      style={{
        width: 240,
        flexShrink: 0,
        background: 'var(--surface-1)',
        borderRight: '1px solid var(--hairline)',
        display: 'flex',
        flexDirection: 'column',
        padding: '20px 12px',
      }}
    >
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '4px 12px 24px' }}>
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 8,
            background: 'var(--accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--on-accent)' }} />
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: -0.2 }}>TrainAR</div>
      </div>

      <div
        style={{
          fontSize: 10,
          color: 'var(--text-3)',
          textTransform: 'uppercase',
          letterSpacing: 0.8,
          padding: '8px 12px 6px',
          fontWeight: 600,
        }}
      >
        Workspace
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {NAV_ITEMS.map((item) => {
          const sel = item.id === active;
          return (
            <div
              key={item.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 12px',
                borderRadius: 8,
                cursor: 'pointer',
                background: sel ? 'var(--surface-3)' : 'transparent',
                color: sel ? 'var(--text-1)' : 'var(--text-2)',
                fontSize: 13.5,
                fontWeight: sel ? 600 : 500,
              }}
            >
              <Icon name={item.icon} size={16} stroke={sel ? 'var(--accent)' : 'var(--text-2)'} />
              <span>{item.label}</span>
              {item.badge && (
                <span
                  className="mono"
                  style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-3)' }}
                >
                  {item.badge}
                </span>
              )}
            </div>
          );
        })}
      </div>

      <div
        style={{
          fontSize: 10,
          color: 'var(--text-3)',
          textTransform: 'uppercase',
          letterSpacing: 0.8,
          padding: '24px 12px 6px',
          fontWeight: 600,
        }}
      >
        Recent
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {RECENT.map((p) => (
          <div
            key={p.name}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '7px 12px',
              borderRadius: 8,
              cursor: 'pointer',
              color: 'var(--text-2)',
              fontSize: 13,
            }}
          >
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: 3,
                background: p.dot,
                flexShrink: 0,
              }}
            />
            <span
              style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {p.name}
            </span>
          </div>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      {/* Glasses status pill — placeholder copy */}
      <div
        style={{
          margin: '0 4px 4px',
          padding: 12,
          borderRadius: 10,
          background: 'var(--surface-2)',
          border: '1px solid var(--hairline)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <div
            className="pulse-dot"
            style={{ width: 7, height: 7, borderRadius: 4, background: 'var(--accent)' }}
          />
          <div
            style={{
              fontSize: 11,
              color: 'var(--accent)',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: 0.4,
            }}
          >
            Connected
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600 }}>TrainAR · M2</div>
            <div className="mono" style={{ fontSize: 10, color: 'var(--text-3)' }}>
              Battery 78%
            </div>
          </div>
          <Icon name="glasses" size={20} stroke="var(--text-2)" />
        </div>
      </div>

      {/* Profile — placeholder */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: 8,
          borderRadius: 8,
          cursor: 'pointer',
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--accent), #6FA31D)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 12,
            fontWeight: 700,
            color: 'var(--on-accent)',
          }}
        >
          A
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            Alex Carter
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-3)' }}>alex@stanford.edu</div>
        </div>
      </div>
    </div>
  );
}
