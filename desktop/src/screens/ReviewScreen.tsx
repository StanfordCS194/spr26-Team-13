// "Review" step of the Add Program flow.
// Renders the canonical TrainingProgram returned by the ingestion API, including
// all weeks, all days, named blocks, and unassigned exercises.

import { ContentHeader } from '../components/ContentHeader';
import { DesktopWindow } from '../components/DesktopWindow';
import type { SidebarNavId } from '../components/Sidebar';
import { Icon } from '../components/ui/Icon';
import type { ReactNode } from 'react';
import type { ProgramExercise, TrainingBlock, TrainingDay, TrainingProgram } from '../lib/types';

interface ReviewScreenProps {
  program: TrainingProgram;
  onSave: () => void;
  onNavigate?: (id: SidebarNavId) => void;
}

interface DayRef {
  weekNumber: number;
  day: TrainingDay;
}

interface ExerciseGroup {
  id: string;
  title: string;
  executionStyle?: TrainingBlock['execution_style'];
  exercises: ProgramExercise[];
}

export function ReviewScreen({ program, onSave, onNavigate }: ReviewScreenProps) {
  const days = program.weeks.flatMap((week) =>
    week.days.map((day) => ({ weekNumber: week.week_number, day })),
  );
  const totalExercises = days.reduce((sum, dayRef) => sum + getDayDisplayExercises(dayRef.day).length, 0);
  const totalSets = days.reduce(
    (sum, dayRef) =>
      sum + getDayDisplayExercises(dayRef.day).reduce((daySum, ex) => daySum + ex.set_count, 0),
    0,
  );

  return (
    <DesktopWindow active="add" title="Review" onNavigate={onNavigate}>
      <ContentHeader
        step={2}
        title="Review parsed program"
        subtitle={`${program.title} · ${days.length} days, ${totalExercises} workouts, ${totalSets} sets. Edit anything that looks off, then send to your glasses.`}
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
      <div style={{ padding: 28, display: 'flex', flexDirection: 'column', gap: 20 }}>
        {days.map((dayRef, dayIndex) => (
          <DayReviewCard
            key={`${dayRef.weekNumber}-${dayRef.day.day_id}-${dayIndex}`}
            dayRef={dayRef}
            dayIndex={dayIndex}
          />
        ))}
      </div>
    </DesktopWindow>
  );
}

function DayReviewCard({ dayRef, dayIndex }: { dayRef: DayRef; dayIndex: number }) {
  const groups = getDayGroups(dayRef.day);
  const exercises = groups.flatMap((group) => group.exercises);
  const setCount = exercises.reduce((sum, ex) => sum + ex.set_count, 0);
  let rowNumber = 0;

  return (
    <section
      style={{
        borderRadius: 14,
        overflow: 'hidden',
        background: 'var(--surface-1)',
        border: '1px solid var(--hairline)',
      }}
    >
      <div
        style={{
          padding: '16px 18px',
          borderBottom: '1px solid var(--hairline)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16,
        }}
      >
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontSize: 11,
              color: 'var(--text-3)',
              textTransform: 'uppercase',
              letterSpacing: 0.8,
              fontWeight: 600,
              marginBottom: 3,
            }}
          >
            Week {dayRef.weekNumber} · Day {dayIndex + 1}
          </div>
          <div style={{ fontSize: 20, fontWeight: 600, letterSpacing: -0.2 }}>
            {dayRef.day.title}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
          <StatChip value={groups.length} label={groups.length === 1 ? 'block' : 'blocks'} />
          <StatChip value={exercises.length} label="workouts" />
          <StatChip value={setCount} label="sets" />
        </div>
      </div>

      <ExerciseTable>
        {groups.length === 0 ? (
          <EmptyRow />
        ) : (
          groups.map((group, groupIndex) => (
            <div key={group.id}>
              {(groups.length > 1 || group.title !== 'Main') && (
                <BlockHeader group={group} isFirst={groupIndex === 0} />
              )}
              {group.exercises.map((exercise, exerciseIndex) => {
                rowNumber += 1;
                return (
                  <ExerciseRow
                    key={`${group.id}-${exercise.exercise_id}-${exerciseIndex}`}
                    exercise={exercise}
                    index={rowNumber}
                    isLast={groupIndex === groups.length - 1 && exerciseIndex === group.exercises.length - 1}
                  />
                );
              })}
            </div>
          ))
        )}
      </ExerciseTable>
    </section>
  );
}

function ExerciseTable({ children }: { children: ReactNode }) {
  return (
    <div>
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
        <div />
      </div>
      {children}
    </div>
  );
}

function BlockHeader({ group, isFirst }: { group: ExerciseGroup; isFirst: boolean }) {
  return (
    <div
      style={{
        padding: '10px 16px',
        background: 'rgba(197,242,62,0.06)',
        borderTop: isFirst ? 'none' : '1px solid var(--hairline)',
        borderBottom: '1px solid var(--hairline)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        <Icon name="columns" size={13} stroke="var(--accent)" />
        <span style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--text-1)' }}>
          {group.title}
        </span>
      </div>
      {group.executionStyle && (
        <span
          className="mono"
          style={{
            fontSize: 10.5,
            color: 'var(--accent)',
            border: '1px solid rgba(197,242,62,0.24)',
            borderRadius: 9999,
            padding: '3px 8px',
            background: 'rgba(197,242,62,0.08)',
          }}
        >
          {group.executionStyle.replace('_', ' ')}
        </span>
      )}
    </div>
  );
}

function ExerciseRow({
  exercise,
  index,
  isLast,
}: {
  exercise: ProgramExercise;
  index: number;
  isLast: boolean;
}) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '2.2fr 0.5fr 0.7fr 0.9fr 2.4fr 36px',
        padding: '14px 16px',
        gap: 12,
        alignItems: 'center',
        borderBottom: isLast ? 'none' : '1px solid var(--hairline)',
        fontSize: 13,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
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
            flexShrink: 0,
          }}
        >
          {index}
        </div>
        <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {exercise.display_name}
        </div>
      </div>
      <div className="mono" style={{ color: 'var(--text-1)' }}>
        {exercise.set_count}
      </div>
      <div className="mono" style={{ color: 'var(--text-1)' }}>
        {exercise.rep_target ?? '—'}
      </div>
      <div className="mono" style={{ color: 'var(--text-1)' }}>
        {exercise.load_target ?? '—'}
      </div>
      <div
        style={{
          fontSize: 12.5,
          color: exercise.notes ? 'var(--text-2)' : 'var(--text-3)',
          fontStyle: exercise.notes ? 'normal' : 'italic',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {exercise.notes || 'Add a note...'}
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
  );
}

function EmptyRow() {
  return (
    <div style={{ padding: 18, color: 'var(--text-3)', fontSize: 13 }}>
      No exercises were returned for this day.
    </div>
  );
}

function StatChip({ value, label }: { value: number; label: string }) {
  return (
    <div
      style={{
        borderRadius: 9999,
        border: '1px solid var(--hairline)',
        background: 'var(--surface-2)',
        padding: '5px 9px',
        fontSize: 11,
        color: 'var(--text-2)',
        whiteSpace: 'nowrap',
      }}
    >
      <span className="mono" style={{ color: 'var(--text-1)', fontWeight: 600 }}>
        {value}
      </span>{' '}
      {label}
    </div>
  );
}

function getDayGroups(day: TrainingDay): ExerciseGroup[] {
  const blockGroups: ExerciseGroup[] =
    day.blocks
      ?.filter((block) => block.exercises.length > 0)
      .map((block) => ({
        id: block.block_id,
        title: block.title,
        executionStyle: block.execution_style,
        exercises: block.exercises,
      })) ?? [];

  const ungrouped = getUngroupedExercises(day);
  if (ungrouped.length > 0) {
    blockGroups.push({
      id: `${day.day_id}-ungrouped`,
      title: blockGroups.length > 0 ? 'Unassigned Section' : 'Main',
      exercises: ungrouped,
    });
  }

  return blockGroups;
}

function getDayDisplayExercises(day: TrainingDay): ProgramExercise[] {
  return getDayGroups(day).flatMap((group) => group.exercises);
}

function getUngroupedExercises(day: TrainingDay): ProgramExercise[] {
  const blocks = day.blocks ?? [];
  if (blocks.length === 0) return day.exercises ?? [];

  const remainingBlockKeys = blocks.flatMap((block) => block.exercises.map(getExerciseKey));
  const ungrouped: ProgramExercise[] = [];

  for (const exercise of day.exercises ?? []) {
    const key = getExerciseKey(exercise);
    const index = remainingBlockKeys.indexOf(key);
    if (index >= 0) {
      remainingBlockKeys.splice(index, 1);
      continue;
    }
    ungrouped.push(exercise);
  }

  return ungrouped;
}

function getExerciseKey(exercise: ProgramExercise): string {
  return JSON.stringify([
    exercise.exercise_id,
    exercise.display_name,
    exercise.set_count,
    exercise.rep_target ?? null,
    exercise.load_target ?? null,
    exercise.rpe_target ?? null,
    exercise.rest_seconds ?? null,
    exercise.notes ?? null,
    exercise.ambiguity_flags,
  ]);
}
