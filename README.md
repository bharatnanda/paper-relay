# PaperRelay

PaperRelay is a research paper distillation app for turning arXiv papers into a structured, plain-English walkthrough that a non-expert can follow without losing the core method, evidence, math, and caveats.

## What It Does

PaperRelay is no longer just a short summary flow. The current product is built around:

- passwordless sign-in with magic links
- background paper analysis with progress tracking
- a multi-pass distillation pipeline instead of a single short summary prompt
- section-aware walkthroughs that cover motivation, method, results, and limitations
- interpreted evidence from extracted figures and tables
- formula explanations with nearby context when equation extraction succeeds
- a grounded knowledge graph built from paper concepts plus interpreted evidence
- exports to PDF and Markdown with PaperRelay branding and source-paper links
- public share links for completed analyses
- an embedded source-paper viewer in the paper page
- completion notifications when a background analysis finishes

## Product Flow

1. Sign in with a magic link.
2. Submit an arXiv abstract or PDF URL.
3. Track the job while the backend downloads, parses, distills, and synthesizes the paper.
4. Read the finished analysis in the paper workspace.
5. Open the original paper alongside the distillation when you need to verify details.
6. Export or share the completed result.

## Distillation Model

PaperRelay uses a staged backend pipeline rather than sending the whole paper through one summary prompt.

High-level flow:

1. Parse the paper PDF into text, sections, formulas, figures, and tables.
2. Build a paper map to identify the main question, likely contribution, and important sections.
3. Distill sections with coverage-aware selection so the output includes method, evaluation, results, and limitations.
4. Interpret tables and figures as evidence objects instead of treating them as raw snapshots only.
5. Explain math using extracted equations or method-context fallback.
6. Synthesize the final user-facing distillation and knowledge graph.

This keeps token usage under control while preserving more of the paper than a single short-context pass.

## Frontend Experience

The frontend is centered on a single authenticated shell:

- `Analyze` for starting a new paper analysis
- `Library` for all completed and in-progress papers
- a merged account menu with sign-out

The paper page now includes:

- `Summary`, `Walkthrough`, `Math`, and `Knowledge Graph` tabs
- evaluation setup and strongest evidence callouts
- interpreted evidence cards with confidence labels
- extracted figure/table context
- a toggleable original-paper PDF viewer
- in-app and browser completion notifications for background jobs

The login and auth flow also auto-validates the persisted session on refresh, so stale client state is cleared when the backend session is no longer valid.

## Exports

Completed analyses can be exported as:

- PDF
- Markdown

Exports now include:

- PaperRelay branding
- paper title, authors, arXiv ID
- original paper URL and source PDF URL
- the richer distillation sections
- interpreted evidence from figures and tables
- formula explanations
- knowledge graph summaries

## Current Limits

PaperRelay is still text-first.

Known limitations:

- figure understanding is only as good as extracted captions and surrounding text
- PDF extraction quality varies by paper layout
- heavily image-driven results can still be underexplained
- parser-heavy tests should be run in the Compose/runtime environment where the full dependency set is available

## Auth Model

The intended auth flow is:

- `POST /api/auth/request-link` accepts an email and sends a magic link
- the email points back to the frontend login page with a verification token
- the frontend calls `POST /api/auth/verify`
- the returned session token is used for authenticated API requests
- `GET /api/auth/me` validates the current session during frontend startup

## LLM Provider Configuration

The backend can run against either:

- `openai`
- `azure` for Azure OpenAI / Azure AI Foundry OpenAI-compatible endpoints

### OpenAI

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

### Azure OpenAI / Azure AI Foundry

```bash
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/v1/
AZURE_OPENAI_MODEL=your-deployment-name
```

Notes:

- Azure uses the deployment name as the `model` value.
- Docker Compose passes both OpenAI and Azure env vars through; the backend selects one using `LLM_PROVIDER`.

## Email Delivery

The default Compose stack uses Mailpit:

```bash
SMTP_HOST=mailpit
SMTP_PORT=1025
FROM_EMAIL=noreply@paperrelay.local
```

Mailpit UI is available at `http://localhost:8025`.

If `SMTP_HOST` is unset, the backend falls back to logging the magic link instead of sending a real email.

## Docker Compose

The local stack is designed to run via Docker Compose:

- `frontend`: React app served by nginx
- `backend`: FastAPI API
- `worker`: Celery worker
- `db`: PostgreSQL
- `redis`: Redis broker/result backend
- `mailpit`: local SMTP server and inbox UI

### Build All Services

```bash
docker compose build
```

### Build Selected Services

```bash
docker compose build backend worker frontend
```

### Start the Full Stack

```bash
docker compose up --build
```

### Start Detached

```bash
docker compose up --build -d
```

### Stop the Stack

```bash
docker compose down
```

### Stop and Remove Volumes

```bash
docker compose down -v
```

## Service Endpoints

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`
- Mailpit inbox: `http://localhost:8025`

The backend `GET /health` and `GET /` responses include a non-secret `llm` section showing the active provider and model selection.

## Backend Dependency Management

The backend uses `uv` with [`backend/pyproject.toml`](backend/pyproject.toml).

### Local Backend Setup With uv

```bash
cd backend
uv sync --group dev --no-install-project
```

### Run Backend Locally With uv

```bash
cd backend
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run the Worker Locally With uv

```bash
cd backend
uv run celery -A app.workers.celery_app worker --loglevel=info
```

## Testing

The intended runtime is Docker Compose. Run tests inside containers when you want the closest match to the app environment.

### Backend Tests

```bash
docker compose run --rm backend uv run pytest
```

### Targeted Backend API Tests

```bash
docker compose run --rm backend uv run pytest tests/api/test_auth.py tests/api/test_papers.py tests/api/test_share.py -q
```

### Targeted Backend Service Tests

```bash
docker compose run --rm backend uv run pytest tests/services/test_ai_processor.py tests/services/test_export_service.py tests/services/test_knowledge_graph.py -q
```

### Frontend Tests

```bash
docker compose --profile tools run --rm frontend_tools sh -lc "npm install --legacy-peer-deps --no-audit --no-fund && npm test -- --run"
```

### Frontend Type Check / Build

```bash
docker compose --profile tools run --rm frontend_tools sh -lc "npm install --legacy-peer-deps --no-audit --no-fund && npm run build"
```

## Useful Commands

### Follow Logs

```bash
docker compose logs -f
```

### Follow One Service

```bash
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f frontend
```

### Restart One Service

```bash
docker compose restart backend
```

### Open a Shell in the Backend Container

```bash
docker compose run --rm backend sh
```

### Open a Shell in the Frontend Builder Container

```bash
docker compose --profile tools run --rm frontend_tools sh
```

## Notes

- Set `OPENAI_API_KEY` in `.env` before running the full analysis flow, or configure the Azure variables instead.
- Full end-to-end validation is best done through Compose because the host Python environment may not include all backend dependencies like `reportlab` or `pdfplumber`.
- The `frontend_tools` build can still hit a Rollup optional native dependency issue on some environments.

## Documentation

- [API documentation](docs/API.md)
- [Project TODO / epic tracking](TODO.md)
