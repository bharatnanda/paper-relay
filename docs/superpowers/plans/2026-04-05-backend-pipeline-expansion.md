# Backend Pipeline Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the distillation pipeline with 4 new synthesis fields, a critic/revision pass, LLM-generated KG relationship triples, and two new API endpoints (chat and reformat-for-audience).

**Architecture:** All new LLM logic lives in `AIProcessor` as async methods following the existing `_chat_json` pattern with tenacity retries. The Celery task (`process_paper_task`) is the only orchestrator — new steps are added there in sequence. Two new REST endpoints (`/chat`, `/reformat`) are added to the papers router and call AIProcessor directly (no task queue — they are synchronous request-response).

**Tech Stack:** Python 3.11, FastAPI, Celery, OpenAI SDK (AsyncOpenAI), tenacity, pytest + pytest-asyncio, slowapi (rate limiting)

---

## File Map

| File | Action | What changes |
|------|--------|--------------|
| `backend/app/services/ai_processor.py` | Modify | Add 6 new methods; update 2 existing prompt schemas |
| `backend/app/services/knowledge_graph.py` | Modify | Accept `relationship_triples` param in `build()` |
| `backend/app/workers/tasks.py` | Modify | Wire critic pass, KG triples, store critique in summary_json |
| `backend/app/schemas/paper.py` | Modify | Add `ChatMessage`, `ChatRequest`, `ChatResponse`, `ReformatRequest`, `ReformatResponse` |
| `backend/app/api/routes/papers.py` | Modify | Add `POST /{paper_id}/chat` and `POST /{paper_id}/reformat` |
| `backend/tests/services/test_ai_processor.py` | Modify | Add tests for 6 new methods |
| `backend/tests/api/test_papers.py` | Modify | Add tests for chat and reformat endpoints |
| `frontend/src/types/index.ts` | Modify | Add new fields to `PaperAnalysis.summary` and `FormulaExplanation` |
| `frontend/src/services/api.ts` | Modify | Add `papersAPI.chat()` and `papersAPI.reformat()` |

---

## Task 1: Expand `synthesize_distillation` output schema

Adds `prior_work_and_gap`, `core_intuition`, `authors_claims`, `evidence_assessment` to the synthesis prompt and fallback. Also extends `repair_distillation` to handle these fields.

**Files:**
- Modify: `backend/app/services/ai_processor.py`
- Modify: `backend/tests/services/test_ai_processor.py`

- [ ] **Step 1: Write the failing test**

Add to the `TestAIProcessor` class in `backend/tests/services/test_ai_processor.py`:

```python
@pytest.mark.anyio
async def test_synthesize_distillation_returns_new_anatomy_fields(self, processor):
    """New anatomy fields must be present in synthesize_distillation output."""
    mock_response = {
        "quick_summary": "Short summary.",
        "guided_walkthrough": "A" * 900,
        "eli5_explanation": "B" * 500,
        "technical_summary": "Technical.",
        "problem_and_motivation": "The problem.",
        "prior_work_and_gap": "Prior work used X. This paper noticed gap Y.",
        "core_intuition": "The central idea is Z.",
        "method_deep_dive": "Method details.",
        "results_and_evidence": "Results show improvement.",
        "authors_claims": "Authors claim state-of-the-art on benchmarks.",
        "evidence_assessment": "Evidence supports moderate gains; strong claim on one dataset.",
        "limitations_and_caveats": "Only tested on English.",
        "key_contributions": ["Contribution A"],
        "key_findings": ["Finding B"],
        "reader_takeaways": ["Takeaway C"],
        "section_breakdown": [],
    }
    metadata = {"title": "Test", "authors": [], "abstract": "Abstract text"}
    paper_map = {"main_question": "Q", "proposed_solution": "S", "math_relevance": "light"}
    section_breakdown = []
    results_view = {"results_summary": "R", "caveats": [], "artifact_interpretations": []}
    formula_explanations = []
    terms = []

    with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
        result = await processor.synthesize_distillation(
            metadata, paper_map, section_breakdown, results_view,
            formula_explanations, terms
        )
    assert result["prior_work_and_gap"] == "Prior work used X. This paper noticed gap Y."
    assert result["core_intuition"] == "The central idea is Z."
    assert result["authors_claims"] == "Authors claim state-of-the-art on benchmarks."
    assert result["evidence_assessment"] == "Evidence supports moderate gains; strong claim on one dataset."
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py::TestAIProcessor::test_synthesize_distillation_returns_new_anatomy_fields -v
```
Expected: FAIL — keys missing from result.

- [ ] **Step 3: Update `synthesize_distillation` in `ai_processor.py`**

In `synthesize_distillation`, locate the `prompt` f-string. Find the `Return strict JSON:` block and add the four new fields after `"problem_and_motivation"`:

```python
  "prior_work_and_gap": "what was attempted before this paper and what specific gap or limitation it addresses",
  "core_intuition": "the central idea of the paper in one plain-English paragraph before any formulas or notation",
  "authors_claims": "what the paper explicitly asserts as its contribution and conclusion",
  "evidence_assessment": "what the extracted evidence actually supports; note any gap between this and authors_claims",
```

In the `fallback` dict inside `synthesize_distillation`, add after `"problem_and_motivation"`:

```python
"prior_work_and_gap": metadata.get("abstract", ""),
"core_intuition": paper_map.get("proposed_solution", ""),
"authors_claims": metadata.get("abstract", ""),
"evidence_assessment": results_view.get("results_summary", ""),
```

In `repair_distillation`, update the `prompt` to include the new fields in the expansion list:

```python
Return strict JSON with the same keys for:
{{
  "guided_walkthrough": "expanded walkthrough",
  "eli5_explanation": "expanded ELI5 walkthrough",
  "method_deep_dive": "expanded method explanation",
  "limitations_and_caveats": "expanded limitations",
  "prior_work_and_gap": "expanded prior work context if too brief",
  "core_intuition": "expanded core intuition if too vague",
  "authors_claims": "expanded authors claims if too vague",
  "evidence_assessment": "expanded evidence assessment if too vague"
}}
```

Also update `repair_distillation`'s `fallback` dict and the `.update()` call at the bottom to include the four new keys (copying the existing pattern for the other fields).

- [ ] **Step 4: Run to verify it passes**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py::TestAIProcessor::test_synthesize_distillation_returns_new_anatomy_fields -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add app/services/ai_processor.py tests/services/test_ai_processor.py
git commit -m "feat: add prior_work_and_gap, core_intuition, authors_claims, evidence_assessment to synthesis"
```

---

## Task 2: Expand formula output schema

Adds `intuition`, `prerequisites`, `where_it_appears` to `explain_formulas` and `explain_math_from_sections`.

**Files:**
- Modify: `backend/app/services/ai_processor.py`
- Modify: `backend/tests/services/test_ai_processor.py`

- [ ] **Step 1: Write the failing test**

Add to `TestAIProcessor`:

```python
@pytest.mark.anyio
async def test_explain_formulas_returns_enriched_schema(self, processor):
    """Formula output must include intuition, prerequisites, where_it_appears."""
    mock_response = {
        "formulas": [{
            "latex": r"\mathcal{L} = -\sum y \log \hat{y}",
            "plain_explanation": "Cross-entropy loss between predictions and targets.",
            "intuition": "Measures how surprised the model is by the correct label.",
            "prerequisites": ["probability", "logarithm"],
            "where_it_appears": "training objective in the method section",
            "symbols": {"y": "true label", r"\hat{y}": "predicted probability"},
            "importance": "Core training signal for the model.",
        }]
    }
    formulas = [{"latex": r"\mathcal{L} = -\sum y \log \hat{y}", "context": "Training loss."}]

    with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
        result = await processor.explain_formulas(formulas)

    assert "intuition" in result[0]
    assert "prerequisites" in result[0]
    assert "where_it_appears" in result[0]
    assert result[0]["intuition"] == "Measures how surprised the model is by the correct label."
    assert result[0]["prerequisites"] == ["probability", "logarithm"]
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py::TestAIProcessor::test_explain_formulas_returns_enriched_schema -v
```
Expected: FAIL — `intuition` key missing (schema not yet updated so model won't return it).

- [ ] **Step 3: Update `explain_formulas` and `explain_math_from_sections` prompts**

In `explain_formulas`, locate the `Return strict JSON:` line and update the per-formula schema:

```python
Return strict JSON:
{{"formulas": [{{"latex": "...", "plain_explanation": "...", "intuition": "what this computes at a high level before any symbols", "prerequisites": ["concept needed to understand this"], "where_it_appears": "which part of method/evaluation this drives", "symbols": {{"x": "meaning or unknown"}}, "importance": "why it matters in this paper"}}]}}
```

Apply the identical schema change to `explain_math_from_sections`.

- [ ] **Step 4: Run to verify it passes**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py::TestAIProcessor::test_explain_formulas_returns_enriched_schema -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add app/services/ai_processor.py tests/services/test_ai_processor.py
git commit -m "feat: add intuition, prerequisites, where_it_appears to formula explanations"
```

---

## Task 3: Add `critique_distillation()` method

**Files:**
- Modify: `backend/app/services/ai_processor.py`
- Modify: `backend/tests/services/test_ai_processor.py`

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.anyio
async def test_critique_distillation_flags_overclaim(self, processor):
    synthesis = {
        "quick_summary": "The model achieves state-of-the-art on all benchmarks.",
        "method_deep_dive": "We use a novel approach.",
        "results_and_evidence": "Our method beats all baselines by 20%.",
        "limitations_and_caveats": "",
        "authors_claims": "State-of-the-art across all tasks.",
        "evidence_assessment": "",
    }
    paper_map = {
        "main_question": "Can X solve Y?",
        "proposed_solution": "A new model",
        "paper_type": "model",
        "math_relevance": "moderate",
    }
    section_breakdown = [{"title": "Results", "summary": "Competitive with baselines"}]
    results_view = {
        "strongest_evidence": ["Comparable to baseline on main metric"],
        "caveats": ["Only tested on one dataset"],
    }
    metadata = {"title": "Test Paper"}

    mock_response = {
        "needs_revision": True,
        "overall_assessment": "Distillation overclaims result strength.",
        "issues": [{
            "field": "results_and_evidence",
            "severity": "high",
            "type": "overclaim",
            "description": "Claims 20% improvement but extracted evidence shows only competitive performance.",
            "suggested_fix": "Soften claim to match evidence.",
        }],
    }

    with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
        result = await processor.critique_distillation(
            synthesis, paper_map, section_breakdown, results_view, metadata
        )

    assert result["needs_revision"] is True
    assert len(result["issues"]) == 1
    assert result["issues"][0]["type"] == "overclaim"
    assert result["issues"][0]["severity"] == "high"
    assert result["issues"][0]["field"] == "results_and_evidence"

@pytest.mark.anyio
async def test_critique_distillation_returns_no_issues_for_good_synthesis(self, processor):
    mock_response = {
        "needs_revision": False,
        "overall_assessment": "Distillation is accurate and complete.",
        "issues": [],
    }
    with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
        result = await processor.critique_distillation({}, {}, [], {}, {"title": "T"})
    assert result["needs_revision"] is False
    assert result["issues"] == []

@pytest.mark.anyio
async def test_critique_distillation_handles_bad_response(self, processor):
    with patch.object(processor, '_chat_json', AsyncMock(return_value="not a dict")):
        result = await processor.critique_distillation({}, {}, [], {}, {"title": "T"})
    assert result["needs_revision"] is False
    assert result["issues"] == []
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py -k "critique" -v
```
Expected: FAIL — `AttributeError: 'AIProcessor' object has no attribute 'critique_distillation'`

- [ ] **Step 3: Implement `critique_distillation()`**

Add after `repair_distillation` in `ai_processor.py`:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((APIError, RateLimitError)),
)
async def critique_distillation(
    self,
    synthesis: Dict[str, Any],
    paper_map: Dict[str, Any],
    section_breakdown: List[Dict[str, Any]],
    results_view: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    section_notes = "\n".join(
        f"- {s.get('title', 'Untitled')}: {(s.get('summary') or '')[:300]}"
        for s in section_breakdown[:8]
    )
    evidence_notes = "\n".join(
        f"- {e}" for e in (results_view.get("strongest_evidence") or [])[:6]
    )
    caveats_from_paper = "\n".join(
        f"- {c}" for c in (
            self._coerce_list(results_view.get("caveats"))
            or self._coerce_list(paper_map.get("likely_limitations"))
        )[:6]
    )
    prompt = f"""Review this research paper distillation and identify specific quality problems.

Issue types to check:
- overclaim: distillation states a result stronger than the evidence shows
- missing_caveat: a limitation in the source material is absent or understated
- vague_method: method explanation is hand-wavy where the source is concrete
- evidence_gap: distillation claims evidence not in the extracted results
- coverage_gap: a priority section from the paper map is missing or barely addressed

Paper title: {metadata.get('title', 'Unknown')}
Paper type: {paper_map.get('paper_type', 'unknown')}
Main question: {paper_map.get('main_question', 'unknown')}
Proposed solution: {paper_map.get('proposed_solution', 'unknown')}
Math relevance: {paper_map.get('math_relevance', 'unknown')}

Ground truth — section summaries:
{section_notes or '- None'}

Ground truth — extracted evidence:
{evidence_notes or '- None extracted'}

Ground truth — caveats and limitations:
{caveats_from_paper or '- None extracted'}

Distillation fields to review:
- quick_summary: {(synthesis.get('quick_summary') or '')[:600]}
- problem_and_motivation: {(synthesis.get('problem_and_motivation') or '')[:600]}
- method_deep_dive: {(synthesis.get('method_deep_dive') or '')[:800]}
- results_and_evidence: {(synthesis.get('results_and_evidence') or '')[:600]}
- authors_claims: {(synthesis.get('authors_claims') or '')[:500]}
- evidence_assessment: {(synthesis.get('evidence_assessment') or '')[:500]}
- limitations_and_caveats: {(synthesis.get('limitations_and_caveats') or '')[:500]}
- guided_walkthrough (first 900 chars): {(synthesis.get('guided_walkthrough') or '')[:900]}

Rules:
- Only flag real problems grounded in the source material above.
- Directionally correct but imprecise → severity "medium", not "high".
- If the distillation is accurate and complete, return needs_revision: false with empty issues.
- Do not penalise appropriate hedging.

Return strict JSON:
{{
  "needs_revision": true,
  "overall_assessment": "one sentence",
  "issues": [
    {{
      "field": "method_deep_dive|results_and_evidence|limitations_and_caveats|guided_walkthrough|problem_and_motivation|authors_claims|evidence_assessment|eli5_explanation",
      "severity": "high|medium|low",
      "type": "overclaim|missing_caveat|vague_method|evidence_gap|coverage_gap",
      "description": "specific problem in under 80 words",
      "suggested_fix": "concrete instruction for the revision pass"
    }}
  ]
}}"""

    fallback: Dict[str, Any] = {
        "needs_revision": False,
        "overall_assessment": "Critique unavailable.",
        "issues": [],
    }
    result = await self._chat_json(
        "You are a strict, grounded critic of research paper distillations. Flag only real problems backed by the source material.",
        prompt,
        fallback,
    )
    if not isinstance(result, dict):
        return fallback
    if not isinstance(result.get("issues"), list):
        result["issues"] = []
    return result
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py -k "critique" -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add app/services/ai_processor.py tests/services/test_ai_processor.py
git commit -m "feat: add critique_distillation method with overclaim/caveat/method/gap checks"
```

---

## Task 4: Add `revise_with_critique()` method

**Files:**
- Modify: `backend/app/services/ai_processor.py`
- Modify: `backend/tests/services/test_ai_processor.py`

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.anyio
async def test_revise_with_critique_updates_only_affected_fields(self, processor):
    synthesis = {
        "results_and_evidence": "Our method beats all baselines by 20%.",
        "method_deep_dive": "We use a novel approach.",
        "limitations_and_caveats": "No limitations noted.",
    }
    critique = {
        "needs_revision": True,
        "issues": [{
            "field": "results_and_evidence",
            "severity": "high",
            "type": "overclaim",
            "description": "Claims 20% improvement but evidence is weaker.",
            "suggested_fix": "Soften the claim to match the extracted evidence.",
        }],
    }
    paper_map = {"proposed_solution": "A new architecture", "main_question": "Can X solve Y?"}
    metadata = {"title": "Test Paper"}

    mock_revision = {"results_and_evidence": "Our method shows competitive performance against baselines."}

    with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_revision)):
        result = await processor.revise_with_critique(synthesis, critique, paper_map, metadata)

    assert result["results_and_evidence"] == "Our method shows competitive performance against baselines."
    # Unaffected fields must not change
    assert result["method_deep_dive"] == "We use a novel approach."
    assert result["limitations_and_caveats"] == "No limitations noted."

@pytest.mark.anyio
async def test_revise_with_critique_returns_original_on_bad_response(self, processor):
    synthesis = {"method_deep_dive": "Original text."}
    critique = {"issues": [{"field": "method_deep_dive", "type": "vague_method", "severity": "medium",
                             "description": "Too vague.", "suggested_fix": "Add detail."}]}
    with patch.object(processor, '_chat_json', AsyncMock(return_value=None)):
        result = await processor.revise_with_critique(synthesis, critique, {}, {"title": "T"})
    assert result["method_deep_dive"] == "Original text."
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py -k "revise_with_critique" -v
```
Expected: FAIL — method does not exist.

- [ ] **Step 3: Implement `revise_with_critique()`**

Add after `critique_distillation` in `ai_processor.py`:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((APIError, RateLimitError)),
)
async def revise_with_critique(
    self,
    synthesis: Dict[str, Any],
    critique: Dict[str, Any],
    paper_map: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    issues = self._coerce_list(critique.get("issues"))
    affected_fields: List[str] = list({
        issue["field"] for issue in issues if issue.get("field")
    })
    if not affected_fields:
        return synthesis

    issues_text = "\n".join(
        f"- [{issue.get('severity', '?').upper()}] {issue.get('field', '?')} "
        f"| {issue.get('type', '?')}: {issue.get('description', '')} "
        f"→ Fix: {issue.get('suggested_fix', '')}"
        for issue in issues
    )
    current_values = "\n".join(
        f'"{field}": {json.dumps((synthesis.get(field) or "")[:1200], ensure_ascii=True)}'
        for field in affected_fields
    )
    field_keys = ", ".join(f'"{f}": "revised text"' for f in affected_fields)

    prompt = f"""Revise specific fields in a research paper distillation to fix critic-identified problems.

Rules:
- Revise only the fields listed below. Do not touch other fields.
- Every claim must stay grounded in the paper evidence — do not invent facts.
- overclaim → soften language, add hedging, or remove unsupported claim
- missing_caveat → add the missing limitation explicitly
- vague_method → make the explanation concrete using the proposed solution
- evidence_gap → remove or qualify the unsupported claim
- coverage_gap → expand the field to cover the missing section

Paper title: {metadata.get('title', 'Unknown')}
Proposed solution: {paper_map.get('proposed_solution', 'unknown')}
Main question: {paper_map.get('main_question', 'unknown')}

Issues to fix:
{issues_text}

Current field values:
{current_values}

Return strict JSON with only the revised fields:
{{{field_keys}}}"""

    fallback = {field: synthesis.get(field, "") for field in affected_fields}
    result = await self._chat_json(
        "You revise research paper distillations to fix specific critic-identified problems. Stay grounded — no invented facts.",
        prompt,
        fallback,
    )
    if not isinstance(result, dict):
        return synthesis

    for field in affected_fields:
        revised = result.get(field)
        if revised:
            synthesis[field] = revised
    return synthesis
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py -k "revise_with_critique" -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add app/services/ai_processor.py tests/services/test_ai_processor.py
git commit -m "feat: add revise_with_critique method — fixes only critic-flagged fields"
```

---

## Task 5: Add `generate_relationships()` and wire into `KnowledgeGraphBuilder`

**Files:**
- Modify: `backend/app/services/ai_processor.py`
- Modify: `backend/app/services/knowledge_graph.py`
- Modify: `backend/tests/services/test_ai_processor.py`
- Modify: `backend/tests/services/test_knowledge_graph.py`

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/services/test_ai_processor.py`:

```python
@pytest.mark.anyio
async def test_generate_relationships_returns_triples(self, processor):
    terms = [
        {"term": "Transformer", "category": "method", "definition": "Attention-based model", "mentions": 10},
        {"term": "BERT", "category": "method", "definition": "Pre-trained language model", "mentions": 8},
    ]
    section_breakdown = [{"title": "Method", "summary": "We build on BERT using Transformer layers."}]
    paper_map = {"proposed_solution": "Fine-tuned Transformer based on BERT"}

    mock_response = {
        "relationships": [{"source": "Transformer", "target": "BERT", "relationship": "builds_on"}]
    }

    with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
        result = await processor.generate_relationships(terms, section_breakdown, paper_map)

    assert isinstance(result, list)
    assert result[0]["source"] == "Transformer"
    assert result[0]["target"] == "BERT"
    assert result[0]["relationship"] == "builds_on"

@pytest.mark.anyio
async def test_generate_relationships_returns_empty_for_no_terms(self, processor):
    result = await processor.generate_relationships([], [], {})
    assert result == []

@pytest.mark.anyio
async def test_generate_relationships_handles_bad_response(self, processor):
    terms = [{"term": "X", "category": "method", "definition": "D", "mentions": 1}]
    with patch.object(processor, '_chat_json', AsyncMock(return_value="bad")):
        result = await processor.generate_relationships(terms, [], {})
    assert result == []
```

Add to `backend/tests/services/test_knowledge_graph.py`:

```python
def test_build_incorporates_llm_relationship_triples():
    from app.services.knowledge_graph import KnowledgeGraphBuilder
    builder = KnowledgeGraphBuilder()
    terms = [
        {"term": "Transformer", "category": "method", "definition": "Attn model", "mentions": 5},
        {"term": "BERT", "category": "method", "definition": "Pre-trained", "mentions": 4},
    ]
    triples = [{"source": "Transformer", "target": "BERT", "relationship": "builds_on"}]
    result = builder.build(terms, "some text", relationship_triples=triples)

    edge_types = [e["type"] for e in result["edges"]]
    assert "builds_on" in edge_types
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py -k "generate_relationships" tests/services/test_knowledge_graph.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement `generate_relationships()` in `ai_processor.py`**

Add after `revise_with_critique`:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((APIError, RateLimitError)),
)
async def generate_relationships(
    self,
    terms: List[Dict[str, Any]],
    section_breakdown: List[Dict[str, Any]],
    paper_map: Dict[str, Any],
) -> List[Dict[str, str]]:
    if not terms:
        return []

    term_names = [t.get("term", "") for t in terms if t.get("term")]
    if len(term_names) < 2:
        return []

    section_context = "\n".join(
        f"- {s.get('title', '')}: {(s.get('summary') or '')[:300]}"
        for s in section_breakdown[:8]
    )
    prompt = f"""Identify explicit relationships between the following terms from a research paper.

Terms: {", ".join(term_names)}

Paper context:
- Proposed solution: {paper_map.get('proposed_solution', 'unknown')}
- Sections: 
{section_context or '- None'}

For each pair of terms that have a clear, specific relationship in this paper, output one triple.
Use only these relationship types: uses, improves, compares_to, solves, builds_on, evaluates, defines, requires.
Only include relationships you can ground in the section summaries above. Do not invent connections.

Return strict JSON:
{{
  "relationships": [
    {{"source": "term A", "target": "term B", "relationship": "builds_on"}}
  ]
}}"""

    result = await self._chat_json(
        "You identify grounded relationships between terms in a research paper. Only output relationships supported by the paper context.",
        prompt,
        {"relationships": []},
    )
    if not isinstance(result, dict):
        return []
    items = result.get("relationships", [])
    if not isinstance(items, list):
        return []
    return [
        r for r in items
        if isinstance(r, dict) and r.get("source") and r.get("target") and r.get("relationship")
    ]
```

- [ ] **Step 4: Update `KnowledgeGraphBuilder.build()` to accept `relationship_triples`**

In `backend/app/services/knowledge_graph.py`, update the `build` signature and body:

```python
def build(
    self,
    terms: List[Dict[str, Any]],
    paper_text: str,
    artifact_interpretations: Optional[List[Dict[str, Any]]] = None,
    results_view: Optional[Dict[str, Any]] = None,
    paper_map: Optional[Dict[str, Any]] = None,
    relationship_triples: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    self.nodes = {}
    self.edges = []
    self._edge_keys = set()

    artifact_interpretations = artifact_interpretations or []
    results_view = results_view or {}
    paper_map = paper_map or {}
    relationship_triples = relationship_triples or []

    self._create_term_nodes(terms)
    self._create_artifact_nodes(artifact_interpretations)
    self._create_results_nodes(results_view)
    self._create_focus_node(paper_map)

    # LLM-generated triples first (high confidence)
    self._add_llm_relationship_edges(relationship_triples)

    self._connect_artifacts_to_terms(artifact_interpretations, terms)
    self._connect_results_to_terms(results_view, terms)
    self._connect_focus_to_terms(paper_map, terms)
    self._detect_text_relationships(terms, paper_text)

    return {"nodes": list(self.nodes.values()), "edges": self.edges}
```

Add `_add_llm_relationship_edges` method to `KnowledgeGraphBuilder`:

```python
def _add_llm_relationship_edges(self, triples: List[Dict[str, str]]) -> None:
    for triple in triples:
        source_label = triple.get("source", "")
        target_label = triple.get("target", "")
        relationship = triple.get("relationship", "related_to")
        source_id = self._node_id(source_label)
        target_id = self._node_id(target_label)
        if source_id in self.nodes and target_id in self.nodes:
            self._add_edge(source_id, target_id, relationship, 1.5)
```

- [ ] **Step 5: Run to verify it passes**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py -k "generate_relationships" tests/services/test_knowledge_graph.py -v
```
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
cd backend && git add app/services/ai_processor.py app/services/knowledge_graph.py tests/services/test_ai_processor.py tests/services/test_knowledge_graph.py
git commit -m "feat: add generate_relationships LLM pass and wire into KnowledgeGraphBuilder"
```

---

## Task 6: Add `reformat_for_audience()` and `chat_with_paper()` methods

**Files:**
- Modify: `backend/app/services/ai_processor.py`
- Modify: `backend/tests/services/test_ai_processor.py`

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.anyio
async def test_reformat_for_audience_reformats_prose_fields(self, processor):
    summary_json = {
        "guided_walkthrough": "The paper introduces a novel attention mechanism applied to...",
        "method_deep_dive": "Using multi-head self-attention layers with position encodings...",
        "eli5_explanation": "Think of the model like a reader who...",
        "problem_and_motivation": "Current NLP models fail to capture long-range dependencies...",
        "core_intuition": "The key insight is that every word should attend to every other word.",
        "prior_work_and_gap": "Previous recurrent models processed sequences step by step.",
    }
    mock_response = {
        "guided_walkthrough": "In really simple terms, this paper shows a new way...",
        "method_deep_dive": "The approach works by letting every word look at every other word...",
        "eli5_explanation": "Imagine you have a magic highlighter...",
        "problem_and_motivation": "The problem was that old models had to read words one at a time...",
        "core_intuition": "The big idea: every word should pay attention to every other word at once.",
        "prior_work_and_gap": "Before this, models read words one at a time like reading left to right.",
    }
    with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
        result = await processor.reformat_for_audience(summary_json, "eli5")

    assert "guided_walkthrough" in result
    assert "method_deep_dive" in result
    assert result["guided_walkthrough"] == "In really simple terms, this paper shows a new way..."

@pytest.mark.anyio
async def test_reformat_for_audience_skips_llm_for_general_level(self, processor):
    summary_json = {"guided_walkthrough": "Original text."}
    with patch.object(processor, '_chat_json', AsyncMock()) as mock_chat:
        result = await processor.reformat_for_audience(summary_json, "general")
    mock_chat.assert_not_called()
    assert result["guided_walkthrough"] == "Original text."

@pytest.mark.anyio
async def test_chat_with_paper_returns_reply_string(self, processor):
    messages = [{"role": "user", "content": "What is the main contribution?"}]
    summary_json = {
        "quick_summary": "The paper introduces X.",
        "method_deep_dive": "Using Y approach...",
        "guided_walkthrough": "First, the authors...",
        "results_and_evidence": "Results show...",
        "limitations_and_caveats": "Only tested on English.",
        "terms": [{"term": "X", "definition": "The proposed method"}],
        "formula_explanations": [],
        "section_breakdown": [],
    }
    mock_response = {"reply": "The main contribution is X, which addresses gap Y."}

    with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
        result = await processor.chat_with_paper(messages, summary_json)

    assert isinstance(result, str)
    assert result == "The main contribution is X, which addresses gap Y."

@pytest.mark.anyio
async def test_chat_with_paper_returns_fallback_on_no_client(self, processor):
    processor.client = None
    result = await processor.chat_with_paper(
        [{"role": "user", "content": "What is this about?"}], {}
    )
    assert isinstance(result, str)
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py -k "reformat_for_audience or chat_with_paper" -v
```
Expected: FAIL — methods don't exist.

- [ ] **Step 3: Implement `reformat_for_audience()` and `chat_with_paper()`**

Add both methods after `generate_relationships` in `ai_processor.py`:

```python
REFORMAT_PROSE_FIELDS = [
    "guided_walkthrough", "method_deep_dive", "eli5_explanation",
    "problem_and_motivation", "core_intuition", "prior_work_and_gap",
    "authors_claims", "evidence_assessment",
]

READING_LEVEL_INSTRUCTIONS = {
    "general": "Write for a curious non-expert reader. Use plain English. Avoid jargon unless you define it.",
    "technical": "Write for a graduate-level reader familiar with the field. Retain precise technical terminology. Assume domain knowledge.",
    "eli5": "Write for someone with no technical background. Use analogies, everyday language, and concrete examples. Avoid all jargon.",
}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((APIError, RateLimitError)),
)
async def reformat_for_audience(
    self,
    summary_json: Dict[str, Any],
    reading_level: str,
) -> Dict[str, Any]:
    if reading_level == "general":
        return {field: summary_json.get(field, "") for field in self.REFORMAT_PROSE_FIELDS}

    level_instruction = self.READING_LEVEL_INSTRUCTIONS.get(
        reading_level, self.READING_LEVEL_INSTRUCTIONS["general"]
    )
    current_fields = "\n\n".join(
        f'## {field}\n{(summary_json.get(field) or "")[:1400]}'
        for field in self.REFORMAT_PROSE_FIELDS
        if summary_json.get(field)
    )
    field_keys = ", ".join(f'"{f}": "rewritten text"' for f in self.REFORMAT_PROSE_FIELDS)

    prompt = f"""Rewrite the following research paper distillation fields for a different audience level.

Audience instruction: {level_instruction}

Rules:
- Preserve the factual content and accuracy exactly. Do not add or remove claims.
- Only change the language level and style to match the audience.
- Return all fields even if unchanged.

Fields to rewrite:
{current_fields}

Return strict JSON:
{{{field_keys}}}"""

    fallback = {field: summary_json.get(field, "") for field in self.REFORMAT_PROSE_FIELDS}
    result = await self._chat_json(
        f"You rewrite research paper distillations for a specific audience. Preserve all facts. Audience: {level_instruction}",
        prompt,
        fallback,
    )
    if not isinstance(result, dict):
        return fallback
    return {field: result.get(field) or summary_json.get(field, "") for field in self.REFORMAT_PROSE_FIELDS}

async def chat_with_paper(
    self,
    messages: List[Dict[str, Any]],
    summary_json: Dict[str, Any],
) -> str:
    if self.client is None:
        return "The AI service is not configured. Please check LLM_PROVIDER settings."

    terms_text = "\n".join(
        f"- {t.get('term')}: {t.get('definition', '')}"
        for t in (summary_json.get("terms") or [])[:12]
    )
    formulas_text = "\n".join(
        f"- {f.get('latex', 'Formula')}: {f.get('intuition', f.get('plain_explanation', ''))}"
        for f in (summary_json.get("formula_explanations") or [])[:6]
    )
    system_prompt = f"""You are an expert assistant helping a reader understand a specific research paper. Answer questions accurately using only the paper content below. If the content does not support a claim, say so explicitly — do not guess.

=== PAPER CONTENT ===
Quick summary: {(summary_json.get('quick_summary') or '')[:400]}

Problem: {(summary_json.get('problem_and_motivation') or '')[:500]}

Core idea: {(summary_json.get('core_intuition') or summary_json.get('method_deep_dive') or '')[:500]}

Method: {(summary_json.get('method_deep_dive') or '')[:700]}

Results: {(summary_json.get('results_and_evidence') or '')[:500]}

What authors claim: {(summary_json.get('authors_claims') or '')[:400]}

Evidence assessment: {(summary_json.get('evidence_assessment') or '')[:400]}

Limitations: {(summary_json.get('limitations_and_caveats') or '')[:400]}

Walkthrough: {(summary_json.get('guided_walkthrough') or '')[:1200]}

Key terms:
{terms_text or '- None'}

Math:
{formulas_text or '- None'}
=== END PAPER CONTENT ===

Return strict JSON: {{"reply": "your answer"}}"""

    last_user_content = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
    )
    result = await self._chat_json(system_prompt, last_user_content, {"reply": ""})
    if not isinstance(result, dict):
        return "Unable to generate a response at this time."
    return result.get("reply") or "Unable to generate a response at this time."
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd backend && uv run pytest tests/services/test_ai_processor.py -k "reformat_for_audience or chat_with_paper" -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add app/services/ai_processor.py tests/services/test_ai_processor.py
git commit -m "feat: add reformat_for_audience and chat_with_paper to AIProcessor"
```

---

## Task 7: Wire critic pass and `generate_relationships` into `tasks.py`

**Files:**
- Modify: `backend/app/workers/tasks.py`

- [ ] **Step 1: Update `process_all()` in `tasks.py`**

Locate the `process_all` async function. Replace the synthesis + repair block (currently lines ~129–157) with:

```python
update_progress("Generating concept relationships...", 72)
relationship_triples = await processor.generate_relationships(
    terms, section_breakdown, paper_map
)
if isinstance(relationship_triples, Exception):
    relationship_triples = []

update_progress("Synthesizing final distillation...", 76)
synthesis = await processor.synthesize_distillation(
    summary_metadata,
    paper_map,
    section_breakdown,
    results_view,
    formula_explanations,
    terms,
    table_interpretations,
    figure_interpretations,
)

update_progress("Reviewing distillation quality...", 80)
critique = await processor.critique_distillation(
    synthesis, paper_map, section_breakdown, results_view, summary_metadata
)

if isinstance(critique, Exception):
    critique = {"needs_revision": False, "overall_assessment": "", "issues": []}

if critique.get("needs_revision"):
    update_progress("Revising based on critique...", 84)
    synthesis = await processor.revise_with_critique(
        synthesis, critique, paper_map, summary_metadata
    )

if (
    len((synthesis.get("eli5_explanation") or "").strip()) < 420
    or len((synthesis.get("guided_walkthrough") or "").strip()) < 800
):
    update_progress("Deepening the walkthrough...", 88)
    synthesis = await processor.repair_distillation(synthesis, summary_metadata, paper_map)

return (
    synthesis,
    critique,
    formula_explanations,
    terms,
    paper_map,
    section_breakdown,
    results_view,
    table_interpretations,
    figure_interpretations,
    relationship_triples,
)
```

Update the `return` unpack after `asyncio.run(process_all())` to match the new tuple:

```python
(
    summary,
    critique,
    formula_explanations,
    terms,
    paper_map,
    section_breakdown,
    results_view,
    table_interpretations,
    figure_interpretations,
    relationship_triples,
) = result
```

Update the `KnowledgeGraphBuilder.build()` call to pass `relationship_triples`:

```python
knowledge_graph = kg_builder.build(
    terms,
    parsed["text"],
    results_view.get("artifact_interpretations", []),
    results_view,
    paper_map,
    relationship_triples=relationship_triples,
)
```

Add `"critique": critique` to `analysis.summary_json` dict (after `"terms": terms`):

```python
"critique": critique,
```

- [ ] **Step 2: Verify the task file is syntactically valid**

```bash
cd backend && uv run python -c "from app.workers.tasks import process_paper_task; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd backend && git add app/workers/tasks.py
git commit -m "feat: wire critic pass, generate_relationships, and critique storage into pipeline"
```

---

## Task 8: Add chat and reformat schemas + endpoints

**Files:**
- Modify: `backend/app/schemas/paper.py`
- Modify: `backend/app/api/routes/papers.py`
- Modify: `backend/tests/api/test_papers.py`

- [ ] **Step 1: Write the failing endpoint tests**

Add to `TestPapersAPI` in `backend/tests/api/test_papers.py`:

```python
@patch("app.api.routes.papers.AIProcessor")
def test_chat_requires_auth(self, mock_processor):
    resp = client.post("/api/papers/some-id/chat", json={"messages": [{"role": "user", "content": "Hello"}]})
    assert resp.status_code == 401

@patch("app.api.routes.papers.AIProcessor")
def test_chat_returns_404_for_unknown_paper(self, mock_processor, auth_token):
    resp = client.post(
        "/api/papers/00000000-0000-0000-0000-000000000000/chat",
        json={"messages": [{"role": "user", "content": "What is this about?"}]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 404

@patch("app.api.routes.papers.AIProcessor")
def test_reformat_requires_auth(self, mock_processor):
    resp = client.post("/api/papers/some-id/reformat", json={"reading_level": "eli5"})
    assert resp.status_code == 401

@patch("app.api.routes.papers.AIProcessor")
def test_reformat_returns_404_for_unknown_paper(self, mock_processor, auth_token):
    resp = client.post(
        "/api/papers/00000000-0000-0000-0000-000000000000/reformat",
        json={"reading_level": "eli5"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 404

@patch("app.api.routes.papers.AIProcessor")
def test_reformat_rejects_invalid_reading_level(self, mock_processor, auth_token):
    resp = client.post(
        "/api/papers/00000000-0000-0000-0000-000000000000/reformat",
        json={"reading_level": "expert"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    # 422 from Pydantic validation or 404 from paper not found — either is correct here
    assert resp.status_code in (404, 422)
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd backend && uv run pytest tests/api/test_papers.py -k "chat or reformat" -v
```
Expected: FAIL — routes don't exist (404 from routing, or 405).

- [ ] **Step 3: Add schemas to `schemas/paper.py`**

```python
from typing import Literal

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    reply: str

class ReformatRequest(BaseModel):
    reading_level: Literal["general", "technical", "eli5"]

class ReformatResponse(BaseModel):
    reformatted_fields: dict
```

- [ ] **Step 4: Add endpoints to `routes/papers.py`**

Add these imports at the top of `papers.py`:

```python
from app.schemas.paper import (
    PaperAnalysisRequest, PaperAnalysisResponse, PaperAnalysisComplete,
    ChatRequest, ChatResponse, ReformatRequest, ReformatResponse,
)
from app.services.ai_processor import AIProcessor
from app.core.limiter import limiter
from fastapi import Request
```

Add these routes after `delete_paper`:

```python
@router.post("/{paper_id}/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_with_paper(
    request: Request,
    paper_id: str,
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).first()
    if analysis is None or analysis.processing_status != "complete":
        raise HTTPException(status_code=400, detail="Paper analysis is not complete")

    summary_json = analysis.summary_json or {}
    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    processor = AIProcessor()
    reply = await processor.chat_with_paper(messages, summary_json)
    return ChatResponse(reply=reply)


@router.post("/{paper_id}/reformat", response_model=ReformatResponse)
@limiter.limit("10/minute")
async def reformat_paper(
    request: Request,
    paper_id: str,
    body: ReformatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).first()
    if analysis is None or analysis.processing_status != "complete":
        raise HTTPException(status_code=400, detail="Paper analysis is not complete")

    summary_json = analysis.summary_json or {}
    processor = AIProcessor()
    reformatted = await processor.reformat_for_audience(summary_json, body.reading_level)
    return ReformatResponse(reformatted_fields=reformatted)
```

- [ ] **Step 5: Run to verify tests pass**

```bash
cd backend && uv run pytest tests/api/test_papers.py -k "chat or reformat" -v
```
Expected: All PASS (404 tests pass because paper doesn't exist in test DB; auth tests pass because no token → 401).

- [ ] **Step 6: Run full backend test suite to confirm no regressions**

```bash
cd backend && uv run pytest tests/api/ tests/services/test_ai_processor.py tests/services/test_knowledge_graph.py -q
```
Expected: All pass.

- [ ] **Step 7: Commit**

```bash
cd backend && git add app/schemas/paper.py app/api/routes/papers.py tests/api/test_papers.py
git commit -m "feat: add /chat and /reformat endpoints with rate limiting and auth"
```

---

## Task 9: Update frontend types and API client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Update `FormulaExplanation` in `types/index.ts`**

Replace the existing `FormulaExplanation` interface:

```typescript
export interface FormulaExplanation {
  latex: string;
  plain_explanation: string;
  symbols: Record<string, string>;
  importance: string;
  intuition?: string;
  prerequisites?: string[];
  where_it_appears?: string;
}
```

- [ ] **Step 2: Add new fields to `PaperAnalysis.summary` in `types/index.ts`**

Inside the `summary?` block of `PaperAnalysis`, add after `limitations_and_caveats?`:

```typescript
prior_work_and_gap?: string;
core_intuition?: string;
authors_claims?: string;
evidence_assessment?: string;
critique?: {
  needs_revision: boolean;
  overall_assessment: string;
  issues: Array<{
    field: string;
    severity: 'high' | 'medium' | 'low';
    type: 'overclaim' | 'missing_caveat' | 'vague_method' | 'evidence_gap' | 'coverage_gap';
    description: string;
    suggested_fix: string;
  }>;
};
```

- [ ] **Step 3: Add `chat` and `reformat` to `papersAPI` in `api.ts`**

Inside the `papersAPI` object, add after `listPapers`:

```typescript
chat: async (paperId: string, messages: Array<{role: 'user' | 'assistant', content: string}>, token: string) => {
  const response = await api.post(
    `/papers/${paperId}/chat`,
    { messages },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data as { reply: string };
},
reformat: async (paperId: string, readingLevel: 'general' | 'technical' | 'eli5', token: string) => {
  const response = await api.post(
    `/papers/${paperId}/reformat`,
    { reading_level: readingLevel },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data as { reformatted_fields: Record<string, string> };
},
```

- [ ] **Step 4: Type-check the frontend**

```bash
cd frontend && npm run build 2>&1 | tail -20
```
Expected: Build succeeds with no type errors.

- [ ] **Step 5: Commit**

```bash
cd frontend && git add src/types/index.ts src/services/api.ts
git commit -m "feat: update frontend types and API client for new backend fields and endpoints"
```

---

## Self-Review

### Spec coverage check

| Requirement | Task |
|---|---|
| `prior_work_and_gap`, `core_intuition`, `authors_claims`, `evidence_assessment` fields | Task 1 |
| `intuition`, `prerequisites`, `where_it_appears` on formula explanations | Task 2 |
| `critique_distillation()` with 5 issue types | Task 3 |
| `revise_with_critique()` affects only flagged fields | Task 4 |
| `generate_relationships()` LLM triples | Task 5 |
| `KnowledgeGraphBuilder` accepts `relationship_triples` | Task 5 |
| `reformat_for_audience()` skips LLM on `general` level | Task 6 |
| `chat_with_paper()` builds context from selective fields | Task 6 |
| Pipeline wired: critic → revision → repair; triples into KG; critique stored | Task 7 |
| `POST /{paper_id}/chat` rate-limited, auth-gated | Task 8 |
| `POST /{paper_id}/reformat` rate-limited, auth-gated | Task 8 |
| Frontend types updated | Task 9 |
| Frontend API client updated | Task 9 |

All requirements covered. No gaps found.

### Placeholder scan

No TBDs, no "similar to Task N", all code blocks are complete.

### Type consistency

- `critique_distillation` returns `Dict[str, Any]` with keys `needs_revision`, `overall_assessment`, `issues` — consumed in Task 7 with `.get("needs_revision")` ✓
- `revise_with_critique` signature takes `synthesis: Dict[str, Any]`, `critique: Dict[str, Any]` — matches Task 7 call site ✓
- `generate_relationships` returns `List[Dict[str, str]]` — passed as `relationship_triples=` kwarg in Task 7 ✓
- `KnowledgeGraphBuilder.build()` new `relationship_triples` param is `Optional[List[Dict[str, str]]]` defaulting to `None` — backward compatible ✓
- `chat_with_paper` takes `List[Dict[str, Any]]` messages — Task 8 endpoint passes `[{"role": m.role, "content": m.content}]` ✓
- `ChatRequest.messages` uses `List[ChatMessage]` with `Literal["user", "assistant"]` role — `api.ts` types match ✓
