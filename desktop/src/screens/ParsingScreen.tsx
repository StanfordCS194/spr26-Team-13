// "Parse" step of the Add Program flow.
// Ported from screens-desktop.jsx DesktopParsingScreen (lines 617-785).
//
// Two intentional swaps from the design:
//   - The mock paper preview is replaced with a real preview of the uploaded file.
//     Images render via URL.createObjectURL; PDFs render page 1 via pdfjs-dist;
//     spreadsheets/unknowns fall back to a centered "Preview unavailable" card.
//   - The phase animation is driven locally while the real Docling + Gemini
//     ingestion request runs through lib/parseProgram.ts.

import { useEffect, useMemo, useState } from 'react';
import { ContentHeader } from '../components/ContentHeader';
import { DesktopWindow } from '../components/DesktopWindow';
import type { SidebarNavId } from '../components/Sidebar';
import { Icon } from '../components/ui/Icon';
import { parseProgram, type ParseProgramResult } from '../lib/parseProgram';
import { renderPdfFirstPage } from '../lib/pdfPreview';
import type { TrainingProgram } from '../lib/types';
import { classifyFile, formatBytes, type FileKind } from '../lib/upload';

const PHASES = [
  'Reading the page',
  'Identifying structure',
  'Mapping workouts',
  'Building schedule',
] as const;

const PHASE_INTERVAL_MS = 700;

interface ParsingScreenProps {
  file: File;
  onCancel: () => void;
  onDone: (result: ParseProgramResult) => void;
  onNavigate?: (id: SidebarNavId) => void;
}

export function ParsingScreen({ file, onCancel, onDone, onNavigate }: ParsingScreenProps) {
  const kind: FileKind = useMemo(() => classifyFile(file), [file]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [phase, setPhase] = useState(0);
  const [parseResult, setParseResult] = useState<ParseProgramResult | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const stats = parseResult ? summarizeProgram(parseResult.program) : null;

  // Build the preview URL (image / pdf / fallback).
  useEffect(() => {
    let cancelled = false;
    let revokable: string | null = null;

    async function build() {
      if (kind === 'image') {
        const url = URL.createObjectURL(file);
        revokable = url;
        if (!cancelled) setPreviewUrl(url);
        return;
      }
      if (kind === 'pdf') {
        try {
          const { dataUrl } = await renderPdfFirstPage(file);
          if (!cancelled) setPreviewUrl(dataUrl);
        } catch (err) {
          if (!cancelled) setPreviewError(err instanceof Error ? err.message : 'PDF preview failed');
        }
        return;
      }
      // sheet/unknown: leave previewUrl null and let the fallback render.
    }

    build();
    return () => {
      cancelled = true;
      if (revokable) URL.revokeObjectURL(revokable);
    };
  }, [file, kind]);

  // Send the file through the real ingestion flow.
  useEffect(() => {
    const controller = new AbortController();

    parseProgram(file, { signal: controller.signal })
      .then(setParseResult)
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        setParseError(err instanceof Error ? err.message : 'Program parsing failed.');
      });

    return () => controller.abort();
  }, [file]);

  // Drive the phase animation while the backend is working. Once the request is
  // complete and the last phase is visible, advance to Review.
  useEffect(() => {
    if (parseError) return;
    if (parseResult && phase >= PHASES.length - 1) {
      const doneResult = parseResult;
      const doneTimer = setTimeout(() => onDone(doneResult), 600);
      return () => clearTimeout(doneTimer);
    }
    if (phase < PHASES.length - 1) {
      const t = setTimeout(() => setPhase((p) => Math.min(p + 1, PHASES.length - 1)), PHASE_INTERVAL_MS);
      return () => clearTimeout(t);
    }
    return undefined;
  }, [parseError, parseResult, phase, onDone]);

  return (
    <DesktopWindow active="add" title="Parsing" onNavigate={onNavigate}>
      <ContentHeader
        step={1}
        title="Parsing your program"
        subtitle="Hang tight — we're reading the page and matching it to known workouts."
      />
      <div style={{ padding: 36, display: 'flex', gap: 24, height: 'calc(100% - 100px)' }}>
        {/* Left — source preview */}
        <div
          style={{
            flex: 1,
            borderRadius: 16,
            overflow: 'hidden',
            background: 'var(--surface-1)',
            border: '1px solid var(--hairline)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid var(--hairline)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
              <Icon name="file" size={14} stroke="var(--text-2)" />
              <span
                style={{
                  fontSize: 12,
                  color: 'var(--text-2)',
                  fontWeight: 500,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={file.name}
              >
                {file.name}
              </span>
              <span className="mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>
                · {formatBytes(file.size)}
              </span>
              {kind === 'pdf' && (
                <span
                  className="mono"
                  style={{
                    fontSize: 10,
                    color: 'var(--accent)',
                    background: 'var(--accent-soft)',
                    border: '1px solid rgba(197,242,62,0.3)',
                    padding: '2px 8px',
                    borderRadius: 9999,
                    marginLeft: 6,
                    flexShrink: 0,
                  }}
                >
                  Page 1
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: 4 }}>
              {(['minus', 'plus', 'maximize'] as const).map((b) => (
                <button
                  key={b}
                  type="button"
                  style={{
                    width: 26,
                    height: 26,
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
                  <Icon name={b} size={14} />
                </button>
              ))}
            </div>
          </div>
          <div
            style={{
              flex: 1,
              padding: 28,
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background:
                'repeating-linear-gradient(45deg, rgba(255,255,255,0.015) 0 12px, rgba(255,255,255,0.025) 12px 24px)',
              overflow: 'hidden',
            }}
          >
            {previewUrl ? (
              <>
                <img
                  src={previewUrl}
                  alt={file.name}
                  style={{
                    maxWidth: '100%',
                    maxHeight: '100%',
                    width: 'auto',
                    height: 'auto',
                    objectFit: 'contain',
                    borderRadius: 8,
                    boxShadow: '0 16px 48px rgba(0,0,0,0.4)',
                    background: '#fff',
                  }}
                />
                {/* Lime scan-sweep overlay */}
                <div
                  className="scan-sweep"
                  style={{
                    position: 'absolute',
                    left: 28,
                    right: 28,
                    height: 40,
                    top: '40%',
                    background:
                      'linear-gradient(180deg, transparent, rgba(197,242,62,0.4), transparent)',
                    pointerEvents: 'none',
                  }}
                />
              </>
            ) : (
              <PreviewFallback file={file} kind={kind} error={previewError} />
            )}
          </div>
        </div>

        {/* Right — progress + findings */}
        <div style={{ width: 380, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Phases */}
          <div
            style={{
              borderRadius: 16,
              padding: 20,
              background: 'var(--surface-1)',
              border: '1px solid var(--hairline)',
            }}
          >
            <div
              style={{
                fontSize: 11,
                color: 'var(--text-3)',
                textTransform: 'uppercase',
                letterSpacing: 0.8,
                fontWeight: 600,
                marginBottom: 14,
              }}
            >
              Progress
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {PHASES.map((label, i) => {
                const done = Boolean(parseResult) || i < phase;
                const active = !parseResult && !parseError && i === phase;
                const failed = Boolean(parseError) && i === phase;
                return (
                  <div key={label} style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                    <div
                      style={{
                        width: 22,
                        height: 22,
                        borderRadius: 9999,
                        flexShrink: 0,
                        background: done
                          ? 'var(--accent)'
                          : active
                            ? 'transparent'
                            : failed
                              ? 'rgba(255,107,92,0.12)'
                            : 'var(--surface-2)',
                        border:
                          '1.5px solid ' +
                          (done
                            ? 'var(--accent)'
                            : active
                              ? 'var(--accent)'
                              : failed
                                ? 'var(--danger)'
                                : 'var(--hairline-2)'),
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        position: 'relative',
                      }}
                    >
                      {done && (
                        <Icon name="check" size={12} stroke="var(--on-accent)" strokeWidth={3} />
                      )}
                      {active && (
                        <div
                          className="spin-ring"
                          style={{
                            position: 'absolute',
                            inset: -2,
                            borderRadius: '50%',
                            border: '2px solid transparent',
                            borderTopColor: 'var(--accent)',
                          }}
                        />
                      )}
                      {failed && <Icon name="alert" size={12} stroke="var(--danger)" strokeWidth={2.4} />}
                    </div>
                    <div style={{ flex: 1, paddingTop: 1 }}>
                      <div
                        style={{
                          fontSize: 13.5,
                          fontWeight: 600,
                          color: done || active || failed ? 'var(--text-1)' : 'var(--text-3)',
                        }}
                      >
                        {label}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Live findings */}
          <div
            style={{
              borderRadius: 16,
              padding: 20,
              background: parseError ? 'var(--surface-1)' : 'var(--hero-bg)',
              border: parseError ? '1px solid rgba(255,107,92,0.24)' : '1px solid var(--hero-border)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                fontSize: 11,
                color: parseError ? 'var(--danger)' : 'var(--accent)',
                textTransform: 'uppercase',
                letterSpacing: 0.8,
                fontWeight: 600,
                marginBottom: 12,
              }}
            >
              {parseError ? 'Needs attention' : 'What we found'}
            </div>
            <div style={{ fontSize: 22, fontWeight: 600, letterSpacing: -0.4, marginBottom: 4 }}>
              {parseError ? 'Parsing failed' : parseResult?.program.title ?? 'Docling + Gemini'}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 16 }}>
              {parseError
                ? parseError
                : parseResult?.extracted_preview?.normalization_mode
                  ? `normalized with ${parseResult.extracted_preview.normalization_mode}`
                  : 'extracting document structure'}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
              {[
                { v: stats?.days ?? '–', l: 'Days' },
                { v: stats?.exercises ?? '–', l: 'Workouts' },
                { v: stats?.sets ?? '–', l: 'Sets' },
              ].map((s) => (
                <div
                  key={s.l}
                  style={{
                    padding: 12,
                    borderRadius: 10,
                    background: 'var(--overlay-1)',
                    border: '1px solid var(--hairline)',
                    textAlign: 'center',
                  }}
                >
                  <div
                    className="mono"
                    style={{
                      fontSize: 22,
                      fontWeight: 600,
                      color: parseError ? 'var(--danger)' : 'var(--accent)',
                    }}
                  >
                    {s.v}
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: 'var(--text-3)',
                      textTransform: 'uppercase',
                      letterSpacing: 0.4,
                      marginTop: 2,
                    }}
                  >
                    {s.l}
                  </div>
                </div>
              ))}
            </div>
            {parseError && (
              <button
                type="button"
                onClick={onCancel}
                className="press"
                style={{
                  marginTop: 16,
                  background: 'var(--surface-2)',
                  color: 'var(--text-1)',
                  border: '1px solid var(--hairline-2)',
                  padding: '9px 14px',
                  borderRadius: 9999,
                  fontSize: 12.5,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <Icon name="arrow-left" size={13} />
                Choose another file
              </button>
            )}
          </div>
        </div>
      </div>
    </DesktopWindow>
  );
}

function summarizeProgram(program: TrainingProgram) {
  const days = program.weeks.flatMap((week) => week.days);
  const exercises = days.flatMap((day) => day.exercises ?? []);

  return {
    days: days.length,
    exercises: exercises.length,
    sets: exercises.reduce((sum, exercise) => sum + exercise.set_count, 0),
  };
}

// ─────────────────────────────────────────────────────────────
// Fallback preview card for spreadsheets / unknown types / pdf-render errors.
// ─────────────────────────────────────────────────────────────
interface PreviewFallbackProps {
  file: File;
  kind: FileKind;
  error: string | null;
}

function PreviewFallback({ file, kind, error }: PreviewFallbackProps) {
  const label =
    kind === 'sheet'
      ? 'Preview unavailable for spreadsheets'
      : kind === 'pdf'
        ? 'PDF preview unavailable'
        : 'Preview unavailable for this file type';
  const sub =
    error
      ? error
      : kind === 'sheet'
        ? "Full data lands in the parsed table on the next step."
        : 'The parser will still process this file.';
  const glyph: 'image' | 'file' = kind === 'sheet' ? 'file' : 'file';
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 10,
        textAlign: 'center',
        maxWidth: 360,
      }}
    >
      <div
        style={{
          width: 72,
          height: 72,
          borderRadius: 16,
          background: 'var(--surface-2)',
          border: '1px solid var(--hairline)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Icon name={glyph} size={32} stroke="var(--text-2)" />
      </div>
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-1)' }}>{label}</div>
      <div style={{ fontSize: 12.5, color: 'var(--text-3)' }}>{sub}</div>
      <div className="mono" style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 6 }}>
        {file.name} · {formatBytes(file.size)}
      </div>
    </div>
  );
}
