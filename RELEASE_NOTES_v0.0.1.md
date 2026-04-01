# PaperRelay v0.1.0 - Initial Release

**Release Date:** April 1, 2026

## Overview

PaperRelay is a research paper distillation application that transforms arXiv papers into structured, plain-English walkthroughs that non-experts can follow without losing core methods, evidence, math, and caveats.

This initial release (v0.1.0) establishes the foundation with passwordless authentication, background paper analysis with progress tracking, and a multi-pass distillation pipeline.

## What's New

### 🔐 Authentication
- Passwordless sign-in with magic links
- Session-based authentication with auto-validation
- Secure email delivery via Mailpit (local) or SMTP

### 📄 Paper Analysis
- Submit arXiv abstract URLs or PDF URLs for analysis
- Background processing with real-time progress tracking
- Multi-pass distillation pipeline (not just single-summary)
- Section-aware walkthroughs covering motivation, method, results, and limitations

### 🧠 Distillation Features
- **Parse**: PDF text, sections, formulas, figures, and tables extraction
- **Map**: Identify main questions, contributions, and important sections
- **Distill**: Coverage-aware section selection
- **Interpret**: Tables and figures as evidence objects with confidence labels
- **Explain**: Math formulas with symbol breakdowns
- **Synthesize**: Final distillation and knowledge graph generation

### 📊 Knowledge Graph
- Grounded knowledge graph built from paper concepts
- Interpreted evidence nodes and edges
- Concept relationships with weights and categories

### 🎨 Frontend Experience
- React-based single-page application
- Material UI design system
- Pages:
  - **Analyze**: Start new paper analysis
  - **Library**: View completed and in-progress papers
  - **Paper Detail**: Summary, Walkthrough, Math, and Knowledge Graph tabs
  - **Shared Papers**: Public access to shared analyses
- Real-time progress indicators
- Completion notifications (in-app and browser)
- Embedded source paper PDF viewer

### 📤 Export & Sharing
- Export to PDF with PaperRelay branding
- Export to Markdown format
- Public share links for completed analyses
- Exports include:
  - Paper metadata (title, authors, arXiv ID)
  - Original paper and source PDF URLs
  - Rich distillation sections
  - Interpreted evidence from figures and tables
  - Formula explanations
  - Knowledge graph summaries

### 🔧 Infrastructure
- FastAPI backend with async support
- Celery workers for background job processing
- PostgreSQL database with SQLAlchemy ORM
- Redis broker for task queues
- Docker Compose for local development
- Support for OpenAI and Azure OpenAI providers


## Getting Started

### Prerequisites
- Docker and Docker Compose
- LLM API key (OpenAI or Azure OpenAI)

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd paper-relay

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your LLM credentials

# Build and start all services
docker compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Mailpit: http://localhost:8025
```

### Configuration

#### OpenAI Provider
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

#### Azure OpenAI Provider
```bash
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/v1/
AZURE_OPENAI_MODEL=your-deployment-name
```

## Known Limitations

- Figure understanding depends on extracted captions and surrounding text
- PDF extraction quality varies by paper layout
- Image-heavy results may be under explained
- Parser-heavy tests require full Docker runtime environment
- Rollup optional native dependency issue in frontend_tools build

## Testing

```bash
# Backend tests
docker compose run --rm backend uv run pytest

# Frontend tests
docker compose --profile tools run --rm frontend_tools sh -lc "npm test -- --run"

# Frontend build check
docker compose --profile tools run --rm frontend_tools sh -lc "npm run build"
```

## Documentation

- [API Documentation](docs/API.md)
- [Project Roadmap](TODO.md)

## What's Next

Planned improvements include:
- Better missing-context indicators
- Enhanced figure/table visualization
- Richer paper metadata (abstract, section list, arXiv categories)
- Manual theme override
- Improved multimodal figure understanding
- Better fallback handling for weak PDF extraction

---
