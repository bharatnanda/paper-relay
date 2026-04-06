# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

PaperRelay transforms arXiv research papers into structured, plain-English walkthroughs via a multi-pass AI distillation pipeline. Users submit an arXiv URL, a background Celery worker downloads, parses, and distills the paper through several LLM calls, and the result is displayed in a tabbed React UI.

## Repository Layout

```
paper-relay/
├── backend/          # FastAPI app + Celery worker (Python, uv)
│   ├── app/
│   │   ├── api/routes/     # FastAPI route handlers (auth, papers, export, share)
│   │   ├── core/           # Config (pydantic-settings), security, rate limiter
│   │   ├── models/         # SQLAlchemy ORM models (Paper, PaperAnalysis, User, ShareLink)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic (ai_processor, pdf_parser, ingestion, export_service, knowledge_graph, email)
│   │   └── workers/        # Celery app + tasks
│   ├── alembic/            # DB migrations (run sequentially: 001 → 004)
│   └── tests/              # pytest tests (api/ and services/ subdirs)
└── frontend/         # React + TypeScript + Vite + MUI
    └── src/
        ├── pages/          # Route-level components (Home, Library, Paper, Login, SharedPaper)
        ├── components/     # UI components (layout, paper tabs, common)
        ├── services/api.ts # All API calls (authAPI, papersAPI, shareAPI)
        ├── hooks/useAuth.ts # Zustand-backed auth state
        └── types/index.ts  # Shared TypeScript types
```

## Development Commands

### Full Stack (Recommended)

```bash
docker compose up --build          # start all services
docker compose down -v             # stop and remove volumes
docker compose logs -f backend     # tail logs for one service
docker compose restart backend     # restart one service
```

### Backend (local with uv)

```bash
cd backend
uv sync --group dev --no-install-project   # install dependencies
uv run alembic upgrade head                 # apply migrations
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
uv run celery -A app.workers.celery_app worker --loglevel=info
```

### Frontend (local)

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev        # Vite dev server
npm run build      # type-check + bundle
npm run lint       # ESLint
npm test -- --run  # Vitest (single run)
```

### Running Tests

Prefer running tests inside Compose (some services need the full runtime dependency set):

```bash
# All backend tests
docker compose run --rm backend uv run pytest

# Targeted API tests
docker compose run --rm backend uv run pytest tests/api/test_auth.py tests/api/test_papers.py tests/api/test_share.py -q

# Targeted service tests
docker compose run --rm backend uv run pytest tests/services/test_ai_processor.py tests/services/test_export_service.py tests/services/test_knowledge_graph.py -q

# Frontend tests
docker compose --profile tools run --rm frontend_tools sh -lc "npm install --legacy-peer-deps --no-audit --no-fund && npm test -- --run"
```

## Architecture

### Backend Pipeline

The core flow is a Celery task (`app/workers/tasks.py: process_paper_task`) that runs the full pipeline synchronously using `asyncio.run()`:

1. **IngestionService** — downloads the arXiv PDF and fetches metadata
2. **PDFParser** — extracts text, sections, formulas, figure captions, and tables via `pdfplumber` / `pymupdf`
3. **AIProcessor** — multi-pass LLM calls using the OpenAI SDK (works against both OpenAI and Azure OpenAI):
   - `map_paper` → identifies structure and main question
   - `distill_sections` → coverage-aware section walkthrough
   - `explain_formulas` / `explain_math_from_sections` → formula explanations with fallback; each formula now includes `intuition`, `prerequisites`, `where_it_appears`
   - `interpret_tables` / `interpret_figures` → evidence interpretation
   - `extract_results_view` → evaluation setup, strongest evidence, caveats
   - `generate_relationships` → LLM-generated `[{source, target, relationship}]` triples for the KG (72%)
   - `synthesize_distillation` → final user-facing output; now includes `prior_work_and_gap`, `core_intuition`, `authors_claims`, `evidence_assessment` (76%)
   - `critique_distillation` → always runs; flags overclaim/missing_caveat/vague_method/evidence_gap/coverage_gap (80%)
   - `revise_with_critique` → conditionally revises only critic-flagged fields when `needs_revision: true` (84%)
   - `repair_distillation` → length check; re-runs if output is too short (88%)
   - `reformat_for_audience` → post-analysis prose rewrite for `general`/`technical`/`eli5` audiences (on-demand, not in pipeline)
   - `chat_with_paper` → multi-turn Q&A using selective `summary_json` fields as context (on-demand)
4. **KnowledgeGraphBuilder** — builds a concept graph from extracted terms, evidence, and LLM-generated relationship triples
5. Results stored as JSONB in `paper_analyses.summary_json` and `paper_analyses.knowledge_graph_json`

Progress is persisted to `paper_analyses.progress_step` / `progress_percent` after each stage so the frontend can poll. The critique result is stored in `summary_json["critique"]`.

### On-Demand Endpoints

Two synchronous endpoints call `AIProcessor` directly (no Celery task):

- `POST /api/papers/{paper_id}/chat` — multi-turn Q&A; rate-limited 20/min; body `{ messages: [{role, content}] }`; returns `{ reply: string }`
- `POST /api/papers/{paper_id}/reformat` — rewrite prose fields for a target audience; rate-limited 10/min; body `{ reading_level: "general"|"technical"|"eli5" }`; returns `{ reformatted_fields: {...} }`; `general` skips the LLM call entirely

### LLM Provider Selection

`AIProcessor._build_client()` reads `settings.LLM_PROVIDER` (`"openai"` or `"azure"`). Azure uses `AsyncOpenAI` pointed at `AZURE_OPENAI_BASE_URL` with the deployment name as `model`. Both paths return an identical `AsyncOpenAI` client, so all LLM call logic is provider-agnostic.

### Auth

Passwordless magic-link flow: `POST /api/auth/request-link` → email with token → `POST /api/auth/verify` → JWT session token. Frontend stores the token in Zustand (persisted to localStorage as `auth-storage`). All authenticated routes expect `Authorization: Bearer <token>`. The axios interceptor in `api.ts` clears localStorage and redirects to `/` on any 401 outside auth routes.

### Database

SQLAlchemy models: `User`, `Paper`, `PaperAnalysis`, `ShareLink`. Migrations in `backend/alembic/versions/` (001–004). Always run `alembic upgrade head` before starting the backend.

### Frontend State

- **Zustand** (`useAuth.ts`) for auth state, persisted to localStorage
- **React Router v6** for client-side routing
- **MUI v5** for components; custom theme in `src/theme.ts`
- **D3** for the knowledge graph visualization (`KnowledgeGraphViz.tsx`)
- **KaTeX** for math rendering (`FormulaBlock.tsx`)

## Environment Variables

Copy `backend/.env.example` and `frontend/.env.example` before running locally. Key backend variables:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `openai` or `azure` |
| `OPENAI_API_KEY` | Required when `LLM_PROVIDER=openai` |
| `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_BASE_URL` / `AZURE_OPENAI_MODEL` | Required when `LLM_PROVIDER=azure` |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Celery broker and result backend |
| `MAGIC_LINK_SECRET` | Signs JWT magic-link tokens |
| `SMTP_HOST` | Email delivery; unset → logs link to console |

## Service Endpoints

- Frontend: `http://localhost:3000`
- Backend API + docs: `http://localhost:8000` / `http://localhost:8000/docs`
- Mailpit inbox (local email): `http://localhost:8025`
- Health check (shows active LLM provider): `GET http://localhost:8000/health`
