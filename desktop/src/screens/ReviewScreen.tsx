// "Review" step of the Add Program flow.
// Ported from screens-desktop.jsx DesktopReviewScreen (lines 790-906).

import { ContentHeader } from '../components/ContentHeader';
import { DesktopWindow } from '../components/DesktopWindow';
import { Icon } from '../components/ui/Icon';
import { sampleProgram } from '../data/sample';

interface ReviewScreenProps {
  onSave: () => void;
}

export function ReviewScreen(_props: ReviewScreenProps) {
  const day = sampleProgram.weeks[0]?.days[0];

  return (
    <DesktopWindow active="add" title="Review">
      <ContentHeader
        step={2}
        title="Review parsed program"
        subtitle="Edit anything that looks off, then send to your glasses."
      />
      <div style={{ padding: 36 }}>
        {/* Day header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 16,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 11,
                color: 'var(--text-3)',
                textTransform: 'uppercase',
                letterSpacing: 0.8,
                fontWeight: 600,
              }}
            >
              Day 1
            </div>
            <div style={{ fontSize: 22, fontWeight: 600, letterSpacing: -0.4, marginTop: 2 }}>
              {day?.title ?? 'Heavy Push'}
            </div>
          </div>
          <button
            type="button"
            style={{
              background: 'var(--surface-2)',
              border: '1px solid var(--hairline)',
              color: 'var(--text-2)',
              borderRadius: 8,
              padding: '6px 12px',
              fontSize: 12,
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <Icon name="plus" size={12} />
            Add workout
          </button>
        </div>
      </div>
    </DesktopWindow>
  );
}
