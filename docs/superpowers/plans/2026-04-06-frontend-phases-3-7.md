# Frontend Phases 3–7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the anatomy view redesign, chat panel, KG improvements, quick wins, and polish as described in `docs/superpowers/specs/2026-04-06-frontend-phases-3-7-design.md`, decomposing `PaperPage.tsx` from a 700-line monolith into focused components.

**Architecture:** Incremental layering — Phase 3 quick wins first, then Phase 4 anatomy redesign (the core, replaces Summary + Walkthrough tabs), then Phase 5 KG improvements, Phase 6 chat panel, and finally Phase 7 polish wired into `PaperPage.tsx`. All new components live under `frontend/src/components/paper/`.

**Tech Stack:** React 18, TypeScript, MUI v5, Vitest + @testing-library/react (jsdom), Axios, D3 v7.

---

## File Map

**Create:**
- `frontend/src/test-setup.ts` — Vitest + @testing-library/jest-dom bootstrap
- `frontend/src/components/library/ConfirmDialog.tsx` — reusable confirm dialog
- `frontend/src/components/paper/anatomy/ProblemSection.tsx`
- `frontend/src/components/paper/anatomy/PriorArtSection.tsx`
- `frontend/src/components/paper/anatomy/IdeaSection.tsx`
- `frontend/src/components/paper/anatomy/MethodSection.tsx`
- `frontend/src/components/paper/anatomy/EvidenceSection.tsx`
- `frontend/src/components/paper/anatomy/VerdictSection.tsx`
- `frontend/src/components/paper/anatomy/TakeawaysSection.tsx`
- `frontend/src/components/paper/anatomy/AnatomyView.tsx`
- `frontend/src/components/paper/PaperAtAGlance.tsx`
- `frontend/src/components/paper/CritiqueIndicator.tsx`
- `frontend/src/components/paper/WorkspaceHeader.tsx`
- `frontend/src/components/paper/TermGlossary.tsx`
- `frontend/src/components/paper/ChatPanel.tsx`
- `frontend/src/components/paper/__tests__/FormulaBlock.test.tsx`
- `frontend/src/components/paper/__tests__/CritiqueIndicator.test.tsx`
- `frontend/src/components/paper/__tests__/TermGlossary.test.tsx`
- `frontend/src/components/paper/__tests__/ChatPanel.test.tsx`
- `frontend/src/components/paper/__tests__/WorkspaceHeader.test.tsx`

**Modify:**
- `frontend/vite.config.ts` — add vitest `test` block
- `frontend/package.json` — add `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`
- `frontend/src/services/api.ts` — add `papersAPI.delete`
- `frontend/src/components/library/PaperCard.tsx` — add delete button + confirm dialog
- `frontend/src/components/paper/FormulaBlock.tsx` — add `intuition`, `prerequisites`, `where_it_appears`
- `frontend/src/components/paper/KnowledgeGraphViz.tsx` — improve D3 tooltip with category chip styling; add click-to-pin
- `frontend/src/pages/PaperPage.tsx` — restructure to orchestrator using all new components

---

## Task 0: Test infrastructure

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.ts`
- Create: `frontend/src/test-setup.ts`

- [ ] **Step 1: Install test dependencies**

```bash
cd frontend
npm install --legacy-peer-deps --save-dev @testing-library/react@^14 @testing-library/jest-dom@^6 @testing-library/user-event@^14
```

- [ ] **Step 2: Configure vitest in vite.config.ts**

Replace the full contents of `frontend/vite.config.ts` with:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
  },
})
```

- [ ] **Step 3: Create test-setup.ts**

```ts
// frontend/src/test-setup.ts
import '@testing-library/jest-dom';
```

- [ ] **Step 4: Verify tests run (no tests yet, just check config)**

```bash
cd frontend && npm test -- --run
```

Expected: `No test files found` or `0 tests passed` — no errors about config.

- [ ] **Step 5: Commit**

```bash
cd frontend && git add package.json package-lock.json vite.config.ts src/test-setup.ts
git commit -m "test: set up vitest with @testing-library/react and jsdom"
```

---

## Task 1: papersAPI.delete

**Files:**
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Add `delete` to `papersAPI` in `api.ts`**

After the `reformat` method (line ~180) inside `papersAPI`, add:

```ts
  delete: async (paperId: string, token: string): Promise<void> => {
    await api.delete(`/papers/${paperId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat: add papersAPI.delete to api client"
```

---

## Task 2: Delete button on PaperCard

**Files:**
- Create: `frontend/src/components/library/ConfirmDialog.tsx`
- Modify: `frontend/src/components/library/PaperCard.tsx`

- [ ] **Step 1: Create ConfirmDialog**

```tsx
// frontend/src/components/library/ConfirmDialog.tsx
import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button } from '@mui/material';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open, title, message, confirmLabel = 'Confirm', onConfirm, onCancel, loading = false,
}) => (
  <Dialog open={open} onClose={onCancel} PaperProps={{ sx: { borderRadius: 4, p: 1 } }}>
    <DialogTitle sx={{ fontWeight: 700 }}>{title}</DialogTitle>
    <DialogContent>
      <DialogContentText>{message}</DialogContentText>
    </DialogContent>
    <DialogActions sx={{ px: 3, pb: 2 }}>
      <Button onClick={onCancel} disabled={loading}>Cancel</Button>
      <Button onClick={onConfirm} variant="contained" color="error" disabled={loading}>
        {loading ? 'Deleting…' : confirmLabel}
      </Button>
    </DialogActions>
  </Dialog>
);
```

- [ ] **Step 2: Add delete state and handler to PaperCard**

Add these imports at the top of `PaperCard.tsx`:

```tsx
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import { ConfirmDialog } from './ConfirmDialog';
import { papersAPI } from '../../services/api';
```

Add these state variables inside the component (after existing useState calls):

```tsx
const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
const [deleting, setDeleting] = useState(false);
```

Add the handler after `getGradient`:

```tsx
const handleDelete = async () => {
  setDeleting(true);
  try {
    await papersAPI.delete(id, token);
    onDelete?.(id);
  } finally {
    setDeleting(false);
    setDeleteDialogOpen(false);
  }
};
```

- [ ] **Step 3: Add `onDelete` prop to PaperCardProps**

Update the interface:

```tsx
interface PaperCardProps {
  id: string;
  title: string;
  authors: string[];
  arxiv_id: string;
  created_at: string;
  token: string;
  onDelete?: (id: string) => void;
}
```

Update the component signature to destructure `onDelete`:

```tsx
export const PaperCard: React.FC<PaperCardProps> = ({ id, title, authors, arxiv_id, created_at, token, onDelete }) => {
```

- [ ] **Step 4: Add delete IconButton to CardActions**

Inside `CardActions`, after the Export `IconButton` block, add:

```tsx
<Tooltip title="Delete">
  <IconButton
    aria-label="Delete paper"
    color="error"
    onClick={() => setDeleteDialogOpen(true)}
    sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 4 }}
  >
    <DeleteOutlineRoundedIcon fontSize="small" />
  </IconButton>
</Tooltip>
```

- [ ] **Step 5: Add ConfirmDialog to the JSX return**

After the `<ExportMenu ... />` block and before the closing `</>`, add:

```tsx
<ConfirmDialog
  open={deleteDialogOpen}
  title="Delete paper?"
  message={`"${title || 'This paper'}" will be permanently removed from your library.`}
  confirmLabel="Delete"
  onConfirm={handleDelete}
  onCancel={() => setDeleteDialogOpen(false)}
  loading={deleting}
/>
```

- [ ] **Step 6: Wire onDelete in LibraryPage**

In `frontend/src/pages/LibraryPage.tsx`, update the `setPapers` state handler and pass `onDelete` to `PaperCard`:

Add a handler after the `filteredPapers` definition:

```tsx
const handleDelete = (deletedId: string) => {
  setPapers(prev => prev.filter(p => p.id !== deletedId));
};
```

Update the `PaperCard` usage to pass `onDelete`:

```tsx
<PaperCard
  id={paper.id}
  title={paper.title}
  authors={paper.authors}
  arxiv_id={paper.arxiv_id}
  created_at={paper.created_at}
  token={user?.token || ''}
  onDelete={handleDelete}
/>
```

- [ ] **Step 7: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/library/ frontend/src/pages/LibraryPage.tsx
git commit -m "feat: add delete button with confirm dialog to PaperCard"
```

---

## Task 3: FormulaBlock updates

**Files:**
- Modify: `frontend/src/components/paper/FormulaBlock.tsx`
- Create: `frontend/src/components/paper/__tests__/FormulaBlock.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// frontend/src/components/paper/__tests__/FormulaBlock.test.tsx
import { render, screen } from '@testing-library/react';
import { FormulaBlock } from '../FormulaBlock';

const baseFormula = {
  latex: 'E = mc^2',
  plain_explanation: 'Energy equals mass times speed of light squared.',
  symbols: { E: 'energy', m: 'mass', c: 'speed of light' },
  importance: 'Foundational',
};

test('renders plain_explanation', () => {
  render(<FormulaBlock formula={baseFormula} />);
  expect(screen.getByText('Energy equals mass times speed of light squared.')).toBeInTheDocument();
});

test('renders intuition when provided', () => {
  render(<FormulaBlock formula={{ ...baseFormula, intuition: 'Mass is frozen energy.' }} />);
  expect(screen.getByText('Mass is frozen energy.')).toBeInTheDocument();
});

test('renders each prerequisite as a chip', () => {
  render(<FormulaBlock formula={{ ...baseFormula, prerequisites: ['Special relativity', 'Classical mechanics'] }} />);
  expect(screen.getByText('Special relativity')).toBeInTheDocument();
  expect(screen.getByText('Classical mechanics')).toBeInTheDocument();
});

test('renders where_it_appears label when provided', () => {
  render(<FormulaBlock formula={{ ...baseFormula, where_it_appears: 'Section 3 — Method' }} />);
  expect(screen.getByText('Section 3 — Method')).toBeInTheDocument();
});

test('does not render intuition section when absent', () => {
  render(<FormulaBlock formula={baseFormula} />);
  expect(screen.queryByTestId('formula-intuition')).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to confirm failure**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/FormulaBlock.test.tsx
```

Expected: FAIL (intuition, prerequisites, where_it_appears not rendered yet).

- [ ] **Step 3: Update FormulaBlock.tsx**

Replace the full file contents:

```tsx
// frontend/src/components/paper/FormulaBlock.tsx
import React from 'react';
import { Box, Chip, Stack, Typography } from '@mui/material';
import { BlockMath } from 'react-katex';
import { FormulaExplanation } from '../../types';

interface FormulaBlockProps {
  formula: FormulaExplanation;
}

export const FormulaBlock: React.FC<FormulaBlockProps> = ({ formula }) => (
  <Stack spacing={1.25}>
    {formula.intuition ? (
      <Typography variant="body2" color="text.secondary" fontStyle="italic" data-testid="formula-intuition">
        {formula.intuition}
      </Typography>
    ) : null}
    {formula.latex ? (
      <Box
        sx={{
          overflowX: 'auto',
          bgcolor: 'action.hover',
          borderRadius: 3,
          px: 2,
          py: 1.5,
          '.katex-display': { margin: 0 },
        }}
      >
        <BlockMath math={formula.latex} errorColor="#cc2f2f" />
      </Box>
    ) : null}
    <Typography variant="body2" color="text.secondary">
      {formula.plain_explanation}
    </Typography>
    {formula.prerequisites?.length ? (
      <Stack direction="row" spacing={0.75} flexWrap="wrap">
        {formula.prerequisites.map((p) => (
          <Chip key={p} label={p} size="small" variant="outlined" sx={{ mb: 0.5 }} />
        ))}
      </Stack>
    ) : null}
    {formula.where_it_appears ? (
      <Typography variant="caption" color="text.secondary">
        {formula.where_it_appears}
      </Typography>
    ) : null}
    {formula.importance ? (
      <Chip label={formula.importance} size="small" variant="outlined" sx={{ alignSelf: 'flex-start' }} />
    ) : null}
  </Stack>
);
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/FormulaBlock.test.tsx
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/paper/FormulaBlock.tsx frontend/src/components/paper/__tests__/FormulaBlock.test.tsx
git commit -m "feat: add intuition, prerequisites, and where_it_appears to FormulaBlock"
```

---

## Task 4: Simple anatomy section components (Problem, PriorArt, Idea, Takeaways)

**Files:**
- Create: `frontend/src/components/paper/anatomy/ProblemSection.tsx`
- Create: `frontend/src/components/paper/anatomy/PriorArtSection.tsx`
- Create: `frontend/src/components/paper/anatomy/IdeaSection.tsx`
- Create: `frontend/src/components/paper/anatomy/TakeawaysSection.tsx`

These four follow identical structure: icon square + label + prose (or list). They are pure layout — no logic to test beyond rendering.

- [ ] **Step 1: Create shared anatomy section shell**

Each section uses this pattern. The icon background colors are:
- Problem: `rgba(33,84,214,0.12)` (primary tint)
- PriorArt: `rgba(15,143,121,0.12)` (secondary tint)
- Idea: `rgba(202,107,20,0.12)` (warning tint)
- Takeaways: `rgba(202,107,20,0.12)` (warning tint)

- [ ] **Step 2: Create ProblemSection.tsx**

```tsx
// frontend/src/components/paper/anatomy/ProblemSection.tsx
import React from 'react';
import { Box, Paper, Stack, Typography } from '@mui/material';

interface ProblemSectionProps {
  content: string;
}

export const ProblemSection: React.FC<ProblemSectionProps> = ({ content }) => (
  <Paper sx={{ p: 2.5, borderRadius: 4 }}>
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(33,84,214,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
          🎯
        </Box>
        <Typography variant="h6">Problem &amp; Motivation</Typography>
      </Stack>
      <Typography variant="body1" color="text.secondary">{content}</Typography>
    </Stack>
  </Paper>
);
```

- [ ] **Step 3: Create PriorArtSection.tsx**

```tsx
// frontend/src/components/paper/anatomy/PriorArtSection.tsx
import React from 'react';
import { Box, Paper, Stack, Typography } from '@mui/material';

interface PriorArtSectionProps {
  content: string;
}

export const PriorArtSection: React.FC<PriorArtSectionProps> = ({ content }) => (
  <Paper sx={{ p: 2.5, borderRadius: 4 }}>
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(15,143,121,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
          📚
        </Box>
        <Typography variant="h6">Prior Work &amp; Gap</Typography>
      </Stack>
      <Typography variant="body1" color="text.secondary">{content}</Typography>
    </Stack>
  </Paper>
);
```

- [ ] **Step 4: Create IdeaSection.tsx**

```tsx
// frontend/src/components/paper/anatomy/IdeaSection.tsx
import React from 'react';
import { Box, Paper, Stack, Typography } from '@mui/material';

interface IdeaSectionProps {
  content: string;
}

export const IdeaSection: React.FC<IdeaSectionProps> = ({ content }) => (
  <Paper sx={{ p: 2.5, borderRadius: 4 }}>
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(202,107,20,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
          💡
        </Box>
        <Typography variant="h6">Core Intuition</Typography>
      </Stack>
      <Typography variant="body1" color="text.secondary">{content}</Typography>
    </Stack>
  </Paper>
);
```

- [ ] **Step 5: Create TakeawaysSection.tsx**

```tsx
// frontend/src/components/paper/anatomy/TakeawaysSection.tsx
import React from 'react';
import { Box, Paper, Stack, Typography } from '@mui/material';

interface TakeawaysSectionProps {
  items: string[];
}

export const TakeawaysSection: React.FC<TakeawaysSectionProps> = ({ items }) => (
  <Paper sx={{ p: 2.5, borderRadius: 4 }}>
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(202,107,20,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
          ✅
        </Box>
        <Typography variant="h6">Takeaways</Typography>
      </Stack>
      <Stack spacing={1}>
        {items.map((item, i) => (
          <Box
            key={i}
            sx={{
              pl: 1.5,
              py: 0.75,
              borderLeft: '3px solid',
              borderColor: 'warning.main',
              borderRadius: '0 6px 6px 0',
              bgcolor: 'action.hover',
            }}
          >
            <Typography variant="body2" color="text.secondary">{item}</Typography>
          </Box>
        ))}
      </Stack>
    </Stack>
  </Paper>
);
```

- [ ] **Step 6: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/paper/anatomy/
git commit -m "feat: add Problem, PriorArt, Idea, Takeaways anatomy section components"
```

---

## Task 5: MethodSection

**Files:**
- Create: `frontend/src/components/paper/anatomy/MethodSection.tsx`

- [ ] **Step 1: Create MethodSection.tsx**

Shows `method_deep_dive` prose + inline `FormulaBlock` cards for formulas whose `where_it_appears` field (case-insensitive) includes "method".

```tsx
// frontend/src/components/paper/anatomy/MethodSection.tsx
import React from 'react';
import { Box, Paper, Stack, Typography } from '@mui/material';
import { FormulaBlock } from '../FormulaBlock';
import { FormulaExplanation } from '../../../types';

interface MethodSectionProps {
  content: string;
  formulas: FormulaExplanation[];
}

export const MethodSection: React.FC<MethodSectionProps> = ({ content, formulas }) => {
  const methodFormulas = formulas.filter(
    (f) => f.where_it_appears?.toLowerCase().includes('method')
  );

  return (
    <Paper sx={{ p: 2.5, borderRadius: 4 }}>
      <Stack spacing={1.5}>
        <Stack direction="row" spacing={1.25} alignItems="center">
          <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(128,0,200,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
            ⚙️
          </Box>
          <Typography variant="h6">Method Deep Dive</Typography>
        </Stack>
        <Typography variant="body1" color="text.secondary">{content}</Typography>
        {methodFormulas.length > 0 && (
          <Stack spacing={1.25}>
            {methodFormulas.map((f, i) => (
              <Paper key={f.latex || i} sx={{ p: 2, borderRadius: 3, bgcolor: 'rgba(128,0,200,0.04)', border: '1px solid', borderColor: 'rgba(128,0,200,0.12)' }}>
                <FormulaBlock formula={f} />
              </Paper>
            ))}
          </Stack>
        )}
      </Stack>
    </Paper>
  );
};
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/paper/anatomy/MethodSection.tsx
git commit -m "feat: add MethodSection with inline formula filtering"
```

---

## Task 6: EvidenceSection

**Files:**
- Create: `frontend/src/components/paper/anatomy/EvidenceSection.tsx`

- [ ] **Step 1: Create EvidenceSection.tsx**

Shows `results_and_evidence` prose, artifact interpretation chips with confidence-based coloring, and raw extracts collapsed behind a toggle.

```tsx
// frontend/src/components/paper/anatomy/EvidenceSection.tsx
import React, { useState } from 'react';
import { Box, Button, Chip, Collapse, Divider, Paper, Stack, Typography } from '@mui/material';
import { ArtifactInterpretation, FigureCaption, ExtractedTable, ResultsView } from '../../../types';

interface EvidenceSectionProps {
  content?: string;
  resultsView?: ResultsView;
  artifactInterpretations?: ArtifactInterpretation[];
  figureCaptions?: FigureCaption[];
  tables?: ExtractedTable[];
}

const confidenceColor = (c?: string): 'success' | 'warning' | 'default' => {
  if (c === 'high') return 'success';
  if (c === 'low' || c === 'medium') return 'warning';
  return 'default';
};

export const EvidenceSection: React.FC<EvidenceSectionProps> = ({
  content,
  resultsView,
  artifactInterpretations = [],
  figureCaptions = [],
  tables = [],
}) => {
  const [rawOpen, setRawOpen] = useState(false);
  const hasRaw = figureCaptions.length > 0 || tables.length > 0;

  return (
    <Paper sx={{ p: 2.5, borderRadius: 4 }}>
      <Stack spacing={1.5}>
        <Stack direction="row" spacing={1.25} alignItems="center">
          <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(15,143,121,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
            📊
          </Box>
          <Typography variant="h6">Evidence &amp; Results</Typography>
        </Stack>

        {content && (
          <Typography variant="body1" color="text.secondary">{content}</Typography>
        )}

        {resultsView?.evaluation_setup && (
          <Typography variant="body2" color="text.secondary">
            <strong>Evaluation setup:</strong> {resultsView.evaluation_setup}
          </Typography>
        )}

        {artifactInterpretations.length > 0 && (
          <Stack spacing={1.25}>
            {artifactInterpretations.map((item, i) => (
              <Paper key={`${item.label}-${i}`} sx={{ p: 2, borderRadius: 3 }}>
                <Stack spacing={0.75}>
                  <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                    <Typography variant="subtitle2" fontWeight={700}>{item.label}</Typography>
                    <Chip size="small" label={item.artifact_type === 'table' ? 'Table' : 'Figure'} variant="outlined" />
                    {item.confidence && (
                      <Chip
                        size="small"
                        label={`${item.confidence} confidence`}
                        color={confidenceColor(item.confidence)}
                        variant="outlined"
                      />
                    )}
                  </Stack>
                  <Typography variant="body2" color="text.secondary">{item.what_it_shows}</Typography>
                  {item.why_it_matters && (
                    <Typography variant="body2">
                      <strong>Why it matters:</strong> {item.why_it_matters}
                    </Typography>
                  )}
                </Stack>
              </Paper>
            ))}
          </Stack>
        )}

        {hasRaw && (
          <>
            <Divider />
            <Button
              size="small"
              variant="text"
              onClick={() => setRawOpen((v) => !v)}
              sx={{ alignSelf: 'flex-start', color: 'text.secondary' }}
            >
              {rawOpen ? 'Hide raw extracts' : 'Show raw extracts'}
            </Button>
            <Collapse in={rawOpen}>
              <Stack spacing={1.25} sx={{ mt: 1 }}>
                {figureCaptions.map((item, i) => (
                  <Paper key={`fig-${i}`} sx={{ p: 2, borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Page {item.page + 1}{item.section_title ? ` · ${item.section_title}` : ''}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: 13 }}>{item.caption}</Typography>
                  </Paper>
                ))}
                {tables.map((table, i) => (
                  <Paper key={`tbl-${i}`} sx={{ p: 2, borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="subtitle2" color="text.secondary">{table.title}</Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      Page {table.page + 1}{table.section_title ? ` · ${table.section_title}` : ''}
                    </Typography>
                    <Box sx={{ overflowX: 'auto' }}>
                      <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', minWidth: 320 }}>
                        <Box component="tbody">
                          {table.rows.map((row, ri) => (
                            <Box component="tr" key={ri}>
                              {row.map((cell, ci) => (
                                <Box component="td" key={ci} sx={{ borderBottom: '1px solid', borderColor: 'divider', py: 0.75, pr: 1.5, fontSize: 12, color: 'text.secondary', verticalAlign: 'top' }}>
                                  {cell || '—'}
                                </Box>
                              ))}
                            </Box>
                          ))}
                        </Box>
                      </Box>
                    </Box>
                  </Paper>
                ))}
              </Stack>
            </Collapse>
          </>
        )}
      </Stack>
    </Paper>
  );
};
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/paper/anatomy/EvidenceSection.tsx
git commit -m "feat: add EvidenceSection with artifact chips, confidence colors, raw extracts toggle"
```

---

## Task 7: VerdictSection

**Files:**
- Create: `frontend/src/components/paper/anatomy/VerdictSection.tsx`

- [ ] **Step 1: Create VerdictSection.tsx**

Two-card side-by-side layout: "Authors claim" (primary tint) vs "Evidence shows" (secondary tint).

```tsx
// frontend/src/components/paper/anatomy/VerdictSection.tsx
import React from 'react';
import { Box, Grid, Paper, Stack, Typography } from '@mui/material';

interface VerdictSectionProps {
  authorsClaim: string;
  evidenceAssessment: string;
}

export const VerdictSection: React.FC<VerdictSectionProps> = ({ authorsClaim, evidenceAssessment }) => (
  <Paper sx={{ p: 2.5, borderRadius: 4 }}>
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(33,84,214,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
          ⚖️
        </Box>
        <Typography variant="h6">Verdict</Typography>
      </Stack>
      <Grid container spacing={1.5}>
        <Grid item xs={12} sm={6}>
          <Paper
            sx={{
              p: 2,
              borderRadius: 3,
              bgcolor: 'rgba(33,84,214,0.04)',
              border: '1px solid',
              borderColor: 'rgba(33,84,214,0.14)',
              height: '100%',
            }}
          >
            <Typography variant="overline" color="primary" display="block" sx={{ mb: 0.75 }}>
              Authors claim
            </Typography>
            <Typography variant="body2" color="text.secondary">{authorsClaim}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6}>
          <Paper
            sx={{
              p: 2,
              borderRadius: 3,
              bgcolor: 'rgba(15,143,121,0.04)',
              border: '1px solid',
              borderColor: 'rgba(15,143,121,0.14)',
              height: '100%',
            }}
          >
            <Typography variant="overline" color="secondary" display="block" sx={{ mb: 0.75 }}>
              Evidence shows
            </Typography>
            <Typography variant="body2" color="text.secondary">{evidenceAssessment}</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  </Paper>
);
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/paper/anatomy/VerdictSection.tsx
git commit -m "feat: add VerdictSection with side-by-side claim/evidence cards"
```

---

## Task 8: AnatomyView

**Files:**
- Create: `frontend/src/components/paper/anatomy/AnatomyView.tsx`

- [ ] **Step 1: Create AnatomyView.tsx**

Sequences all 7 section components. Skips sections with missing/empty content. Receives `summary` prop.

```tsx
// frontend/src/components/paper/anatomy/AnatomyView.tsx
import React from 'react';
import { Stack } from '@mui/material';
import { PaperAnalysis, FormulaExplanation } from '../../../types';
import { ProblemSection } from './ProblemSection';
import { PriorArtSection } from './PriorArtSection';
import { IdeaSection } from './IdeaSection';
import { MethodSection } from './MethodSection';
import { EvidenceSection } from './EvidenceSection';
import { VerdictSection } from './VerdictSection';
import { TakeawaysSection } from './TakeawaysSection';

interface AnatomyViewProps {
  summary: NonNullable<PaperAnalysis['summary']>;
}

export const AnatomyView: React.FC<AnatomyViewProps> = ({ summary }) => {
  const formulas: FormulaExplanation[] = summary.formula_explanations ?? [];

  const artifactInterpretations =
    summary.artifact_interpretations ??
    summary.results_view?.artifact_interpretations ??
    [
      ...(summary.table_interpretations ?? []),
      ...(summary.figure_interpretations ?? []),
    ];

  return (
    <Stack spacing={2}>
      {summary.problem_and_motivation && (
        <ProblemSection content={summary.problem_and_motivation} />
      )}
      {summary.prior_work_and_gap && (
        <PriorArtSection content={summary.prior_work_and_gap} />
      )}
      {summary.core_intuition && (
        <IdeaSection content={summary.core_intuition} />
      )}
      {summary.method_deep_dive && (
        <MethodSection content={summary.method_deep_dive} formulas={formulas} />
      )}
      {(summary.results_and_evidence || artifactInterpretations.length > 0) && (
        <EvidenceSection
          content={summary.results_and_evidence}
          resultsView={summary.results_view}
          artifactInterpretations={artifactInterpretations}
          figureCaptions={summary.figure_captions}
          tables={summary.tables}
        />
      )}
      {summary.authors_claims && summary.evidence_assessment && (
        <VerdictSection
          authorsClaim={summary.authors_claims}
          evidenceAssessment={summary.evidence_assessment}
        />
      )}
      {summary.reader_takeaways?.length ? (
        <TakeawaysSection items={summary.reader_takeaways} />
      ) : null}
    </Stack>
  );
};
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/paper/anatomy/AnatomyView.tsx
git commit -m "feat: add AnatomyView sequencing all anatomy section components"
```

---

## Task 9: CritiqueIndicator

**Files:**
- Create: `frontend/src/components/paper/CritiqueIndicator.tsx`
- Create: `frontend/src/components/paper/__tests__/CritiqueIndicator.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// frontend/src/components/paper/__tests__/CritiqueIndicator.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CritiqueIndicator } from '../CritiqueIndicator';

const critique = {
  needs_revision: true,
  overall_assessment: 'Some issues found.',
  issues: [
    { field: 'results', severity: 'high' as const, type: 'overclaim' as const, description: 'Overclaims generalization.', suggested_fix: 'Qualify the claim.' },
    { field: 'method', severity: 'low' as const, type: 'vague_method' as const, description: 'Method is underspecified.', suggested_fix: 'Add detail.' },
  ],
};

test('renders chip with issue count', () => {
  render(<CritiqueIndicator critique={critique} />);
  expect(screen.getByText(/2 quality notes/i)).toBeInTheDocument();
});

test('renders nothing when no issues', () => {
  const { container } = render(<CritiqueIndicator critique={{ ...critique, issues: [] }} />);
  expect(container.firstChild).toBeNull();
});

test('opens drawer with issue list on chip click', async () => {
  render(<CritiqueIndicator critique={critique} />);
  await userEvent.click(screen.getByText(/2 quality notes/i));
  expect(screen.getByText('Overclaims generalization.')).toBeInTheDocument();
  expect(screen.getByText('Method is underspecified.')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to confirm failure**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/CritiqueIndicator.test.tsx
```

Expected: FAIL (module not found).

- [ ] **Step 3: Create CritiqueIndicator.tsx**

```tsx
// frontend/src/components/paper/CritiqueIndicator.tsx
import React, { useState } from 'react';
import { Box, Chip, Divider, Drawer, Stack, Typography } from '@mui/material';
import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded';
import { PaperAnalysis } from '../../types';

type Critique = NonNullable<NonNullable<PaperAnalysis['summary']>['critique']>;

interface CritiqueIndicatorProps {
  critique: Critique;
}

const severityColor = (s: string): 'error' | 'warning' | 'default' => {
  if (s === 'high') return 'error';
  if (s === 'medium') return 'warning';
  return 'default';
};

export const CritiqueIndicator: React.FC<CritiqueIndicatorProps> = ({ critique }) => {
  const [open, setOpen] = useState(false);

  if (!critique.issues?.length) return null;

  return (
    <>
      <Chip
        icon={<WarningAmberRoundedIcon />}
        label={`${critique.issues.length} quality note${critique.issues.length !== 1 ? 's' : ''}`}
        color="warning"
        variant="outlined"
        size="small"
        onClick={() => setOpen(true)}
        sx={{ cursor: 'pointer' }}
      />
      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        PaperProps={{ sx: { width: { xs: '100%', sm: 400 }, p: 3 } }}
      >
        <Typography variant="h6" gutterBottom>Quality notes</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {critique.overall_assessment}
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Stack spacing={2}>
          {critique.issues.map((issue, i) => (
            <Box key={i}>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.75 }}>
                <Chip size="small" label={issue.severity} color={severityColor(issue.severity)} />
                <Chip size="small" label={issue.type.replace(/_/g, ' ')} variant="outlined" />
                <Typography variant="caption" color="text.secondary">{issue.field}</Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">{issue.description}</Typography>
              {issue.suggested_fix && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, pl: 1, borderLeft: '2px solid', borderColor: 'divider' }}>
                  Fix: {issue.suggested_fix}
                </Typography>
              )}
            </Box>
          ))}
        </Stack>
      </Drawer>
    </>
  );
};
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/CritiqueIndicator.test.tsx
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/paper/CritiqueIndicator.tsx frontend/src/components/paper/__tests__/CritiqueIndicator.test.tsx
git commit -m "feat: add CritiqueIndicator chip with issue drawer"
```

---

## Task 10: PaperAtAGlance

**Files:**
- Create: `frontend/src/components/paper/PaperAtAGlance.tsx`

- [ ] **Step 1: Create PaperAtAGlance.tsx**

```tsx
// frontend/src/components/paper/PaperAtAGlance.tsx
import React from 'react';
import { Box, Chip, Paper, Stack, Typography } from '@mui/material';
import ArticleRoundedIcon from '@mui/icons-material/ArticleRounded';
import FunctionsRoundedIcon from '@mui/icons-material/FunctionsRounded';
import { PaperMap, PaperAnalysis } from '../../types';
import { CritiqueIndicator } from './CritiqueIndicator';

interface PaperAtAGlanceProps {
  paperMap: PaperMap;
  critique?: NonNullable<PaperAnalysis['summary']>['critique'];
}

export const PaperAtAGlance: React.FC<PaperAtAGlanceProps> = ({ paperMap, critique }) => (
  <Paper sx={{ p: 2, borderRadius: 4, bgcolor: 'rgba(33,84,214,0.03)', border: '1px solid', borderColor: 'rgba(33,84,214,0.1)' }}>
    <Stack spacing={1}>
      <Typography variant="overline" color="text.secondary">At a glance</Typography>
      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
        {paperMap.paper_type && (
          <Chip
            icon={<ArticleRoundedIcon />}
            label={paperMap.paper_type}
            color="primary"
            variant="outlined"
            size="small"
          />
        )}
        {paperMap.math_relevance && (
          <Chip
            icon={<FunctionsRoundedIcon />}
            label={`Math: ${paperMap.math_relevance}`}
            variant="outlined"
            size="small"
          />
        )}
        {paperMap.results_focus && (
          <Chip label={paperMap.results_focus} variant="outlined" size="small" />
        )}
        {critique?.issues?.length ? (
          <Box sx={{ ml: 'auto' }}>
            <CritiqueIndicator critique={critique} />
          </Box>
        ) : null}
      </Stack>
      {paperMap.reader_orientation && (
        <Typography variant="body2" color="text.secondary">{paperMap.reader_orientation}</Typography>
      )}
    </Stack>
  </Paper>
);
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/paper/PaperAtAGlance.tsx
git commit -m "feat: add PaperAtAGlance card with paper type, math level, critique chip"
```

---

## Task 11: WorkspaceHeader

**Files:**
- Create: `frontend/src/components/paper/WorkspaceHeader.tsx`
- Create: `frontend/src/components/paper/__tests__/WorkspaceHeader.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
// frontend/src/components/paper/__tests__/WorkspaceHeader.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WorkspaceHeader } from '../WorkspaceHeader';

const defaultProps = {
  readingLevel: 'general' as const,
  onReadingLevelChange: vi.fn(),
  rightPanel: null as 'paper' | 'chat' | null,
  onRightPanelChange: vi.fn(),
  hasPaperUrl: true,
};

test('renders reading level options', () => {
  render(<WorkspaceHeader {...defaultProps} />);
  expect(screen.getByText('General')).toBeInTheDocument();
  expect(screen.getByText('Technical')).toBeInTheDocument();
  expect(screen.getByText('ELI5')).toBeInTheDocument();
});

test('calls onReadingLevelChange when Technical is clicked', async () => {
  const spy = vi.fn();
  render(<WorkspaceHeader {...defaultProps} onReadingLevelChange={spy} />);
  await userEvent.click(screen.getByText('Technical'));
  expect(spy).toHaveBeenCalledWith('technical');
});

test('clicking Chat sets rightPanel to chat', async () => {
  const spy = vi.fn();
  render(<WorkspaceHeader {...defaultProps} onRightPanelChange={spy} />);
  await userEvent.click(screen.getByText('Chat'));
  expect(spy).toHaveBeenCalledWith('chat');
});

test('clicking Chat when chat is active sets rightPanel to null', async () => {
  const spy = vi.fn();
  render(<WorkspaceHeader {...defaultProps} rightPanel="chat" onRightPanelChange={spy} />);
  await userEvent.click(screen.getByText('Chat'));
  expect(spy).toHaveBeenCalledWith(null);
});
```

- [ ] **Step 2: Run test to confirm failure**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/WorkspaceHeader.test.tsx
```

Expected: FAIL (module not found).

- [ ] **Step 3: Create WorkspaceHeader.tsx**

```tsx
// frontend/src/components/paper/WorkspaceHeader.tsx
import React from 'react';
import { Box, Button, Paper, Stack, Typography } from '@mui/material';
import MenuBookRoundedIcon from '@mui/icons-material/MenuBookRounded';
import ChatRoundedIcon from '@mui/icons-material/ChatRounded';

type ReadingLevel = 'general' | 'technical' | 'eli5';
type RightPanel = 'paper' | 'chat' | null;

interface WorkspaceHeaderProps {
  readingLevel: ReadingLevel;
  onReadingLevelChange: (level: ReadingLevel) => void;
  rightPanel: RightPanel;
  onRightPanelChange: (panel: RightPanel) => void;
  hasPaperUrl: boolean;
}

const LEVELS: { value: ReadingLevel; label: string }[] = [
  { value: 'general', label: 'General' },
  { value: 'technical', label: 'Technical' },
  { value: 'eli5', label: 'ELI5' },
];

export const WorkspaceHeader: React.FC<WorkspaceHeaderProps> = ({
  readingLevel,
  onReadingLevelChange,
  rightPanel,
  onRightPanelChange,
  hasPaperUrl,
}) => {
  const handlePaperToggle = () =>
    onRightPanelChange(rightPanel === 'paper' ? null : 'paper');

  const handleChatToggle = () =>
    onRightPanelChange(rightPanel === 'chat' ? null : 'chat');

  return (
    <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 6 }}>
      <Stack spacing={2}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} justifyContent="space-between" alignItems={{ md: 'flex-start' }}>
          <Box>
            <Typography variant="overline" color="text.secondary">Analysis workspace</Typography>
            <Typography variant="h3">Distilled paper view</Typography>
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 640, mt: 0.5 }}>
              Read the paper as a guided walkthrough — problem, method, evidence, and verdict.
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
            {/* Reading level segmented control */}
            <Box
              sx={{
                display: 'inline-flex',
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: '10px',
                overflow: 'hidden',
              }}
            >
              {LEVELS.map(({ value, label }) => (
                <Box
                  key={value}
                  component="button"
                  onClick={() => onReadingLevelChange(value)}
                  sx={{
                    px: 1.75,
                    py: 0.75,
                    border: 0,
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                    fontSize: 13,
                    fontWeight: readingLevel === value ? 700 : 500,
                    bgcolor: readingLevel === value ? 'primary.main' : 'transparent',
                    color: readingLevel === value ? 'primary.contrastText' : 'text.secondary',
                    transition: 'background 150ms, color 150ms',
                    '&:hover': {
                      bgcolor: readingLevel === value ? 'primary.main' : 'action.hover',
                    },
                  }}
                >
                  {label}
                </Box>
              ))}
            </Box>

            {hasPaperUrl && (
              <Button
                variant={rightPanel === 'paper' ? 'contained' : 'outlined'}
                startIcon={<MenuBookRoundedIcon />}
                onClick={handlePaperToggle}
                size="small"
              >
                {rightPanel === 'paper' ? 'Hide paper' : 'View paper'}
              </Button>
            )}

            <Button
              variant={rightPanel === 'chat' ? 'contained' : 'outlined'}
              startIcon={<ChatRoundedIcon />}
              onClick={handleChatToggle}
              size="small"
            >
              Chat
            </Button>
          </Stack>
        </Stack>
      </Stack>
    </Paper>
  );
};
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/WorkspaceHeader.test.tsx
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/paper/WorkspaceHeader.tsx frontend/src/components/paper/__tests__/WorkspaceHeader.test.tsx
git commit -m "feat: add WorkspaceHeader with reading level control and panel toggles"
```

---

## Task 12: TermGlossary

**Files:**
- Create: `frontend/src/components/paper/TermGlossary.tsx`
- Create: `frontend/src/components/paper/__tests__/TermGlossary.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
// frontend/src/components/paper/__tests__/TermGlossary.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TermGlossary } from '../TermGlossary';
import { DistilledTerm } from '../../../types';

const terms: DistilledTerm[] = [
  { term: 'Attention', category: 'method', definition: 'Weighted focus mechanism.', mentions: 5 },
  { term: 'BLEU', category: 'metric', definition: 'Translation quality metric.', mentions: 3 },
  { term: 'Transformer', category: 'concept', definition: 'Sequence-to-sequence model.', mentions: 8 },
];

test('renders all terms initially', () => {
  render(<TermGlossary terms={terms} />);
  expect(screen.getByText('Attention')).toBeInTheDocument();
  expect(screen.getByText('BLEU')).toBeInTheDocument();
  expect(screen.getByText('Transformer')).toBeInTheDocument();
});

test('filters terms by search query', async () => {
  render(<TermGlossary terms={terms} />);
  const input = screen.getByPlaceholderText(/search/i);
  await userEvent.type(input, 'trans');
  expect(screen.getByText('Transformer')).toBeInTheDocument();
  expect(screen.queryByText('BLEU')).not.toBeInTheDocument();
  expect(screen.queryByText('Attention')).not.toBeInTheDocument();
});

test('matches on definition text too', async () => {
  render(<TermGlossary terms={terms} />);
  const input = screen.getByPlaceholderText(/search/i);
  await userEvent.type(input, 'metric');
  expect(screen.getByText('BLEU')).toBeInTheDocument();
  expect(screen.queryByText('Attention')).not.toBeInTheDocument();
});

test('shows empty message when no match', async () => {
  render(<TermGlossary terms={terms} />);
  const input = screen.getByPlaceholderText(/search/i);
  await userEvent.type(input, 'zzznomatch');
  expect(screen.getByText(/no terms match/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to confirm failure**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/TermGlossary.test.tsx
```

Expected: FAIL (module not found).

- [ ] **Step 3: Create TermGlossary.tsx**

```tsx
// frontend/src/components/paper/TermGlossary.tsx
import React, { useState } from 'react';
import { Box, Chip, InputAdornment, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { DistilledTerm } from '../../types';

interface TermGlossaryProps {
  terms: DistilledTerm[];
}

export const TermGlossary: React.FC<TermGlossaryProps> = ({ terms }) => {
  const [query, setQuery] = useState('');

  const filtered = query.trim()
    ? terms.filter(
        (t) =>
          t.term.toLowerCase().includes(query.toLowerCase()) ||
          t.definition.toLowerCase().includes(query.toLowerCase())
      )
    : terms;

  return (
    <Paper sx={{ p: { xs: 2, md: 3 }, borderRadius: 5 }}>
      <Stack spacing={2}>
        <Typography variant="h6">Term Glossary</Typography>
        <TextField
          size="small"
          placeholder="Search terms or definitions…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
          sx={{ maxWidth: 400 }}
        />
        {filtered.length === 0 ? (
          <Typography variant="body2" color="text.secondary">No terms match "{query}".</Typography>
        ) : (
          <Box sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Term</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Definition</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filtered.map((term, i) => (
                  <TableRow key={`${term.term}-${i}`}>
                    <TableCell sx={{ fontWeight: 600, whiteSpace: 'nowrap' }}>{term.term}</TableCell>
                    <TableCell>
                      <Chip label={term.category} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell sx={{ color: 'text.secondary' }}>{term.definition}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}
      </Stack>
    </Paper>
  );
};
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/TermGlossary.test.tsx
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/paper/TermGlossary.tsx frontend/src/components/paper/__tests__/TermGlossary.test.tsx
git commit -m "feat: add TermGlossary with client-side search"
```

---

## Task 13: ChatPanel

**Files:**
- Create: `frontend/src/components/paper/ChatPanel.tsx`
- Create: `frontend/src/components/paper/__tests__/ChatPanel.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
// frontend/src/components/paper/__tests__/ChatPanel.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { ChatPanel } from '../ChatPanel';

vi.mock('../../../services/api', () => ({
  papersAPI: {
    chat: vi.fn().mockResolvedValue({ reply: 'The key equation balances reconstruction and KL divergence.' }),
  },
}));

import { papersAPI } from '../../../services/api';

test('renders starter prompts when no messages', () => {
  render(<ChatPanel paperId="p1" token="tok" onClose={vi.fn()} />);
  expect(screen.getByText(/explain the key equation/i)).toBeInTheDocument();
  expect(screen.getByText(/does the evaluation actually prove/i)).toBeInTheDocument();
});

test('sends message and shows reply', async () => {
  render(<ChatPanel paperId="p1" token="tok" onClose={vi.fn()} />);
  const input = screen.getByPlaceholderText(/ask/i);
  await userEvent.type(input, 'What is the main idea?');
  await userEvent.click(screen.getByText('Send'));

  expect(screen.getByText('What is the main idea?')).toBeInTheDocument();
  await waitFor(() =>
    expect(screen.getByText('The key equation balances reconstruction and KL divergence.')).toBeInTheDocument()
  );
});

test('clears input after send', async () => {
  render(<ChatPanel paperId="p1" token="tok" onClose={vi.fn()} />);
  const input = screen.getByPlaceholderText(/ask/i);
  await userEvent.type(input, 'Hello');
  await userEvent.click(screen.getByText('Send'));
  expect(input).toHaveValue('');
});

test('clicking starter prompt pre-fills and sends', async () => {
  render(<ChatPanel paperId="p1" token="tok" onClose={vi.fn()} />);
  const prompt = screen.getByText(/explain the key equation/i);
  await userEvent.click(prompt);
  await waitFor(() =>
    expect(papersAPI.chat).toHaveBeenCalledWith(
      'p1',
      expect.arrayContaining([expect.objectContaining({ content: expect.stringContaining('key equation') })]),
      'tok'
    )
  );
});

test('calls onClose when close button clicked', async () => {
  const onClose = vi.fn();
  render(<ChatPanel paperId="p1" token="tok" onClose={onClose} />);
  await userEvent.click(screen.getByLabelText(/close/i));
  expect(onClose).toHaveBeenCalled();
});
```

- [ ] **Step 2: Run test to confirm failure**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/ChatPanel.test.tsx
```

Expected: FAIL (module not found).

- [ ] **Step 3: Create ChatPanel.tsx**

```tsx
// frontend/src/components/paper/ChatPanel.tsx
import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, IconButton, Paper, Stack, TextField, Typography } from '@mui/material';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import { papersAPI } from '../../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatPanelProps {
  paperId: string;
  token: string;
  onClose: () => void;
}

const STARTER_PROMPTS = [
  'Explain the key equation in plain English',
  'Does the evaluation actually prove the main claim?',
  'What would I need to reproduce this?',
  'What does this paper assume the reader already knows?',
];

export const ChatPanel: React.FC<ChatPanelProps> = ({ paperId, token, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMessage: Message = { role: 'user', content: text.trim() };
    const next = [...messages, userMessage];
    setMessages(next);
    setInput('');
    setLoading(true);
    try {
      const { reply } = await papersAPI.chat(paperId, next, token);
      setMessages([...next, { role: 'assistant', content: reply }]);
    } catch {
      setMessages([...next, { role: 'assistant', content: 'Something went wrong. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper
      sx={{
        p: { xs: 2, md: 2.5 },
        borderRadius: 6,
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 168px)',
        minHeight: 480,
      }}
    >
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
        <Typography variant="h6">Chat with paper</Typography>
        <IconButton aria-label="close chat" size="small" onClick={onClose}>
          <CloseRoundedIcon fontSize="small" />
        </IconButton>
      </Stack>

      {/* Message list */}
      <Box sx={{ flex: 1, overflowY: 'auto', mb: 1.5 }}>
        {messages.length === 0 ? (
          <Stack spacing={1} sx={{ pt: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>
              Try one of these
            </Typography>
            {STARTER_PROMPTS.map((p) => (
              <Box
                key={p}
                component="button"
                onClick={() => send(p)}
                sx={{
                  textAlign: 'left',
                  p: 1.25,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 3,
                  cursor: 'pointer',
                  bgcolor: 'transparent',
                  fontFamily: 'inherit',
                  fontSize: 13,
                  color: 'text.primary',
                  '&:hover': { bgcolor: 'action.hover' },
                  width: '100%',
                }}
              >
                {p}
              </Box>
            ))}
          </Stack>
        ) : (
          <Stack spacing={1.25} sx={{ pt: 0.5 }}>
            {messages.map((msg, i) => (
              <Box
                key={i}
                sx={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '88%',
                  px: 1.75,
                  py: 1.25,
                  borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                  bgcolor: msg.role === 'user' ? 'primary.main' : 'action.hover',
                  color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                  border: '1px solid',
                  borderColor: msg.role === 'user' ? 'primary.main' : 'divider',
                }}
              >
                <Typography variant="body2" sx={{ lineHeight: 1.6 }}>{msg.content}</Typography>
              </Box>
            ))}
            {loading && (
              <Box sx={{ alignSelf: 'flex-start', px: 2, py: 1.25, bgcolor: 'action.hover', borderRadius: '14px 14px 14px 4px', border: '1px solid', borderColor: 'divider' }}>
                <CircularProgress size={14} />
              </Box>
            )}
            <div ref={bottomRef} />
          </Stack>
        )}
      </Box>

      {/* Input */}
      <Stack direction="row" spacing={1} alignItems="flex-end">
        <TextField
          fullWidth
          size="small"
          multiline
          maxRows={4}
          placeholder="Ask a question…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          disabled={loading}
        />
        <IconButton
          color="primary"
          onClick={() => send(input)}
          disabled={!input.trim() || loading}
          sx={{ border: '1px solid', borderColor: 'primary.main', borderRadius: 3 }}
        >
          <SendRoundedIcon fontSize="small" />
        </IconButton>
      </Stack>
      <Typography variant="caption" color="text.secondary" align="center" sx={{ mt: 0.75 }}>
        Rate-limited · 20 messages / min
      </Typography>
    </Paper>
  );
};
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd frontend && npm test -- --run src/components/paper/__tests__/ChatPanel.test.tsx
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/paper/ChatPanel.tsx frontend/src/components/paper/__tests__/ChatPanel.test.tsx
git commit -m "feat: add ChatPanel with starter prompts, message bubbles, and send/receive"
```

---

## Task 14: KnowledgeGraphViz tooltip enhancement

**Files:**
- Modify: `frontend/src/components/paper/KnowledgeGraphViz.tsx`

The existing component already has a D3 `div` tooltip showing `label`, `definition`, and `category`. The enhancement: improve tooltip HTML to show category as a styled badge, and keep the existing hover interaction (no new behavior needed since the existing tooltip already does what's required).

- [ ] **Step 1: Read the existing tooltip section**

Open `frontend/src/components/paper/KnowledgeGraphViz.tsx` and locate the `nodes.on('mouseover', ...)` block (around line 142).

- [ ] **Step 2: Update the tooltip HTML in the mouseover handler**

Replace the `nodes.on('mouseover', ...)` block with:

```ts
nodes
  .on('mouseover', (_event, d) => {
    tooltip.style('visibility', 'visible').html(
      `<div style="font-weight:700;margin-bottom:4px">${d.label}</div>` +
      `<div style="display:inline-block;padding:2px 8px;border-radius:6px;border:1px solid ${theme.palette.divider};font-size:11px;margin-bottom:6px;opacity:0.75">${d.category}</div>` +
      `<div style="opacity:0.8;line-height:1.5">${d.definition || 'No definition available.'}</div>`
    );
  })
  .on('mousemove', (event) => {
    tooltip.style('top', (event.pageY - 10) + 'px').style('left', (event.pageX + 10) + 'px');
  })
  .on('mouseout', () => {
    tooltip.style('visibility', 'hidden');
  });
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/paper/KnowledgeGraphViz.tsx
git commit -m "feat: improve KnowledgeGraphViz tooltip with category badge styling"
```

---

## Task 15: PaperPage restructure

**Files:**
- Modify: `frontend/src/pages/PaperPage.tsx`

This is the final wiring step. `PaperPage.tsx` becomes an orchestrator that uses all new components. The old inline tab content is removed.

- [ ] **Step 1: Read the current PaperPage.tsx in full before touching it**

Confirm you have read `frontend/src/pages/PaperPage.tsx` (700 lines, currently all inline).

- [ ] **Step 2: Replace PaperPage.tsx with the restructured orchestrator**

Replace the full file contents:

```tsx
// frontend/src/pages/PaperPage.tsx
import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Button, Container, Drawer, Paper, Snackbar, Alert,
  Stack, Tab, Tabs, Typography, useMediaQuery,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import OpenInNewRoundedIcon from '@mui/icons-material/OpenInNewRounded';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import { useAuth } from '../hooks/useAuth';
import { AppErrorInfo, getApiErrorInfo, papersAPI } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { ProcessingProgress } from '../components/common/ProcessingProgress';
import { WorkspaceHeader } from '../components/paper/WorkspaceHeader';
import { PaperAtAGlance } from '../components/paper/PaperAtAGlance';
import { AnatomyView } from '../components/paper/anatomy/AnatomyView';
import { ChatPanel } from '../components/paper/ChatPanel';
import { KnowledgeGraphViz } from '../components/paper/KnowledgeGraphViz';
import { TermGlossary } from '../components/paper/TermGlossary';
import { FormulaBlock } from '../components/paper/FormulaBlock';
import { PaperAnalysis, FormulaExplanation } from '../types';

type ReadingLevel = 'general' | 'technical' | 'eli5';
type RightPanel = 'paper' | 'chat' | null;

const getProcessingFailureHint = (errorMessage?: string) => {
  const normalized = errorMessage?.toLowerCase() || '';
  if (normalized.includes('download pdf'))
    return 'PaperRelay could not download the PDF from arXiv. Retry in a moment, or confirm that the paper PDF is publicly accessible.';
  if (normalized.includes('parsing'))
    return 'The PDF was found but could not be parsed cleanly. Retrying may help for transient extraction issues.';
  if (normalized.includes('ai processing') || normalized.includes('service unavailable') || normalized.includes('timeout'))
    return 'The paper was fetched, but the analysis step could not finish. Retry after the upstream service recovers.';
  return 'Retry the analysis. If the same paper keeps failing, inspect the backend and worker logs.';
};

export const PaperPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [displaySummary, setDisplaySummary] = useState<PaperAnalysis['summary']>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppErrorInfo | null>(null);
  const [tab, setTab] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [readingLevel, setReadingLevel] = useState<ReadingLevel>('general');
  const [rightPanel, setRightPanel] = useState<RightPanel>(null);
  const [reformatError, setReformatError] = useState(false);
  const [completionNoticeOpen, setCompletionNoticeOpen] = useState(false);
  const previousStatusRef = useRef<PaperAnalysis['status'] | null>(null);

  // Fetch + poll
  useEffect(() => {
    if (!user || !paperId) { navigate('/'); return; }
    let mounted = true;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const fetchAnalysis = async () => {
      try {
        const result = await papersAPI.getAnalysis(paperId, user.token);
        if (!mounted) return;
        setAnalysis(result);
        setDisplaySummary(result.summary);
        setError(null);
        if (result.status === 'processing' || result.status === 'pending')
          timeoutId = setTimeout(fetchAnalysis, 3000);
      } catch (err: any) {
        if (!mounted) return;
        setError(getApiErrorInfo(err, 'Failed to load the paper analysis.'));
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchAnalysis();
    return () => { mounted = false; if (timeoutId) clearTimeout(timeoutId); };
  }, [paperId, user, navigate, reloadKey]);

  // Completion notification
  useEffect(() => {
    if (!paperId || !analysis) return;
    const watchKey = `paperrelay-analysis-watch:${paperId}`;
    const notifiedKey = `paperrelay-analysis-complete:${paperId}`;
    const permissionKey = `paperrelay-notification-permission-requested:${paperId}`;
    const previousStatus = previousStatusRef.current;

    if (analysis.status === 'processing' || analysis.status === 'pending') {
      sessionStorage.setItem(watchKey, '1');
      sessionStorage.removeItem(notifiedKey);
      if ('Notification' in window && Notification.permission === 'default' && !sessionStorage.getItem(permissionKey)) {
        sessionStorage.setItem(permissionKey, '1');
        Notification.requestPermission().catch(() => undefined);
      }
    }

    const wasBeingTracked = sessionStorage.getItem(watchKey) === '1';
    const alreadyNotified = sessionStorage.getItem(notifiedKey) === '1';
    const transitionedToComplete = analysis.status === 'complete' && previousStatus !== 'complete' && previousStatus !== null;
    const completedAfterWatch = analysis.status === 'complete' && wasBeingTracked && !alreadyNotified;

    if (transitionedToComplete || completedAfterWatch) {
      setCompletionNoticeOpen(true);
      sessionStorage.setItem(notifiedKey, '1');
      sessionStorage.removeItem(watchKey);
      if ('Notification' in window && Notification.permission === 'granted' && document.visibilityState === 'hidden') {
        const notification = new Notification('PaperRelay analysis ready', {
          body: analysis.title || 'Your paper distillation is complete.',
          tag: `paperrelay-analysis-${paperId}`,
        });
        notification.onclick = () => { window.focus(); notification.close(); };
      }
    }
    if (analysis.status === 'failed') sessionStorage.removeItem(watchKey);
    previousStatusRef.current = analysis.status;
  }, [analysis, paperId]);

  // Reading level change — calls reformat, merges fields into displaySummary
  const handleReadingLevelChange = async (level: ReadingLevel) => {
    setReadingLevel(level);
    if (level === 'general') {
      setDisplaySummary(analysis?.summary);
      return;
    }
    if (!paperId || !user) return;
    try {
      const { reformatted_fields } = await papersAPI.reformat(paperId, level, user.token);
      setDisplaySummary((prev) => prev ? { ...prev, ...reformatted_fields } : prev);
    } catch {
      setReformatError(true);
      setReadingLevel('general');
      setDisplaySummary(analysis?.summary);
    }
  };

  const handleRightPanelChange = (panel: RightPanel) => setRightPanel(panel);

  if (loading) return <LoadingSpinner message="Loading paper analysis..." />;

  if (error || !analysis) {
    return (
      <Container maxWidth="md">
        <Box sx={{ mt: 8 }}>
          <ErrorBanner
            title={error?.title || 'Paper not found'}
            message={error?.message || 'The requested paper analysis could not be loaded.'}
            hint={error?.hint}
            actions={
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                <Button variant="contained" onClick={() => { setLoading(true); setError(null); setReloadKey((v) => v + 1); }}>Retry</Button>
                <Button variant="outlined" onClick={() => navigate('/library')}>Back to library</Button>
              </Stack>
            }
          />
        </Box>
      </Container>
    );
  }

  if (analysis.status === 'processing' || analysis.status === 'pending' || analysis.status === 'failed') {
    return (
      <Container maxWidth="md">
        <Box sx={{ mt: 8 }}>
          <ProcessingProgress
            progressStep={analysis.progress_step}
            progressPercent={analysis.progress_percent}
            status={analysis.status}
            errorMessage={analysis.error_message}
            errorHint={analysis.status === 'failed' ? getProcessingFailureHint(analysis.error_message) : undefined}
            actions={analysis.status === 'failed' ? (
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                <Button variant="contained" onClick={() => navigate('/')}>Analyze another paper</Button>
                <Button variant="outlined" onClick={() => setReloadKey((v) => v + 1)}>Refresh status</Button>
              </Stack>
            ) : undefined}
          />
        </Box>
      </Container>
    );
  }

  const originalPaperUrl = analysis.pdf_url || (analysis.arxiv_id ? `https://arxiv.org/pdf/${analysis.arxiv_id}.pdf` : '');
  const isMathHeavy = analysis.summary?.paper_map?.math_relevance === 'heavy';

  const renderPaperViewer = (embedded: boolean) => (
    <Paper sx={{ p: { xs: 2, md: 2.5 }, borderRadius: embedded ? 6 : 0, display: 'flex', flexDirection: 'column', height: embedded ? 'calc(100vh - 168px)' : '100%', minHeight: embedded ? 680 : '100vh', boxShadow: embedded ? undefined : 'none' }}>
      <Stack spacing={2} sx={{ height: '100%' }}>
        <Stack direction="row" spacing={1.25} justifyContent="space-between" alignItems="flex-start">
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="overline" color="text.secondary">Original paper</Typography>
            <Typography variant="h6">Source PDF</Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            {originalPaperUrl && (
              <Button size="small" variant="outlined" endIcon={<OpenInNewRoundedIcon />} component="a" href={originalPaperUrl} target="_blank" rel="noreferrer">Open</Button>
            )}
            {!embedded && (
              <Button size="small" variant="text" startIcon={<CloseRoundedIcon />} onClick={() => setRightPanel(null)}>Close</Button>
            )}
          </Stack>
        </Stack>
        <Box sx={{ flex: 1, minHeight: 0, overflow: 'hidden', borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
          {originalPaperUrl ? (
            <Box component="iframe" src={originalPaperUrl} title={analysis.title || 'Original paper PDF'} sx={{ width: '100%', height: '100%', minHeight: embedded ? 560 : '100vh', border: 0 }} />
          ) : (
            <Stack spacing={2} justifyContent="center" alignItems="flex-start" sx={{ p: 3, height: '100%' }}>
              <Typography>No source PDF URL is available for this paper.</Typography>
            </Stack>
          )}
        </Box>
      </Stack>
    </Paper>
  );

  const renderRightPanel = () => {
    if (rightPanel === 'paper') return renderPaperViewer(true);
    if (rightPanel === 'chat') return (
      <ChatPanel paperId={paperId!} token={user!.token} onClose={() => setRightPanel(null)} />
    );
    return null;
  };

  const showRightColumn = rightPanel !== null && isDesktop;

  return (
    <Container maxWidth={showRightColumn ? 'xl' : 'lg'}>
      <Box sx={{ display: 'grid', gap: 3, gridTemplateColumns: showRightColumn ? 'minmax(0, 1.45fr) minmax(360px, 0.9fr)' : 'minmax(0, 1fr)', alignItems: 'start' }}>
        <Box sx={{ display: 'grid', gap: 3, minWidth: 0 }}>

          <WorkspaceHeader
            readingLevel={readingLevel}
            onReadingLevelChange={handleReadingLevelChange}
            rightPanel={rightPanel}
            onRightPanelChange={handleRightPanelChange}
            hasPaperUrl={!!originalPaperUrl}
          />

          <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 6 }}>
            {analysis.summary?.paper_map && (
              <Box sx={{ mb: 3 }}>
                <PaperAtAGlance
                  paperMap={analysis.summary.paper_map}
                  critique={analysis.summary.critique}
                />
              </Box>
            )}

            <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
              <Tab label="Anatomy" />
              {isMathHeavy && <Tab label="Math" />}
              <Tab label="Knowledge Graph" />
            </Tabs>

            {/* Anatomy tab */}
            {tab === 0 && displaySummary && (
              <AnatomyView summary={displaySummary} />
            )}

            {/* Math tab — only shown when math_relevance === 'heavy' */}
            {isMathHeavy && tab === 1 && displaySummary && (
              <Stack spacing={2}>
                <Typography variant="h5">Formula explanations</Typography>
                {displaySummary.formula_explanations?.length ? (
                  displaySummary.formula_explanations.map((f: FormulaExplanation, i: number) => (
                    <Paper key={f.latex || i} sx={{ p: 2.5, borderRadius: 5 }}>
                      <FormulaBlock formula={f} />
                    </Paper>
                  ))
                ) : (
                  <Paper sx={{ p: 3, borderRadius: 5 }}>
                    <Typography color="text.secondary">No equation-level explanation was recovered for this paper.</Typography>
                  </Paper>
                )}
              </Stack>
            )}

            {/* Knowledge Graph tab — index depends on whether Math tab is shown */}
            {tab === (isMathHeavy ? 2 : 1) && (
              <>
                {analysis.knowledge_graph ? (
                  <Stack spacing={3}>
                    <KnowledgeGraphViz data={analysis.knowledge_graph} />
                    {analysis.summary?.terms?.length ? (
                      <TermGlossary terms={analysis.summary.terms} />
                    ) : null}
                  </Stack>
                ) : (
                  <Typography>No knowledge graph data available for this paper.</Typography>
                )}
              </>
            )}
          </Paper>
        </Box>

        {showRightColumn && (
          <Box sx={{ position: 'sticky', top: 24, alignSelf: 'start' }}>
            {renderRightPanel()}
          </Box>
        )}
      </Box>

      {/* Mobile drawer for right panels */}
      <Drawer
        anchor="right"
        open={rightPanel !== null && !isDesktop}
        onClose={() => setRightPanel(null)}
        PaperProps={{ sx: { width: '100%', maxWidth: 960 } }}
      >
        {renderRightPanel()}
      </Drawer>

      <Snackbar open={reformatError} autoHideDuration={5000} onClose={() => setReformatError(false)} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert severity="error" variant="filled" onClose={() => setReformatError(false)}>
          Could not reformat the paper. Reverted to General view.
        </Alert>
      </Snackbar>

      <Snackbar open={completionNoticeOpen} autoHideDuration={6000} onClose={() => setCompletionNoticeOpen(false)} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert onClose={() => setCompletionNoticeOpen(false)} severity="success" variant="filled" sx={{ width: '100%' }}>
          {analysis.title ? `Analysis ready: ${analysis.title}` : 'Paper analysis is ready.'}
        </Alert>
      </Snackbar>
    </Container>
  );
};
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Run all frontend tests**

```bash
cd frontend && npm test -- --run
```

Expected: all tests PASS.

- [ ] **Step 5: Run lint**

```bash
cd frontend && npm run lint
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/PaperPage.tsx
git commit -m "feat: restructure PaperPage to use anatomy view, chat panel, and workspace header"
```

---

## Task 16: Full stack smoke test

- [ ] **Step 1: Start the full stack**

```bash
docker compose up --build
```

- [ ] **Step 2: Open http://localhost:3000 and verify**

- [ ] Library page loads; delete button appears on each card.
- [ ] Clicking delete opens confirm dialog; cancel leaves card; confirm removes it.
- [ ] Open an existing completed paper. Workspace header shows General / Technical / ELI5 control.
- [ ] Anatomy tab shows sections for any paper with `problem_and_motivation` data.
- [ ] Clicking "Technical" calls `/api/papers/{id}/reformat`; prose updates.
- [ ] Clicking "Chat" opens the chat panel; paper viewer closes if it was open.
- [ ] Sending a chat message gets a reply.
- [ ] Knowledge Graph tab shows graph + term glossary below; hovering a node shows tooltip with definition.
- [ ] For a math-heavy paper (`math_relevance: "heavy"`), Math tab appears between Anatomy and Knowledge Graph.

- [ ] **Step 3: Run full backend test suite to confirm nothing regressed**

```bash
docker compose run --rm backend uv run pytest -q
```

Expected: all tests PASS.

- [ ] **Step 4: Commit any final fixups, then push the branch**

```bash
git push origin feat/backend-pipeline-expansion
```
