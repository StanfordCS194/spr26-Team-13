# TrainAR · Desktop companion app

The companion-app UI for TrainAR. For tomorrow's demo this is the **Add Program** flow only:

1. **Entry** — drop a program file, browse via the native macOS Finder, or ⌘V a screenshot.
2. **Parsing** — preview of the file you uploaded, with a 4-phase animated progress.
3. **Review** — parsed program rendered as an editable-looking table.

Backend is **not** wired. The single seam for connecting a real parser later lives in
`src/lib/parseProgram.ts`. TS types in `src/lib/types.ts` mirror the Python contracts in
[../src/contracts/program.py](../src/contracts/program.py).

## Run

```bash
npm install
npm run dev          # http://localhost:5173 — fullscreen Chrome/Safari for the demo look
```

## File layout

```
src/
├── App.tsx                    # 'entry' | 'parsing' | 'review' state machine
├── main.tsx                   # ReactDOM root + token/global CSS imports
├── styles/
│   ├── tokens.css             # design tokens (dark + lime accent)
│   └── globals.css            # body resets + Inter / JetBrains Mono fonts
├── components/
│   ├── DesktopWindow.tsx      # 1240x800 dark window w/ traffic-light title bar
│   ├── Sidebar.tsx            # PLACEHOLDER — logo, nav, recent, glasses, profile
│   ├── ContentHeader.tsx      # title row + StepIndicator
│   ├── StepIndicator.tsx      # Source → Parse → Review pill row
│   └── ui/                    # Icon, Pill, Button primitives
├── screens/
│   ├── EntryScreen.tsx        # browse + drop + paste, all → onFileSelected(File)
│   ├── ParsingScreen.tsx      # split: real preview | progress + findings
│   └── ReviewScreen.tsx       # parsed program exercise table
├── lib/
│   ├── upload.ts              # ACCEPTED_INPUT_TYPES, classifyFile, formatBytes
│   ├── usePasteImage.ts       # ⌘V → File hook
│   ├── pdfPreview.ts          # pdfjs-dist page-1 → data URL
│   ├── parseProgram.ts        # mock async parser (returns sample.ts)
│   └── types.ts               # mirror of src/contracts/program.py
└── data/
    └── sample.ts              # hardcoded "Powerbuilding 5x" program
```

## Design source

This UI was built from the Claude Design handoff at
`/tmp/design2_extract/trainai/project/screens-desktop.jsx` — the four `Desktop*Screen`
components. Tokens were copied verbatim from `tokens.css` in that bundle.

Two intentional changes from the design:

- The "Open from Finder" placeholder screen is replaced by the **real** macOS Finder via
  `<input type="file">`. We don't recreate the fake Finder UI.
- The Parsing screen's "mock paper" placeholder is replaced by a **real preview** of the
  uploaded file (image via `URL.createObjectURL`, PDF via `pdfjs-dist`).
