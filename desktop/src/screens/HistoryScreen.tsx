import { useMemo, useState } from 'react';
import { DesktopWindow } from '../components/DesktopWindow';
import type { SidebarNavId } from '../components/Sidebar';
import { Icon } from '../components/ui/Icon';
import { completedSessions, type CompletedSession, type LoggedSet } from '../data/history';

interface HistoryScreenProps {
  onNavigate?: (id: SidebarNavId) => void;
}

export function HistoryScreen({ onNavigate }: HistoryScreenProps) {
  const [selectedId, setSelectedId] = useState(completedSessions[0]?.id);
  const selected = useMemo(
    () => completedSessions.find((session) => session.id === selectedId) ?? completedSessions[0],
    [selectedId],
  );

  return (
    <DesktopWindow active="history" title="History" onNavigate={onNavigate}>
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
            Workout history
          </h1>
          <div style={{ fontSize: 14, color: 'var(--text-2)' }}>
            Completed sessions with logged sets, loads, RPE, notes, and volume.
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <SummaryPill label="Sessions" value={completedSessions.length.toString()} />
          <SummaryPill
            label="Avg complete"
            value={`${Math.round(
              completedSessions.reduce((sum, session) => sum + session.completion, 0) /
                completedSessions.length,
            )}%`}
          />
        </div>
      </div>

      <div
        style={{
          padding: 28,
          display: 'grid',
          gridTemplateColumns: '300px 1fr',
          gap: 20,
          minHeight: 'calc(100% - 96px)',
        }}
      >
        <SessionList selectedId={selected?.id} onSelect={setSelectedId} />
        {selected && <SessionDetail session={selected} />}
      </div>
    </DesktopWindow>
  );
}

function SessionList({
  selectedId,
  onSelect,
}: {
  selectedId?: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div
      style={{
        borderRadius: 14,
        background: 'var(--surface-1)',
        border: '1px solid var(--hairline)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '12px 14px',
          borderBottom: '1px solid var(--hairline)',
          color: 'var(--text-3)',
          textTransform: 'uppercase',
          letterSpacing: 0.7,
          fontSize: 10.5,
          fontWeight: 700,
        }}
      >
        Recent completed
      </div>
      {completedSessions.map((session) => {
        const selected = session.id === selectedId;
        return (
          <button
            key={session.id}
            type="button"
            onClick={() => onSelect(session.id)}
            style={{
              width: '100%',
              border: 'none',
              borderBottom: '1px solid var(--hairline)',
              background: selected ? 'var(--surface-3)' : 'transparent',
              color: 'var(--text-1)',
              fontFamily: 'var(--font-sans)',
              textAlign: 'left',
              padding: 14,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
              <div style={{ fontSize: 14, fontWeight: 650 }}>{session.title}</div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>
                {session.date}
              </div>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-2)' }}>{session.program}</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <MiniMetric value={session.duration} />
              <MiniMetric value={session.volume} />
              <MiniMetric value={`${session.completion}%`} />
            </div>
          </button>
        );
      })}
    </div>
  );
}

function SessionDetail({ session }: { session: CompletedSession }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0 }}>
      <div
        style={{
          borderRadius: 14,
          background: 'var(--surface-1)',
          border: '1px solid var(--hairline)',
          padding: 18,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 20, marginBottom: 16 }}>
          <div>
            <div
              style={{
                color: 'var(--text-3)',
                textTransform: 'uppercase',
                letterSpacing: 0.7,
                fontSize: 10.5,
                fontWeight: 700,
                marginBottom: 4,
              }}
            >
              {session.date} completed
            </div>
            <div style={{ fontSize: 24, fontWeight: 650, letterSpacing: -0.3 }}>{session.title}</div>
            <div style={{ color: 'var(--text-2)', fontSize: 13, marginTop: 3 }}>{session.program}</div>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <SummaryTile label="Duration" value={session.duration} icon="clock" />
            <SummaryTile label="Volume" value={session.volume} icon="dumbbell" />
            <SummaryTile label="Complete" value={`${session.completion}%`} icon="check" />
            <SummaryTile label="PRs" value={session.prCount.toString()} icon="trophy" />
          </div>
        </div>
        <div
          style={{
            borderRadius: 10,
            background: 'var(--surface-2)',
            border: '1px solid var(--hairline)',
            padding: '10px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <Icon name="bolt" size={15} stroke="var(--accent)" />
          <div style={{ fontSize: 13, color: 'var(--text-2)' }}>
            Readiness: <span style={{ color: 'var(--text-1)', fontWeight: 600 }}>{session.readiness}</span>
            <span style={{ color: 'var(--text-3)' }}> - {session.notes}</span>
          </div>
        </div>
      </div>

      {session.exercises.map((exercise) => (
        <div
          key={exercise.id}
          style={{
            borderRadius: 14,
            background: 'var(--surface-1)',
            border: '1px solid var(--hairline)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '13px 16px',
              borderBottom: '1px solid var(--hairline)',
              display: 'flex',
              justifyContent: 'space-between',
              gap: 12,
            }}
          >
            <div>
              <div style={{ fontSize: 15, fontWeight: 650 }}>{exercise.name}</div>
              <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>
                Planned: {exercise.planned}
              </div>
            </div>
            <MiniMetric value={`${exercise.sets.length} sets`} />
          </div>
          <LoggedSetTable sets={exercise.sets} />
        </div>
      ))}
    </div>
  );
}

function LoggedSetTable({ sets }: { sets: LoggedSet[] }) {
  return (
    <div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '0.45fr 0.9fr 0.8fr 0.85fr 0.6fr 0.9fr 1.5fr',
          gap: 10,
          padding: '9px 16px',
          background: 'var(--surface-2)',
          borderBottom: '1px solid var(--hairline)',
          color: 'var(--text-3)',
          textTransform: 'uppercase',
          letterSpacing: 0.55,
          fontSize: 10.5,
          fontWeight: 700,
        }}
      >
        <div>Set</div>
        <div>Target</div>
        <div>Actual</div>
        <div>Load</div>
        <div>RPE</div>
        <div>Status</div>
        <div>Notes</div>
      </div>
      {sets.map((set, index) => (
        <div
          key={set.set}
          style={{
            display: 'grid',
            gridTemplateColumns: '0.45fr 0.9fr 0.8fr 0.85fr 0.6fr 0.9fr 1.5fr',
            gap: 10,
            padding: '11px 16px',
            borderBottom: index < sets.length - 1 ? '1px solid var(--hairline)' : 'none',
            alignItems: 'center',
            fontSize: 13,
          }}
        >
          <div className="mono" style={{ color: 'var(--text-2)' }}>
            {set.set}
          </div>
          <div className="mono">{set.target ?? '-'}</div>
          <div className="mono">{set.reps}</div>
          <div className="mono">{set.load ?? '-'}</div>
          <div className="mono">{set.rpe ?? '-'}</div>
          <StatusPill status={set.status ?? 'complete'} />
          <div
            style={{
              color: set.note ? 'var(--text-2)' : 'var(--text-3)',
              fontStyle: set.note ? 'normal' : 'italic',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {set.note ?? 'No note'}
          </div>
        </div>
      ))}
    </div>
  );
}

function SummaryTile({ label, value, icon }: { label: string; value: string; icon: 'clock' | 'dumbbell' | 'check' | 'trophy' }) {
  return (
    <div
      style={{
        minWidth: 84,
        borderRadius: 10,
        background: 'var(--surface-2)',
        border: '1px solid var(--hairline)',
        padding: '9px 10px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-3)', marginBottom: 5 }}>
        <Icon name={icon} size={12} />
        <span style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: 0.4 }}>{label}</span>
      </div>
      <div className="mono" style={{ fontSize: 15, fontWeight: 650 }}>
        {value}
      </div>
    </div>
  );
}

function SummaryPill({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        borderRadius: 9999,
        border: '1px solid var(--hairline)',
        background: 'var(--surface-1)',
        padding: '7px 11px',
        display: 'flex',
        gap: 7,
        alignItems: 'center',
      }}
    >
      <span className="mono" style={{ color: 'var(--accent)', fontWeight: 650, fontSize: 13 }}>
        {value}
      </span>
      <span style={{ color: 'var(--text-3)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.4 }}>
        {label}
      </span>
    </div>
  );
}

function MiniMetric({ value }: { value: string }) {
  return (
    <span
      className="mono"
      style={{
        fontSize: 10.5,
        color: 'var(--text-2)',
        background: 'var(--surface-2)',
        border: '1px solid var(--hairline)',
        borderRadius: 9999,
        padding: '3px 7px',
        whiteSpace: 'nowrap',
      }}
    >
      {value}
    </span>
  );
}

function StatusPill({ status }: { status: LoggedSet['status'] }) {
  const color =
    status === 'complete' ? 'var(--accent)' : status === 'modified' ? 'var(--warn)' : 'var(--danger)';

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        color,
        fontSize: 12,
        fontWeight: 600,
        textTransform: 'capitalize',
      }}
    >
      <span style={{ width: 6, height: 6, borderRadius: 9999, background: color }} />
      {status}
    </div>
  );
}
