// Render the first page of a PDF File to a data URL using pdfjs-dist.
// Lazy-imported so the ~200KB pdfjs bundle only loads when a PDF is uploaded.

export interface PdfPreviewResult {
  dataUrl: string;
  width: number;
  height: number;
}

export async function renderPdfFirstPage(file: File, targetWidth = 800): Promise<PdfPreviewResult> {
  // Lazy import — keeps the entry-screen bundle slim.
  const pdfjs = await import('pdfjs-dist');

  // pdfjs needs a worker URL set once. Resolve via Vite ?url; fall back to CDN.
  if (!pdfjs.GlobalWorkerOptions.workerSrc) {
    try {
      const workerUrl = (await import('pdfjs-dist/build/pdf.worker.min.mjs?url')).default;
      pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
    } catch {
      pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
    }
  }

  const buf = await file.arrayBuffer();
  const doc = await pdfjs.getDocument({ data: buf }).promise;
  const page = await doc.getPage(1);

  const viewport1x = page.getViewport({ scale: 1 });
  const scale = targetWidth / viewport1x.width;
  const viewport = page.getViewport({ scale });

  const canvas = document.createElement('canvas');
  canvas.width = Math.ceil(viewport.width);
  canvas.height = Math.ceil(viewport.height);
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('PDF preview: could not get canvas 2d context');

  await page.render({ canvasContext: ctx, viewport, canvas }).promise;

  return {
    dataUrl: canvas.toDataURL('image/png'),
    width: canvas.width,
    height: canvas.height,
  };
}
