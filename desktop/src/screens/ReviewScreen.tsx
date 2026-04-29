// "Review" step of the Add Program flow.
// Ported from screens-desktop.jsx DesktopReviewScreen (lines 790-906).

import { ContentHeader } from '../components/ContentHeader';
import { DesktopWindow } from '../components/DesktopWindow';
import { Icon } from '../components/ui/Icon';
import { sampleProgram } from '../data/sample';

interface ReviewScreenProps {
  onSave: () => void;
}

export function ReviewScreen({ onSave }: ReviewScreenProps) {
  const day = sampleProgram.weeks[0]?.days[0];
  const exercises = day?.exercises ?? [];
  const totalSets = exercises.reduce((sum, ex) => sum + ex.set_count, 0);

  return (
    <DesktopWindow active="add" title="Review">
      <ContentHeader
        step={2}
        title="Review parsed program"
        subtitle={`${exercises.length} workouts, ${totalSets} sets across the day. Edit anything that looks off, then send to your glasses.`}
        right={
          <button
            type="button"
            onClick={onSave}
            className="press"
            style={{
              background: 'var(--accent)',
              color: 'var(--on-accent)',
              border: 'none',
              padding: '10px 18px',
              borderRadius: 9999,
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              whiteSpace: 'nowrap',
            }}
          >
            Save &amp; sync to glasses
            <Icon name="arrow-right" size={14} stroke="var(--on-accent)" strokeWidth={2.2} />
          </button>
        }
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

        {/* Table */}
        <div
          style={{
            borderRadius: 14,
            overflow: 'hidden',
            background: 'var(--surface-1)',
            border: '1px solid var(--hairline)',
          }}
        >
          {/* Header row */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '2.2fr 0.5fr 0.7fr 0.9fr 2.4fr 36px',
              padding: '10px 16px',
              gap: 12,
              background: 'var(--surface-2)',
              borderBottom: '1px solid var(--hairline)',
              fontSize: 10.5,
              color: 'var(--text-3)',
              textTransform: 'uppercase',
              letterSpacing: 0.6,
              fontWeight: 700,
            }}
          >
            <div>Workout</div>
            <div>Sets</div>
            <div>Reps</div>
            <div>Weight</div>
            <div>Notes</div>
            <div></div>
          </div>
          {exercises.map((ex, i) => (
            <div
              key={ex.exercise_id}
              style={{
                display: 'grid',
                gridTemplateColumns: '2.2fr 0.5fr 0.7fr 0.9fr 2.4fr 36px',
                padding: '14px 16px',
                gap: 12,
                alignItems: 'center',
                borderBottom: i < exercises.length - 1 ? '1px solid var(--hairline)' : 'none',
                fontSize: 13,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 8,
                    background: 'var(--accent-soft)',
                    border: '1px solid rgba(197,242,62,0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 11,
                    fontWeight: 700,
                    color: 'var(--accent)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {i + 1}
                </div>
                <div style={{ fontWeight: 600 }}>{ex.display_name}</div>
              </div>
              <div className="mono" style={{ color: 'var(--text-1)' }}>
                {ex.set_count}
              </div>
              <div className="mono" style={{ color: 'var(--text-1)' }}>
                {ex.rep_target ?? '—'}
              </div>
              <div className="mono" style={{ color: 'var(--text-1)' }}>
                {ex.load_target ?? '—'}
              </div>
              <div
                style={{
                  fontSize: 12.5,
                  color: ex.notes ? 'var(--text-2)' : 'var(--text-3)',
                  fontStyle: ex.notes ? 'normal' : 'italic',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {ex.notes || 'Add a note…'}
              </div>
              <button
                type="button"
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 6,
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-3)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Icon name="more-horizontal" size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </DesktopWindow>
  );
}
