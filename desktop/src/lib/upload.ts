// Helpers for the EntryScreen file pickers.

export const ACCEPTED_INPUT_TYPES = 'image/*,application/pdf,.csv,.xlsx,.xls';

export type FileKind = 'image' | 'pdf' | 'sheet' | 'unknown';

export function classifyFile(file: File): FileKind {
  if (file.type.startsWith('image/')) return 'image';
  if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) return 'pdf';
  if (
    file.type === 'application/vnd.ms-excel' ||
    file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
    file.type === 'text/csv' ||
    /\.(xlsx?|csv)$/i.test(file.name)
  ) {
    return 'sheet';
  }
  return 'unknown';
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
