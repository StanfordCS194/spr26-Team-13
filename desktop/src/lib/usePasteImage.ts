// Listen for ⌘V at the document level. When the clipboard carries an image
// (e.g. macOS Shift+Ctrl+Cmd+4 screenshot), wrap it as a File and call onImage.

import { useEffect } from 'react';

export function usePasteImage(onImage: (file: File) => void) {
  useEffect(() => {
    const handler = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.kind === 'file' && item.type.startsWith('image/')) {
          const blob = item.getAsFile();
          if (!blob) continue;
          // Pasted screenshots land as 'image/png' with empty .name; give them
          // a stable filename so downstream UI shows something useful.
          const ext = (item.type.split('/')[1] || 'png').toLowerCase();
          const name = blob.name && blob.name.length > 0
            ? blob.name
            : `pasted-screenshot-${Date.now()}.${ext}`;
          const file = new File([blob], name, { type: item.type });
          e.preventDefault();
          onImage(file);
          return;
        }
      }
    };
    document.addEventListener('paste', handler);
    return () => document.removeEventListener('paste', handler);
  }, [onImage]);
}
