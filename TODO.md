# TODO — Implementation Plan

---

## Upfront Decisions (settled)

**D1 — Audience calibration: post-analysis reformat endpoint** ✅
`POST /api/papers/{paper_id}/reformat` accepts `{ reading_level: "general"|"technical"|"eli5" }` and reformats the existing `summary_json` text fields. 2–3 LLM calls max. `general` skips the LLM entirely.

**D2 — Anatomy view: replace tabs** ✅ (decided; frontend work pending)
Replace the 4-tab layout with a sequential anatomy read. Keep a "Source" tab. Keep a secondary Math tab visible only when `paper_map.math_relevance === "heavy"`.

**D3 — Critic pass: always run critique, conditionally run revision** ✅
`critique_distillation` always runs (one LLM call). `revise_with_critique` fires only if `needs_revision: true`.

**D4 — KG relationships: new AIProcessor step** ✅
`generate_relationships()` runs after `extract_terms`, feeds LLM-generated triples into `KnowledgeGraphBuilder` as high-confidence edges.

**D5 — Chat context: selective, not full summary_json** ✅
System prompt built from `guided_walkthrough` + `method_deep_dive` + `results_and_evidence` + `formula_explanations[:6]` + `terms[:12]` + anatomy fields. Full conversation history passed per request.

---

## Phase 0 — Baseline Validation
*Gate: must be done before trusting any quality improvements.*

- [ ] Run end-to-end analysis on at least 5 real arXiv papers: 2 theory-heavy, 2 benchmark-heavy, 1 figure-heavy.
- [ ] Document specific failure modes: where does the distillation go wrong, what sections get skipped, where is math lost.
- [ ] Fix weak PDF extraction fallback (`pdf_parser.py`): when text is near-empty, surface a clear error to the task rather than silently producing a bad distillation.
- [ ] Improve figure/table prompt behavior for papers where these artifacts are the primary evidence vehicle.
- [ ] Run export tests with `reportlab` in a Compose environment.
- [ ] Run parser tests with `pdfplumber` in a Compose environment.

---

## Phase 1 — Backend: Distillation Schema Expansion ✅ COMPLETE

All changes landed on `feat/backend-pipeline-expansion`.

### Done
- **1a.** `synthesize_distillation` output schema expanded with `prior_work_and_gap`, `core_intuition`, `authors_claims`, `evidence_assessment`. `repair_distillation` extended to handle all four.
- **1b.** Formula schema expanded with `intuition`, `prerequisites`, `where_it_appears` per formula.
- **1c.** `critique_distillation(synthesis, paper_map, section_breakdown, results_view, metadata)` — always runs; detects overclaim, missing_caveat, vague_method, evidence_gap, coverage_gap.
- **1d.** `revise_with_critique(synthesis, critique, paper_map, metadata)` — revises only critic-flagged fields; stays grounded.
- **1e.** `generate_relationships(terms, section_breakdown, paper_map)` → `[{source, target, relationship}]` triples fed into `KnowledgeGraphBuilder` as weight-1.5 edges.
- **1f.** `reformat_for_audience(summary_json, reading_level)` — post-analysis prose rewrite; skips LLM on `general`.
- **1g.** `chat_with_paper(messages, summary_json)` — multi-turn chat with full conversation history; retry decorator; graceful fallback when client is None.
- **1h.** Pipeline wired in `tasks.py`: generate_relationships (72%) → synthesize (76%) → critique (80%) → conditional revision (84%) → repair (88%); all new steps wrapped in try/except; critique stored in `summary_json["critique"]`; `relationship_triples` passed to KG builder.

---

## Phase 2 — Backend: New API Endpoints ✅ COMPLETE

### Done
- **2a.** `POST /api/papers/{paper_id}/chat` — auth-gated, rate-limited 20/min, calls `chat_with_paper`, returns `{ reply }`.
- **2b.** `POST /api/papers/{paper_id}/reformat` — auth-gated, rate-limited 10/min, calls `reformat_for_audience`, returns `{ reformatted_fields }`.
- **2c.** Schemas added: `ChatMessage`, `ChatRequest`, `ChatResponse`, `ReformatRequest`, `ReformatResponse`.
- **2d.** `papersAPI.chat()` and `papersAPI.reformat()` added in `frontend/src/services/api.ts`.

---

## Phase 3 — Frontend: Types + Quick Wins

### 3a. Update `types/index.ts` ✅ DONE
- Added to `PaperAnalysis.summary`: `prior_work_and_gap?`, `core_intuition?`, `authors_claims?`, `evidence_assessment?`, `critique?`
- Updated `FormulaExplanation`: added `intuition?`, `prerequisites?`, `where_it_appears?`

### 3b. At-a-glance paper card — pure frontend, zero new data
All fields already in `summary.paper_map`. New component `PaperAtAGlance.tsx`:
- Paper type badge (`paper_map.paper_type`)
- Math level chip (`paper_map.math_relevance`)
- Reader orientation blurb (`paper_map.reader_orientation`)

Render above the anatomy view in `PaperPage.tsx`.

### 3c. Paper deletion button — backend already done
`DELETE /api/papers/{paper_id}` already exists. Add delete button to `PaperCard.tsx` in the library with a confirm dialog. Wire to a new `papersAPI.delete(paperId, token)` call.

---

## Phase 4 — Frontend: Anatomy View Redesign
*Largest frontend change. Work on a branch.*

### 4a. New anatomy section components
Create in `src/components/paper/anatomy/`:
- `AnatomySection.tsx` — base wrapper (title, icon, content slot)
- `ProblemSection.tsx` — `problem_and_motivation`
- `PriorArtSection.tsx` — `prior_work_and_gap`
- `IdeaSection.tsx` — `core_intuition`
- `MethodSection.tsx` — `method_deep_dive` + inline math (formulas with `where_it_appears` matching "method")
- `EvidenceSection.tsx` — `results_and_evidence` + `results_view` + artifact interpretation cards
- `VerdictSection.tsx` — two cards side by side: "What the authors claim" (`authors_claims`) / "What the evidence shows" (`evidence_assessment`)
- `TakeawaysSection.tsx` — `reader_takeaways` as a list

### 4b. Update `FormulaBlock.tsx`
Show `intuition` before the LaTeX block. Show `prerequisites` as a small chip list. Show `where_it_appears` as a label.

### 4c. Restructure `PaperPage.tsx`
Replace the 4-tab layout:
- Tab 0 "Anatomy" → sequential render of all anatomy section components
- Tab 1 "Math" — only visible when `paper_map.math_relevance === "heavy"` — shows full `FormulaBlock` list as reference
- Tab 2 "Knowledge Graph" — unchanged
- Remove the "Summary" and "Walkthrough" tabs (content moves into Anatomy)

Add reading level segmented control to the workspace header. On change: call `papersAPI.reformat()`, merge returned fields into local display state.

### 4d. Critique indicator
If `summary.critique?.issues?.length > 0`: show a small chip "X quality notes" near the workspace header. Clicking opens a side panel listing the critic's issues with severity badges.

---

## Phase 5 — Frontend: Knowledge Graph Improvements

- `KnowledgeGraphViz.tsx`: on node click/hover, show a popover with `node.definition` and `node.category`. D3 already has the data — just wire up the interaction.
- Add `TermGlossary.tsx` below the graph: searchable table of all `summary.terms` — term, category, definition. Filter input at the top.

---

## Phase 6 — Frontend: Chat Panel

### 6a. `ChatPanel.tsx` component
- Slide-out drawer from right edge of the paper workspace
- Message list (user / assistant bubbles)
- Text input + send button
- Starter prompts rendered as chips when history is empty:
  - "Explain the key equation in plain English"
  - "Does the evaluation actually prove the main claim?"
  - "What would I need to reproduce this?"
  - "What does this paper assume the reader already knows?"
- On send: call `papersAPI.chat()`, append assistant reply to local state

### 6b. Wire into `PaperPage.tsx`
Add "Chat" button to the workspace header. Opens `ChatPanel` drawer.

---

## Phase 7 — UI Polish + Engineering

- Add weak-extraction confidence indicators: when `artifact_interpretation.confidence === "low"`, show a muted warning chip on the evidence card.
- De-emphasize raw figure/table snapshots: move them below interpreted evidence cards, reduce visual weight.
- Add API tests for `GET /api/papers/{paper_id}` covering `title`, `authors`, `arxiv_id`, `pdf_url` in the response body.

---

## Later

- True figure understanding via multimodal model pass — send extracted figure regions to a vision model. Highest-value item here; deferred because it requires a separate model call and image extraction plumbing.
- Persist chat history to DB so conversations survive page reload (v2 of Chat).
- Better table normalization if `pdfplumber` extraction is consistently noisy across paper shapes.
- Profile latency of the full critique + revision pass on real papers. If it adds >60s, consider making it opt-in or async.
