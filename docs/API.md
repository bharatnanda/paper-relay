# PaperRelay API Documentation

**Last Updated:** 2026-03-31

The paper-distillation endpoints are provider-agnostic. The backend can run with OpenAI or Azure OpenAI / Azure AI Foundry based on server configuration.

## Auth

### Request Magic Link

```http
POST /api/auth/request-link
Content-Type: application/json

{"email": "user@example.com"}
```

Response:

```json
{"message": "Check your email for the magic link", "status": "link_sent"}
```

### Verify Magic Link

```http
POST /api/auth/verify
Content-Type: application/json

{"token": "magic-link-token"}
```

Response:

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "token": "session-token",
  "papers_count": 0
}
```

### Get Current Session User

```http
GET /api/auth/me
Authorization: Bearer <session-token>
```

Response:

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "papers_count": 3
}
```

## Papers

### Analyze Paper

```http
POST /api/papers/analyze
Authorization: Bearer <session-token>
Content-Type: application/json

{"arxiv_url": "https://arxiv.org/abs/2301.12345"}
```

Possible responses:

- `200` with `status="processing"` when a new or requeued job is accepted
- `400` for an invalid arXiv URL
- `404` when the paper is not found on arXiv
- `502` when upstream arXiv metadata fetch fails
- `503` when the backend cannot submit the background job

Example accepted response:

```json
{
  "paper_id": "uuid",
  "status": "processing",
  "message": "Processing started"
}
```

### Get Analysis

```http
GET /api/papers/{paper_id}
Authorization: Bearer <session-token>
```

Possible statuses:

- `pending`
- `processing`
- `complete`
- `failed`

Processing response example:

```json
{
  "paper_id": "uuid",
  "status": "processing",
  "title": "Paper title",
  "authors": ["Author One", "Author Two"],
  "arxiv_id": "2301.12345",
  "pdf_url": "https://arxiv.org/pdf/2301.12345.pdf",
  "progress_step": "Parsing PDF...",
  "progress_percent": 25,
  "error_message": null
}
```

Completed response example:

```json
{
  "paper_id": "uuid",
  "status": "complete",
  "title": "Paper title",
  "authors": ["Author One", "Author Two"],
  "arxiv_id": "2301.12345",
  "pdf_url": "https://arxiv.org/pdf/2301.12345.pdf",
  "summary": {
    "quick": "High-level summary",
    "eli5": "Longer plain-English explanation",
    "technical": "Technical summary fallback",
    "problem_and_motivation": "Why the paper exists",
    "method_deep_dive": "How the method works",
    "results_and_evidence": "What the evidence shows",
    "guided_walkthrough": "Reader-friendly walkthrough",
    "limitations_and_caveats": "Important caveats",
    "key_contributions": ["Contribution 1"],
    "key_findings": ["Finding 1"],
    "reader_takeaways": ["Takeaway 1"],
    "section_breakdown": [
      {
        "title": "Method",
        "summary": "Section summary",
        "why_it_matters": "Why this section matters"
      }
    ],
    "results_view": {
      "evaluation_setup": "How evaluation was run",
      "results_summary": "Concise evidence summary",
      "strongest_evidence": ["Main evidence point"],
      "caveats": ["Evidence caveat"],
      "artifact_interpretations": [
        {
          "artifact_type": "table",
          "label": "Table 1",
          "section_title": "Results",
          "what_it_shows": "Main benchmark comparison",
          "why_it_matters": "Supports the claim",
          "confidence": "high"
        }
      ]
    },
    "artifact_interpretations": [
      {
        "artifact_type": "figure",
        "label": "Figure 2",
        "section_title": "Experiments",
        "what_it_shows": "Ablation trend",
        "why_it_matters": "Shows which component helps",
        "confidence": "medium"
      }
    ],
    "formula_explanations": [
      {
        "latex": "y = mx + b",
        "plain_explanation": "Plain-English explanation",
        "symbols": {"m": "slope"},
        "importance": "Why the equation matters"
      }
    ],
    "figure_captions": [
      {
        "label": "Figure 1",
        "caption": "System overview",
        "page": 0,
        "section_title": "Method",
        "context": "Nearby extracted context"
      }
    ],
    "tables": [
      {
        "title": "Table 1",
        "page": 1,
        "section_title": "Results",
        "row_count": 8,
        "column_count": 4,
        "context": "Nearby extracted context",
        "rows": [["Model", "Score"], ["A", "90"]]
      }
    ],
    "terms": [
      {
        "term": "Agent",
        "category": "concept",
        "definition": "A system that acts in an environment",
        "mentions": 2
      }
    ]
  },
  "knowledge_graph": {
    "nodes": [
      {
        "id": "agent",
        "label": "Agent",
        "category": "concept",
        "definition": "A system that acts in an environment",
        "value": 1
      }
    ],
    "edges": [
      {
        "source": "agent",
        "target": "memory",
        "type": "uses",
        "weight": 1
      }
    ]
  }
}
```

### List Papers

```http
GET /api/papers
Authorization: Bearer <session-token>
```

### Delete Paper

```http
DELETE /api/papers/{paper_id}
Authorization: Bearer <session-token>
```

## Export

### Export Paper

```http
GET /api/papers/{paper_id}/export?format=pdf
Authorization: Bearer <session-token>
```

Supported formats:

- `pdf`
- `md`

Exports include:

- PaperRelay branding
- paper metadata
- original paper/source PDF URL
- richer distillation sections
- interpreted evidence
- math explanations
- knowledge graph summary

## Share

### Create Share Link

```http
POST /api/papers/{paper_id}/share
Authorization: Bearer <session-token>
```

Response:

```json
{"share_url": "/share/<token>"}
```

### Get Shared Paper

```http
GET /api/share/{share_token}
```

The shared response includes:

- paper metadata including `pdf_url`
- completed analysis summary
- knowledge graph payload

## Health

```http
GET /health
```

The health response includes a non-secret `llm` object with the active provider and selected model.
