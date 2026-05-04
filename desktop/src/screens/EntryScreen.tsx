// Add Program entry screen — the "Source" step.
// Ported from screens-desktop.jsx DesktopEntryScreen (lines 240-347), with the design's
// `<button>Browse files</button>` replaced by a real <input type="file"> trigger and
// the dropzone wired for drag-and-drop + paste-screenshot via App's onFileSelected.

import { useRef, useState } from 'react';
import type { DragEvent } from 'react';
import { ContentHeader } from '../components/ContentHeader';
import { DesktopWindow } from '../components/DesktopWindow';
import type { SidebarNavId } from '../components/Sidebar';
import { Icon } from '../components/ui/Icon';
import { ACCEPTED_INPUT_TYPES } from '../lib/upload';
import { usePasteImage } from '../lib/usePasteImage';

interface EntryScreenProps {
  onFileSelected: (file: File) => void;
  onNavigate?: (id: SidebarNavId) => void;
}

export function EntryScreen({ onFileSelected, onNavigate }: EntryScreenProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  // ⌘V anywhere on the page — pastes a screenshot from clipboard.
  usePasteImage(onFileSelected);

  const handleBrowse = () => inputRef.current?.click();

  const handleFiles = (files: FileList | null | undefined) => {
    if (!files || files.length === 0) return;
    onFileSelected(files[0]);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <DesktopWindow active="add" title="Add a program" onNavigate={onNavigate}>
      <ContentHeader
        step={0}
        title="Add a program"
        subtitle="Drop a photo, PDF, or spreadsheet — TrainAR parses it into structured workouts your glasses can follow."
      />
      <div style={{ padding: '32px 36px' }}>
        {/* Hidden native file input — opens real macOS Finder via inputRef.current?.click() */}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_INPUT_TYPES}
          onChange={(e) => handleFiles(e.target.files)}
          style={{ display: 'none' }}
        />

        {/* Drop zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            height: 320,
            borderRadius: 20,
            border: isDragging
              ? '2px dashed var(--accent)'
              : '2px dashed var(--hairline-2)',
            background: isDragging ? 'var(--accent-soft)' : 'var(--surface-1)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            position: 'relative',
            overflow: 'hidden',
            transition: 'border-color 160ms, background 160ms',
          }}
        >
          {/* Soft lime glow */}
          <div
            style={{
              position: 'absolute',
              width: 280,
              height: 280,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(197,242,62,0.10), transparent 60%)',
              pointerEvents: 'none',
            }}
          />
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: 20,
              background: 'var(--accent-soft)',
              border: '1px solid rgba(197,242,62,0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
            }}
          >
            <Icon name="upload" size={32} stroke="var(--accent)" strokeWidth={1.8} />
          </div>
          <div style={{ textAlign: 'center', position: 'relative' }}>
            <div style={{ fontSize: 20, fontWeight: 600, marginBottom: 6 }}>
              {isDragging ? 'Release to upload' : 'Drop your program here'}
            </div>
            <div style={{ fontSize: 14, color: 'var(--text-2)' }}>
              JPG, PNG, HEIC, PDF, XLSX, CSV — up to 25 MB
            </div>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginTop: 4,
              position: 'relative',
            }}
          >
            <button
              type="button"
              onClick={handleBrowse}
              className="press"
              style={{
                background: 'var(--accent)',
                color: 'var(--on-accent)',
                border: 'none',
                padding: '10px 20px',
                borderRadius: 9999,
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Icon name="folder" size={14} stroke="var(--on-accent)" strokeWidth={2} />
              Browse files
            </button>
            <span style={{ fontSize: 12, color: 'var(--text-3)' }}>
              or paste a screenshot ⌘V
            </span>
          </div>
        </div>

        {/* Alternative actions — placeholders */}
        <div style={{ marginTop: 28 }}>
          <div
            style={{
              fontSize: 11,
              color: 'var(--text-3)',
              textTransform: 'uppercase',
              letterSpacing: 0.8,
              fontWeight: 600,
              marginBottom: 12,
            }}
          >
            Or start another way
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 12,
            }}
          >
            {[
              { icon: 'sparkle' as const, label: 'Browse templates', sub: 'Curated programs from coaches' },
              { icon: 'mail' as const, label: 'Forward an email', sub: 'Send to programs@trainar.app' },
            ].map((a) => (
              <button
                key={a.label}
                type="button"
                className="press"
                style={{
                  background: 'var(--surface-1)',
                  border: '1px solid var(--hairline)',
                  borderRadius: 14,
                  padding: 18,
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontFamily: 'var(--font-sans)',
                  color: 'var(--text-1)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                }}
              >
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: 'var(--surface-3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Icon name={a.icon} size={18} stroke="var(--text-1)" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 2 }}>{a.label}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{a.sub}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Recently parsed — placeholder chips */}
        <div style={{ marginTop: 36 }}>
          <div
            style={{
              fontSize: 11,
              color: 'var(--text-3)',
              textTransform: 'uppercase',
              letterSpacing: 0.8,
              fontWeight: 600,
              marginBottom: 12,
            }}
          >
            Recently parsed
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {[
              'Powerbuilding 5x · Jeff Nippard',
              'Push/Pull/Legs · 6 weeks',
              'Strong Curves · phase 2',
            ].map((label) => (
              <div
                key={label}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 14px',
                  borderRadius: 9999,
                  background: 'var(--surface-1)',
                  border: '1px solid var(--hairline)',
                  fontSize: 12.5,
                  color: 'var(--text-2)',
                  cursor: 'pointer',
                }}
              >
                <Icon name="file" size={12} stroke="var(--text-3)" />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DesktopWindow>
  );
}
