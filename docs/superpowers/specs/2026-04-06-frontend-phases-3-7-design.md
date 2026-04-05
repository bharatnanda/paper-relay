# Frontend Phases 3–7 Design

**Date:** 2026-04-06
**Branch:** feat/backend-pipeline-expansion
**Scope:** Phases 3–7 from TODO.md — anatomy view redesign, chat panel, KG improvements, quick wins, and polish. No standalone visual revamp.

---

## Decisions

| # | Decision |
|---|---|
| D1 | Navigation within anatomy view: pure vertical scroll, no in-page nav bar |
| D2 | Reading level control (General / Technical / ELI5) lives in the workspace header |
| D3 | Chat panel and paper viewer are mutually exclusive — one active right column at a time |
| D4 | Implementation strategy: incremental layering (anatomy → chat → KG → polish) |

---

## Target Component Structure

After all phases land, `PaperPage.tsx` becomes an orchestrator (~150 lines). All content lives in focused components:

```
src/
├── pages/
│   └── PaperPage.tsx                  ← orchestration only
├── components/paper/
│   ├── WorkspaceHeader.tsx            ← title, reading level segmented control, "View paper" + "Chat" buttons
│   ├── PaperAtAGlance.tsx             ← paper type badge, math level chip, reader orientation blurb
│   ├── CritiqueIndicator.tsx          ← "⚠ N quality notes" chip + side drawer listing issues
│   ├── ChatPanel.tsx                  ← right column (desktop) / full-screen drawer (mobile)
│   ├── anatomy/
│   │   ├── AnatomyView.tsx            ← scrollable container, sequences section components
│   │   ├── ProblemSection.tsx         ← problem_and_motivation
│   │   ├── PriorArtSection.tsx        ← prior_work_and_gap
│   │   ├── IdeaSection.tsx            ← core_intuition
│   │   ├── MethodSection.tsx          ← method_deep_dive + inline formulas (where_it_appears matching "method")
│   │   ├── EvidenceSection.tsx        ← results_and_evidence + results_view + artifact chips
│   │   ├── VerdictSection.tsx         ← authors_claims / evidence_assessment side-by-side cards
│   │   └── TakeawaysSection.tsx       ← reader_takeaways as left-bordered list items
│   ├── KnowledgeGraphViz.tsx          ← existing; gets node hover/click popover wired in
│   ├── TermGlossary.tsx               ← searchable table of summary.terms
│   └── FormulaBlock.tsx               ← existing; gets intuition, prerequisites, where_it_appears display
```

---

## Tab Layout (after Phase 4)

| Tab | Label | Visible when | Content |
|---|---|---|---|
| 0 | Anatomy | always | `AnatomyView` (replaces Summary + Walkthrough) |
| 1 | Math | `paper_map.math_relevance === "heavy"` | Full `FormulaBlock` list |
| 2 | Knowledge Graph | always | `KnowledgeGraphViz` + `TermGlossary` below |

The old Summary and Walkthrough tabs are removed. Their content moves into anatomy sections.

---

## Right Column Behavior

"View paper" and "Chat" buttons in `WorkspaceHeader` are mutually exclusive:
- Clicking either one opens that panel and closes the other.
- On desktop (≥lg): active panel renders as a sticky side column alongside the anatomy.
- On mobile (<lg): active panel renders as a full-screen MUI `Drawer` anchored right.
- Both buttons have an active/contained visual state when their panel is open.

---

## Phase 3 — Quick Wins

### 3b. PaperAtAGlance card
- New component `PaperAtAGlance.tsx`
- Renders above `AnatomyView` inside the anatomy tab
- Shows: `paper_map.paper_type` (badge, primary color), `paper_map.math_relevance` (chip), `paper_map.reader_orientation` (blurb text)
- Also hosts `CritiqueIndicator` chip on the right side when `summary.critique?.issues?.length > 0`
- All data already present in `summary.paper_map` — zero new API calls

### 3c. Paper deletion
- Trash icon button on `PaperCard.tsx` in the library
- Clicking opens a MUI `Dialog` with title "Delete paper?" and confirm/cancel actions
- On confirm: calls `papersAPI.delete(paperId, token)` (wraps existing `DELETE /api/papers/{id}`)
- On success: removes the paper from local `papers` state without page reload
- `papersAPI.delete` needs to be added to `services/api.ts`

---

## Phase 4 — Anatomy View Redesign

### WorkspaceHeader
- Replaces the inline header block in `PaperPage.tsx`
- Props: `analysis`, `readingLevel`, `onReadingLevelChange`, `rightPanel`, `onRightPanelChange`
- `rightPanel` type: `"paper" | "chat" | null`
- Contains: title/subtitle copy, segmented control (General / Technical / ELI5), "View paper" button, "Chat" button
- Reading level change calls `papersAPI.reformat(paperId, level, token)`, merges returned `reformatted_fields` into local display state via a `displaySummary` derived state in `PaperPage`

### AnatomyView
- Receives `summary` and `displaySummary` (reformatted override)
- Renders sections in fixed order: Problem → Prior Art → Idea → Method → Evidence → Verdict → Takeaways
- Skips a section entirely if its source field is absent/empty
- Each section component receives only the fields it needs — no whole-summary prop drilling

### Section components (shared anatomy)
Each section follows this structure:
- Icon (28×28 rounded square, tinted background) + bold label
- Prose content from the relevant `summary` field
- Optional sub-content (inline formula card, artifact chips, verdict split, takeaway list)

| Section | Icon | Source fields | Sub-content |
|---|---|---|---|
| Problem | 🎯 blue | `problem_and_motivation` | — |
| Prior Art | 📚 green | `prior_work_and_gap` | — |
| Idea | 💡 amber | `core_intuition` | — |
| Method | ⚙️ purple | `method_deep_dive` | Inline formula cards for `formula_explanations` where `where_it_appears?.toLowerCase().includes("method")` is true |
| Evidence | 📊 green | `results_and_evidence`, `results_view`, `artifact_interpretations` | Artifact chips with confidence color (green=high, amber=medium/low); raw figure/table snapshots below a "Show raw extracts" toggle |
| Verdict | ⚖️ blue | `authors_claims`, `evidence_assessment` | Two-card side-by-side grid |
| Takeaways | ✅ amber | `reader_takeaways` | Left-bordered list items |

### FormulaBlock updates
- Show `intuition` text above the LaTeX block
- Show `prerequisites` as small outlined chips below the intuition
- Show `where_it_appears` as a muted label

### CritiqueIndicator
- Chip: "⚠ N quality notes" in warning color; only renders when `issues.length > 0`
- Clicking opens a MUI `Drawer` (right, 400px wide) listing each issue:
  - Severity badge (high=red, medium=amber, low=grey)
  - Type label (`overclaim`, `missing_caveat`, etc.)
  - Description text
  - Suggested fix in a muted block

---

## Phase 5 — Knowledge Graph Improvements

### Node hover/click popover
- D3 `mouseover` event on nodes shows a MUI `Popover` anchored to cursor position
- Popover content: `node.label` (bold), `node.category` (chip), `node.definition` (body text)
- `mouseout` dismisses; click pins the popover until dismissed

### TermGlossary
- New component rendered below `KnowledgeGraphViz` in the Knowledge Graph tab
- MUI `Table` with columns: Term, Category (chip), Definition
- `TextField` with search icon above the table; filters rows client-side on `term` and `definition`
- Source: `summary.terms`

---

## Phase 6 — Chat Panel

### ChatPanel component
- Props: `paperId`, `token`, `onClose`
- State: `messages: {role: "user"|"assistant", content: string}[]`
- Empty state: header + 4 starter prompt chips (full width, clickable to pre-fill input)
  1. "Explain the key equation in plain English"
  2. "Does the evaluation actually prove the main claim?"
  3. "What would I need to reproduce this?"
  4. "What does this paper assume the reader already knows?"
- Active state: scrollable message list; user bubbles right-aligned (primary tint), assistant bubbles left-aligned (neutral); "···" typing indicator while awaiting reply
- Send: appends user message, calls `papersAPI.chat(paperId, messages, token)`, appends assistant reply
- Rate limit note below input: "Rate-limited · 20 messages / min"
- Close button top-right; `onClose` sets `rightPanel` to `null` in `PaperPage`
- On mobile: rendered inside full-screen MUI `Drawer`

---

## Phase 7 — Polish

- **Low-confidence artifacts:** confidence chip in `EvidenceSection` renders amber/warning when `confidence === "low"` or `"medium"`, green when `"high"`
- **Raw extracts de-emphasis:** `figure_captions` and `tables` move below interpreted artifact cards in `EvidenceSection`; collapsed behind a "Show raw extracts" `Button` toggle; when expanded, rendered at smaller font size and muted border
- **Critique side panel:** described under `CritiqueIndicator` above in Phase 4

---

## Error Handling

- `papersAPI.reformat` failure: show MUI `Snackbar` error; revert `displaySummary` to original `summary`
- `papersAPI.chat` failure: show inline error message in the chat message list (assistant bubble, red tint); allow retry
- `papersAPI.delete` failure: dismiss dialog, show `Snackbar` error; paper stays in list

---

## Out of Scope

- Dark/light theme revamp (deferred)
- Persist chat history to DB (listed as later in TODO.md)
- True figure vision pass (listed as later in TODO.md)
