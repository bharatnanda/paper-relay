# Architecture Review

This document captures the architecture review and simplification work completed so far for PaperRelay, along with the next recommended steps.

## Current System Overview

PaperRelay has three major runtime paths:

1. Backend request path
   - FastAPI routes handle auth-gated paper operations.
   - Papers are created or looked up in Postgres.
   - Long-running analysis work is submitted to Celery.

2. Backend analysis path
   - Celery downloads the PDF, parses it, runs the AI distillation pipeline, builds the knowledge graph, and saves results.

3. Frontend paper workspace
   - React fetches analysis state, polls while processing, renders the paper workspace, and calls chat/reformat endpoints on demand.

## Original Architecture Problems

### 1. Duplicated analysis contract

The same "analysis summary" concept existed in multiple shapes:

- AI synthesis output used keys like `quick_summary`, `eli5_explanation`, `technical_summary`.
- Worker persistence remapped those into stored keys like `quick`, `eli5`, `technical`.
- API response schema exposed `summary` as an untyped `dict`.
- Export code read raw dict fields directly.
- Frontend defined its own parallel TypeScript shape.

This caused contract drift and forced alias logic into business code.

### 2. Route-level orchestration

`backend/app/api/routes/papers.py` was responsible for:

- arXiv URL validation
- existing paper lookup
- creating `Paper` and `PaperAnalysis`
- queue submission state transitions
- completed-analysis lookup rules for chat/reformat

That made the route layer own workflow rules instead of only HTTP concerns.

### 3. Monolithic worker orchestration

`backend/app/workers/tasks.py` mixed too many responsibilities:

- DB session lifecycle
- progress updates
- download and parse checks
- AI orchestration
- critique and revision flow
- graph build
- persistence
- failure handling

The nested async pipeline logic inside the worker was effectively a hidden application service.

### 4. Contract mismatch between persisted and synthesis shapes

Because persisted field names differed from synthesis field names, on-demand operations such as chat and reformat needed alias-handling logic to reconstruct meaning from stored summaries.

### 5. Frontend page owns too much state

`frontend/src/pages/PaperPage.tsx` currently combines:

- loading and polling
- completion notification logic
- reading-level mutation flow
- responsive right-panel state
- tab rendering and layout logic

This is workable, but it is still a future simplification target.

## Simplification Work Completed

### Step 1. Canonical backend summary schema

Completed:

- Added a typed backend summary model in `backend/app/schemas/paper.py`.
- Introduced nested models for critique, sections, paper map, results view, terms, formulas, figures, and tables.
- Changed `PaperAnalysisComplete.summary` from `Optional[dict]` to `Optional[AnalysisSummary]`.

Why this mattered:

- The backend now owns a canonical summary contract.
- Validation happens at the API boundary instead of relying on raw dict usage.
- This reduced drift risk without changing external behavior.

Tests added or updated:

- API test to prove the current stored summary shape is accepted by the typed response schema.

### Step 2. Centralized worker summary mapping

Completed:

- Added `AnalysisSummary.from_pipeline(...)` in `backend/app/schemas/paper.py`.
- Replaced the long inline `analysis.summary_json = {...}` mapping in the worker with:

  - `AnalysisSummary.from_pipeline(...).model_dump()`

Why this mattered:

- The worker no longer owns the persisted summary contract directly.
- Summary mapping now lives next to the canonical schema.
- This lowers the chance of future schema drift when fields are added or renamed.

### Step 3. Extracted route orchestration service

Completed:

- Added `backend/app/services/paper_analysis.py`.
- Moved these responsibilities out of the route layer:
  - queue submission transitions
  - analyze/requeue behavior
  - user paper lookup
  - completed analysis lookup for chat/reformat
- Slimmed `backend/app/api/routes/papers.py` so routes delegate to the service.

Why this mattered:

- Routes are now closer to pure HTTP adapters.
- Workflow logic is easier to test and reuse.
- The service boundary is now the right place for future lifecycle changes.

### Step 4. Extracted analysis pipeline from the Celery worker

Completed:

- Added `backend/app/services/analysis_pipeline.py`.
- Introduced:
  - `AnalysisPipeline`
  - `AnalysisPipelineResult`
- Moved the nested async orchestration out of `backend/app/workers/tasks.py` into the pipeline service.
- Refactored the worker so it now focuses on:
  - loading DB state
  - downloading/parsing prerequisites
  - invoking the pipeline
  - building the knowledge graph
  - saving results
  - marking failures

Why this mattered:

- The worker now behaves like a worker instead of a hidden application service.
- The AI orchestration path has a named seam and structured result object.
- Worker tests can validate worker behavior without mocking every AI stage individually.

### Step 5. Unified canonical summary usage for chat and reformat

Completed:

- Added `AnalysisSummary.from_storage(...)` in `backend/app/schemas/paper.py`.
- Normalized stored summaries at the route boundary before they reach on-demand AI operations.
- Updated chat and reformat flows to operate on canonical summary fields like:
  - `quick`
  - `eli5`
  - `technical`
  - `method_deep_dive`
  - `evidence_assessment`
- Removed alias-table logic from the `AIProcessor` chat/reformat path.

Why this mattered:

- Compatibility is now handled at the storage/API boundary instead of inside business logic.
- `AIProcessor` now speaks one backend summary contract for on-demand operations.
- This removed the last major contract mismatch from the backend runtime path.

### Step 6. Decomposed frontend paper workspace page

Completed:

- Added `frontend/src/hooks/usePaperAnalysis.ts`.
- Added `frontend/src/hooks/useAnalysisCompletionNotice.ts`.
- Refactored `frontend/src/pages/PaperPage.tsx` to delegate:
  - analysis loading and polling
  - reload behavior
  - completion-notification state

Why this mattered:

- `PaperPage.tsx` no longer owns all workspace side effects directly.
- The page now reads more like a composition layer and less like a monolithic controller.
- The frontend structure is now better aligned with the backend refactors already completed.

### Step 7. Typed the export layer around the canonical summary model

Completed:

- Updated `backend/app/api/routes/export.py` to normalize stored summaries with `AnalysisSummary.from_storage(...)`.
- Refactored `backend/app/services/export_service.py` so its public API consumes typed `AnalysisSummary` data instead of raw `summary_json` dicts.
- Moved export rendering to use canonical summary fields and typed nested models for sections, terms, formulas, figures, tables, and results-view artifacts.
- Added the missing `missing_context` field to the canonical `ArtifactInterpretation` schema so normalization no longer drops export content.

Why this mattered:

- Export no longer bypasses the canonical backend summary contract.
- Legacy stored summary shapes are normalized once at the route boundary, matching the chat and reformat paths.
- The remaining backend presentation path that depended on raw summary dict access is now aligned with the typed schema layer.

### Step 8. Normalized the public share route around the canonical summary model

Completed:

- Updated `backend/app/api/routes/share.py` so shared-paper responses normalize stored summaries with `AnalysisSummary.from_storage(...)`.
- Added a typed shared response schema in `backend/app/schemas/paper.py` for the public share payload.
- Tightened the frontend share client and `SharedPaperPage` to consume a typed shared response instead of using `any`.

Why this mattered:

- Public share links no longer bypass canonical summary normalization.
- Shared-paper consumers now see the same summary contract as authenticated paper, chat, reformat, and export flows.
- The share boundary is easier to reason about because its response shape is now explicit on both backend and frontend.

### Step 9. Extracted remaining PaperPage workspace state into focused hooks

Completed:

- Added `frontend/src/hooks/usePaperReadingLevel.ts` to own reading-level selection, reformat API calls, fallback-to-general behavior, and reformat error state.
- Added `frontend/src/hooks/usePaperRightPanel.ts` to own right-panel open/close state for the paper viewer and chat panel.
- Refactored `frontend/src/pages/PaperPage.tsx` so it now composes those hooks instead of directly coordinating those state transitions inline.

Why this mattered:

- `PaperPage.tsx` is now closer to a composition layer and less of a stateful controller.
- Reading-level mutation flow and right-panel behavior now have named seams that are easier to test and evolve independently.
- The remaining frontend page complexity is concentrated in rendering rather than side-effect and UI-state orchestration.

### Step 10. Renamed synthesis-time summary fields to canonical names earlier in the pipeline

Completed:

- Updated `backend/app/services/ai_processor.py` so synthesis, repair, critique, and `generate_summary()` now use canonical internal fields:
  - `quick`
  - `eli5`
  - `technical`
- Updated `backend/app/services/analysis_pipeline.py` to evaluate shallow-summary repair thresholds against canonical fields instead of legacy synthesis names.
- Updated `AnalysisSummary.from_pipeline(...)` to accept either canonical or legacy synthesis keys during the transition, so the persistence boundary stays backward-compatible while upstream code moves to canonical names.

Why this mattered:

- Canonical summary naming now appears earlier in the backend analysis flow rather than only at storage normalization time.
- The internal contract between synthesis, critique, repair, and pipeline orchestration is simpler and more consistent.
- Backward compatibility for older stored summaries remains intact, but new synthesis output no longer needs late aliasing to become canonical.

### Step 11. Replaced remaining internal synthesis dict flow with a typed summary object

Completed:

- Updated `backend/app/services/ai_processor.py` so synthesis, repair, critique, and critique-driven revision now operate on a typed `AnalysisSummary` object instead of raw summary dicts.
- Updated `backend/app/services/analysis_pipeline.py` so `AnalysisPipelineResult.summary` is now a typed `AnalysisSummary`, enriched with critique and extracted analysis artifacts before leaving the pipeline.
- Simplified `backend/app/workers/tasks.py` so persistence now saves `result.summary.model_dump()` directly instead of remapping pipeline output through another summary-construction step.

Why this mattered:

- The internal backend summary contract is now typed not just at storage and route boundaries, but across the AI orchestration path itself.
- Pipeline-to-worker handoff is simpler because the worker now receives a fully assembled typed summary object.
- This removes another source of contract drift by reducing the number of places where summary payloads are reconstructed from loose dictionaries.

## Additional Functional Fixes Completed During Review

The following correctness fixes were also made while simplifying architecture:

1. Persisted new anatomy fields in `summary_json`
   - `prior_work_and_gap`
   - `core_intuition`
   - `authors_claims`
   - `evidence_assessment`

2. Fixed reformat endpoint schema handling
   - `reformat_for_audience()` now returns and consumes canonical summary fields.

3. Fixed chat context schema handling
   - `chat_with_paper()` now consumes canonical stored summary fields.

4. Added targeted tests covering:
   - canonical summary handling in `AIProcessor`
   - worker persistence of anatomy fields
   - typed summary response acceptance
   - route behavior after service extraction
   - export normalization for both service and API paths
   - share-route normalization for public responses
   - page-state decomposition for shared frontend workspace behavior
   - canonical synthesis-field usage earlier in the backend pipeline
   - typed summary-object flow across processor, pipeline, and worker boundaries

## Files Added

- `backend/app/services/paper_analysis.py`
- `backend/app/services/analysis_pipeline.py`
- `backend/tests/workers/test_tasks.py`
- `backend/tests/api/test_export.py`
- `backend/tests/api/test_share.py`
- `frontend/src/hooks/usePaperAnalysis.ts`
- `frontend/src/hooks/useAnalysisCompletionNotice.ts`
- `frontend/src/hooks/usePaperReadingLevel.ts`
- `frontend/src/hooks/usePaperRightPanel.ts`

## Files Meaningfully Refactored

- `backend/app/schemas/paper.py`
- `backend/app/api/routes/papers.py`
- `backend/app/api/routes/export.py`
- `backend/app/api/routes/share.py`
- `backend/app/workers/tasks.py`
- `backend/app/services/ai_processor.py`
- `backend/app/services/analysis_pipeline.py`
- `backend/app/services/export_service.py`
- `backend/tests/api/test_papers.py`
- `frontend/src/services/api.ts`
- `frontend/src/pages/SharedPaperPage.tsx`
- `frontend/src/types/index.ts`
- `backend/tests/services/test_export_service.py`
- `backend/tests/services/test_ai_processor.py`
- `frontend/src/pages/PaperPage.tsx`

## Architecture State After Current Refactors

The backend now has clearer layers:

1. Schema layer
   - Owns the canonical persisted/API summary contract.

2. Route layer
   - Owns HTTP input/output concerns.

3. Analysis service layer
   - Owns paper-analysis lifecycle orchestration.

4. Pipeline layer
   - Owns AI stage orchestration.

5. Worker layer
   - Owns job execution, progress persistence, and result saving.

This is a materially simpler shape than the original implementation.

The backend analysis contract is now effectively unified around the canonical `AnalysisSummary` model for:

- persistence
- API response validation
- worker output conversion
- chat context
- reformat output
- export rendering
- public share responses

The frontend paper workspace now has a clearer split between:

- page composition
- data/polling state
- completion-notification behavior

## Recommended Next Simplification Steps

### Frontend follow-up

Optional future simplification:

- Add page-level tests around `PaperPage.tsx` once the interaction surface expands again.

### Longer-term backend follow-up

Optional future simplification:

- If desired, split `AnalysisSummary` into separate internal and persisted presentation models if the AI-stage contract and API/export contract ever need to diverge.

The main untyped internal summary flow has now been removed, so this is only a future modeling refinement rather than necessary cleanup.

## Test Notes

Targeted backend verification completed during the refactors:

- `tests/api/test_papers.py`
- `tests/services/test_ai_processor.py`
- `tests/workers/test_tasks.py`

Frontend verification completed for the paper-page decomposition:

- `npm test -- --run`
- `npm run build`

Additional backend verification completed for export typing:

- `backend/tests/services/test_export_service.py`
- `backend/tests/api/test_export.py`

Additional verification completed for share-response typing:

- `backend/tests/api/test_share.py`

The current targeted test coverage is strong around the newly introduced backend boundaries, and the frontend decomposition has been validated through build and component tests.
