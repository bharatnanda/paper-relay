import asyncio
from openai import AsyncOpenAI, APIError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, Any, List, Optional
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProcessor:
    SECTION_CHAR_BUDGET = 4500
    MAX_SECTION_PASSES = 7
    SECTION_ROLE_KEYWORDS = {
        "overview": ("abstract", "introduction", "background", "related work", "preliminaries", "problem setup"),
        "method": ("method", "methods", "approach", "model", "architecture", "training"),
        "evaluation": ("experimental setup", "experiments", "evaluation", "benchmark"),
        "results": ("results", "analysis"),
        "limitations": ("limitations", "discussion", "conclusion", "conclusions"),
        "ablation": ("ablation", "appendix"),
    }

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower().strip()
        self.client, self.model, self.misconfiguration_reason = self._build_client()
        self.max_tokens = settings.OPENAI_MAX_TOKENS

    def _build_client(self):
        if self.provider == "azure":
            if not settings.AZURE_OPENAI_API_KEY:
                return None, settings.AZURE_OPENAI_MODEL or settings.OPENAI_MODEL, "Azure OpenAI API key not configured."
            if not settings.AZURE_OPENAI_BASE_URL:
                return None, settings.AZURE_OPENAI_MODEL or settings.OPENAI_MODEL, "Azure OpenAI base URL not configured."
            if not settings.AZURE_OPENAI_MODEL:
                return None, settings.OPENAI_MODEL, "Azure OpenAI deployment/model name not configured."
            return (
                AsyncOpenAI(
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    base_url=settings.AZURE_OPENAI_BASE_URL,
                ),
                settings.AZURE_OPENAI_MODEL,
                None,
            )

        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                return None, settings.OPENAI_MODEL, "OpenAI API key not configured."
            return AsyncOpenAI(api_key=settings.OPENAI_API_KEY), settings.OPENAI_MODEL, None

        return None, settings.OPENAI_MODEL, f"Unsupported LLM provider: {settings.LLM_PROVIDER}"

    async def _chat_json(self, system_prompt: str, user_prompt: str, fallback: Any) -> Any:
        if self.client is None:
            return fallback

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON response from model: %s", exc)
            return fallback

    def _select_sections(self, metadata: Dict[str, Any], paper_text: str) -> List[Dict[str, Any]]:
        sections = metadata.get("sections", []) or []
        cleaned_sections = []
        seen_titles = set()

        for index, section in enumerate(sections):
            title = (section.get("title") or "").strip() or "Untitled section"
            content = (section.get("content") or "").strip()
            if not content:
                continue
            normalized_title = " ".join(title.lower().split())
            if normalized_title in seen_titles:
                continue
            seen_titles.add(normalized_title)
            cleaned_sections.append(
                {
                    "title": title,
                    "content": content[: self.SECTION_CHAR_BUDGET * 2],
                    "index": index,
                    "role": self._infer_section_role(title),
                }
            )

        if cleaned_sections:
            return cleaned_sections[:18]

        normalized_text = " ".join(paper_text.split())
        chunks = []
        for index in range(0, len(normalized_text), self.SECTION_CHAR_BUDGET):
            chunk = normalized_text[index:index + self.SECTION_CHAR_BUDGET].strip()
            if chunk:
                chunks.append({"title": f"Chunk {len(chunks) + 1}", "content": chunk, "index": len(chunks), "role": "other"})
            if len(chunks) >= 10:
                break
        return chunks

    def _infer_section_role(self, title: str) -> str:
        normalized_title = " ".join(title.lower().split())
        for role, keywords in self.SECTION_ROLE_KEYWORDS.items():
            if any(keyword in normalized_title for keyword in keywords):
                return role
        return "other"

    def _select_sections_for_coverage(
        self,
        sections: List[Dict[str, Any]],
        paper_map: Optional[Dict[str, Any]] = None,
        max_sections: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if not sections:
            return []

        limit = max_sections or self.MAX_SECTION_PASSES
        priority_titles = {
            " ".join(title.lower().split())
            for title in self._coerce_list((paper_map or {}).get("priority_sections"), limit=limit)
        }
        required_roles = ["overview", "method", "evaluation", "results", "limitations"]
        chosen: List[Dict[str, Any]] = []
        chosen_titles = set()

        def section_key(section: Dict[str, Any]) -> str:
            return " ".join(section.get("title", "").lower().split())

        def add(section: Dict[str, Any]) -> None:
            key = section_key(section)
            if key in chosen_titles:
                return
            chosen.append(section)
            chosen_titles.add(key)

        for section in sections:
            if section_key(section) in priority_titles:
                add(section)
                if len(chosen) >= limit:
                    return sorted(chosen, key=lambda item: item.get("index", 0))

        for role in required_roles:
            candidate = next(
                (section for section in sections if section.get("role") == role and section_key(section) not in chosen_titles),
                None,
            )
            if candidate:
                add(candidate)
                if len(chosen) >= limit:
                    return sorted(chosen, key=lambda item: item.get("index", 0))

        remaining = sorted(
            [section for section in sections if section_key(section) not in chosen_titles],
            key=lambda section: (
                0 if section_key(section) in priority_titles else 1,
                0 if section.get("role") == "ablation" else 1,
                len(section.get("content", "")) * -1,
                section.get("index", 0),
            ),
        )
        for section in remaining:
            add(section)
            if len(chosen) >= limit:
                break

        return sorted(chosen, key=lambda item: item.get("index", 0))

    def _format_sections_for_prompt(self, sections: List[Dict[str, Any]], char_budget: int) -> str:
        blocks = []
        for section in sections[: self.MAX_SECTION_PASSES]:
            title = section.get("title", "Untitled section")
            content = (section.get("content") or "").strip()
            if not content:
                continue
            blocks.append(f"## {title}\n{content[:char_budget]}")
        return "\n\n".join(blocks)

    def _coerce_list(self, value: Any, limit: Optional[int] = None) -> List[Any]:
        if not isinstance(value, list):
            return []
        result = [item for item in value if item]
        return result[:limit] if limit is not None else result

    def _normalize_artifact_interpretations(self, value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            return []
        items = []
        for item in value:
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            what_it_shows = item.get("what_it_shows")
            if not label and not what_it_shows:
                continue
            items.append(item)
        return items

    def _format_figure_artifacts(self, figures: List[Dict[str, Any]], limit: int = 8) -> str:
        blocks = []
        for figure in figures[:limit]:
            caption = figure.get("caption")
            if not caption:
                continue
            blocks.append(
                "\n".join(
                    [
                        f"- Label: {figure.get('label', 'Figure')}",
                        f"  Section: {figure.get('section_title', 'Unknown')}",
                        f"  Page: {figure.get('page', 'Unknown')}",
                        f"  Caption: {caption}",
                        f"  Context before: {figure.get('context_before', 'None')}",
                        f"  Context after: {figure.get('context_after', 'None')}",
                    ]
                )
            )
        return "\n\n".join(blocks)

    def _format_table_artifacts(self, tables: List[Dict[str, Any]], limit: int = 6) -> str:
        blocks = []
        for table in tables[:limit]:
            rows = table.get("rows", [])[:4]
            rendered_rows = []
            for row in rows:
                rendered_rows.append(" | ".join(cell for cell in row if cell))
            blocks.append(
                "\n".join(
                    [
                        f"- Title: {table.get('title', 'Table')}",
                        f"  Section: {table.get('section_title', 'Unknown')}",
                        f"  Page: {table.get('page', 'Unknown')}",
                        f"  Header: {' | '.join(table.get('header', []) or []) or 'Unknown'}",
                        f"  Row count: {table.get('row_count', 0)}",
                        f"  Column count: {table.get('column_count', 0)}",
                        f"  Rows preview: {' || '.join(rendered_rows) or 'None'}",
                        f"  Context before: {table.get('context_before', 'None')}",
                        f"  Context after: {table.get('context_after', 'None')}",
                    ]
                )
            )
        return "\n\n".join(blocks)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def interpret_figures(
        self,
        metadata: Dict[str, Any],
        paper_map: Dict[str, Any],
        section_breakdown: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        figures_text = self._format_figure_artifacts(metadata.get("figure_captions", []), limit=10)
        if not figures_text:
            return []

        section_notes = "\n".join(
            f"- {section.get('title', 'Untitled section')}: {section.get('summary', '')}"
            for section in section_breakdown[:6]
        )
        prompt = f"""Interpret the extracted figures from this paper.

Rules:
- Explain what each figure appears to show using the caption and nearby context.
- Tie the figure back to the paper's method, evaluation, or conclusions.
- If the figure extraction is incomplete, say so explicitly and lower confidence.
- Do not guess image content beyond what the text supports.

Paper title: {metadata.get('title', 'Unknown')}
Main question: {paper_map.get('main_question', 'Unknown')}

Section context:
{section_notes or '- None'}

Figures:
{figures_text}

Return strict JSON:
{{
  "figures": [
    {{
      "artifact_type": "figure",
      "label": "Figure 1",
      "section_title": "where it appears",
      "what_it_shows": "grounded explanation",
      "why_it_matters": "why this matters to the paper",
      "confidence": "high|medium|low"
    }}
  ]
}}"""

        result = await self._chat_json(
            "You interpret research paper figures using only captions and nearby text.",
            prompt,
            {"figures": []},
        )
        return self._normalize_artifact_interpretations(result.get("figures", []) if isinstance(result, dict) else [])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def interpret_tables(
        self,
        metadata: Dict[str, Any],
        paper_map: Dict[str, Any],
        section_breakdown: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        tables_text = self._format_table_artifacts(metadata.get("tables", []), limit=8)
        if not tables_text:
            return []

        section_notes = "\n".join(
            f"- {section.get('title', 'Untitled section')}: {section.get('summary', '')}"
            for section in section_breakdown[:6]
        )
        prompt = f"""Interpret the extracted tables from this paper.

Rules:
- Explain what each table compares or measures.
- Mention the likely metrics, baselines, or evaluated settings when the table text supports them.
- Say when headers or rows are incomplete or noisy.
- Do not overstate the result if the extraction is partial.

Paper title: {metadata.get('title', 'Unknown')}
Results focus hint: {paper_map.get('results_focus', 'Unknown')}

Section context:
{section_notes or '- None'}

Tables:
{tables_text}

Return strict JSON:
{{
  "tables": [
    {{
      "artifact_type": "table",
      "label": "Table 1",
      "section_title": "where it appears",
      "what_it_shows": "grounded explanation",
      "why_it_matters": "why this matters to the paper",
      "confidence": "high|medium|low"
    }}
  ]
}}"""

        result = await self._chat_json(
            "You interpret research paper tables using headers, rows, and nearby context.",
            prompt,
            {"tables": []},
        )
        return self._normalize_artifact_interpretations(result.get("tables", []) if isinstance(result, dict) else [])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def map_paper(self, paper_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        sections = self._select_sections(metadata, paper_text)
        section_titles = ", ".join(section["title"] for section in sections) or "Not detected"
        excerpt = self._format_sections_for_prompt(sections[:4], 2200)
        prompt = f"""Build a control map for this research paper so later passes can explain it well to a non-expert reader.

Rules:
- Stay grounded in the paper text and metadata only.
- Focus on what the paper is trying to do, how it appears to do it, and where evidence likely appears.
- If something is unclear, say so instead of guessing.

Paper metadata:
- Title: {metadata.get('title', 'Unknown')}
- Authors: {", ".join(metadata.get('authors', []))}
- Abstract: {metadata.get('abstract', 'Not available')}
- Detected sections: {section_titles}

Paper excerpts:
{excerpt or paper_text[:7000]}

Return strict JSON:
{{
  "main_question": "what problem the paper is solving",
  "paper_type": "system|model|benchmark|theory|survey|other",
  "proposed_solution": "core idea in plain English",
  "reader_orientation": "how a naive but serious reader should approach the paper",
  "priority_sections": ["section titles to focus on"],
  "math_relevance": "none|light|moderate|heavy",
  "results_focus": "what evidence or experiments matter most",
  "likely_limitations": ["possible caveat grounded in the text or say unclear"]
}}"""

        fallback = {
            "main_question": metadata.get("abstract", "Main question unavailable"),
            "paper_type": "other",
            "proposed_solution": metadata.get("abstract", "Proposed solution unavailable"),
            "reader_orientation": "Read the abstract, method, and evaluation closely.",
            "priority_sections": [section["title"] for section in sections[:4]],
            "math_relevance": "unclear",
            "results_focus": "Results focus unavailable",
            "likely_limitations": [],
        }
        result = await self._chat_json(
            "You build concise paper maps for a multi-pass distillation pipeline.",
            prompt,
            fallback,
        )
        if isinstance(result, dict):
            return result
        return fallback

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def distill_section(self, section: Dict[str, Any], paper_map: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""Distill this section of a research paper for a reader who wants to understand the whole paper without reading every line.

Rules:
- Explain what this section contributes to the paper.
- Keep the explanation accessible, but do not omit concrete details.
- Separate claims from evidence.
- Mention math, experiments, or limitations if this section contains them.

Paper title: {metadata.get('title', 'Unknown')}
Main question: {paper_map.get('main_question', 'Unknown')}
Proposed solution: {paper_map.get('proposed_solution', 'Unknown')}
Section title: {section.get('title', 'Untitled section')}

Section text:
{(section.get('content') or '')[:self.SECTION_CHAR_BUDGET]}

Return strict JSON:
{{
  "title": "{section.get('title', 'Untitled section')}",
  "summary": "one substantial paragraph",
  "why_it_matters": "why this section matters in the full paper",
  "key_points": ["important point"],
  "evidence": ["evidence or result from this section"],
  "math_focus": "what mathematical idea appears here, or say not central",
  "reader_confusions": ["what might confuse a new reader"]
}}"""

        fallback = {
            "title": section.get("title", "Untitled section"),
            "summary": (section.get("content") or "")[:600],
            "why_it_matters": "This section contributes to the paper's narrative.",
            "key_points": [],
            "evidence": [],
            "math_focus": "not central",
            "reader_confusions": [],
        }
        result = await self._chat_json(
            "You write section-by-section research paper distillations for non-expert readers.",
            prompt,
            fallback,
        )
        if isinstance(result, dict):
            return result
        return fallback

    async def distill_sections(self, paper_text: str, metadata: Dict[str, Any], paper_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        sections = self._select_sections(metadata, paper_text)
        ranked_sections = self._select_sections_for_coverage(sections, paper_map, self.MAX_SECTION_PASSES)

        distilled = []
        for section in ranked_sections:
            distilled.append(await self.distill_section(section, paper_map, metadata))
        return distilled

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def extract_results_view(
        self,
        metadata: Dict[str, Any],
        section_breakdown: List[Dict[str, Any]],
        paper_map: Dict[str, Any],
        table_interpretations: Optional[List[Dict[str, Any]]] = None,
        figure_interpretations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        figure_captions = self._format_figure_artifacts(metadata.get("figure_captions", []), limit=10)
        table_descriptions = self._format_table_artifacts(metadata.get("tables", []), limit=8)
        artifact_notes = "\n".join(
            f"- [{item.get('artifact_type', 'artifact')}] {item.get('label', 'Unknown')}: {item.get('what_it_shows', '')} Why it matters: {item.get('why_it_matters', '')} Confidence: {item.get('confidence', 'unknown')}"
            for item in [*(table_interpretations or []), *(figure_interpretations or [])]
        )
        section_notes = "\n\n".join(
            (
                f"## {section.get('title', 'Untitled section')}\n"
                f"Summary: {section.get('summary', '')}\n"
                f"Evidence: {'; '.join(section.get('evidence', []))}\n"
                f"Key points: {'; '.join(section.get('key_points', []))}\n"
                f"Why it matters: {section.get('why_it_matters', '')}"
            )
            for section in section_breakdown
        )
        prompt = f"""Build a results-and-evidence view of this paper.

Rules:
- Focus on what evidence the paper presents, how the method is evaluated, and what conclusions a careful reader should draw.
- Be explicit when metrics or baselines are unclear.
- Do not inflate weak evidence into strong claims.
- Use figure and table context to explain what each artifact seems to show, not just its title.
- Mention when the extracted artifact is incomplete or noisy.
- When interpreted artifacts are available, prefer them over generic section summaries.

Paper title: {metadata.get('title', 'Unknown')}
Results focus hint: {paper_map.get('results_focus', 'Unknown')}

Section evidence:
{section_notes[:9000]}

Figure captions:
{figure_captions or '- None extracted'}

Table excerpts:
{table_descriptions or '- None extracted'}

Artifact interpretations:
{artifact_notes or '- None interpreted'}

Return strict JSON:
{{
  "evaluation_setup": "what seems to have been evaluated",
  "results_summary": "substantial paragraph on the evidence",
  "strongest_evidence": ["grounded result"],
  "caveats": ["limits of the evidence"],
  "artifact_interpretations": [
    {{
      "artifact_type": "table|figure",
      "label": "Table 1 or Figure 2",
      "section_title": "where it appears",
      "what_it_shows": "grounded explanation",
      "why_it_matters": "why this artifact matters",
      "confidence": "high|medium|low"
    }}
  ]
}}"""

        fallback = {
            "evaluation_setup": "Evaluation setup unavailable",
            "results_summary": "Results summary unavailable",
            "strongest_evidence": [],
            "caveats": self._coerce_list(paper_map.get("likely_limitations")),
            "artifact_interpretations": [*(table_interpretations or []), *(figure_interpretations or [])],
        }
        result = await self._chat_json(
            "You extract grounded evidence summaries from research papers.",
            prompt,
            fallback,
        )
        if isinstance(result, dict):
            result["artifact_interpretations"] = self._normalize_artifact_interpretations(
                result.get("artifact_interpretations", fallback["artifact_interpretations"])
            ) or fallback["artifact_interpretations"]
            return result
        return fallback

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def explain_formulas(self, formulas: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        if not formulas:
            return []

        if self.client is None:
            return []

        formula_context = "\n\n".join(
            [
                f"Formula {i + 1}: {formula.get('latex', '')}\nContext: {(formula.get('context') or '')[:520]}"
                for i, formula in enumerate(formulas[:10])
            ]
        )
        prompt = f"""Explain the following research-paper formulas or equation-like snippets in plain English.

Rules:
- Stay close to the formula and nearby context.
- If symbols are ambiguous, say "not clearly defined in excerpt" instead of guessing.
- Focus on what the expression is doing in this paper.
- If a snippet is noisy because of PDF extraction, explain cautiously and state the uncertainty.

{formula_context}

Return strict JSON:
{{"formulas": [{{"latex": "...", "plain_explanation": "...", "intuition": "what this computes at a high level before any symbols", "prerequisites": ["concept needed to understand this"], "where_it_appears": "which part of method/evaluation this drives", "symbols": {{"x": "meaning or unknown"}}, "importance": "why it matters in this paper"}}]}}"""

        result = await self._chat_json(
            "You are a technical explainer for research math. Be precise and avoid guessing.",
            prompt,
            {"formulas": []},
        )
        items = result.get("formulas", []) if isinstance(result, dict) else []
        return items if isinstance(items, list) else []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def explain_math_from_sections(
        self,
        paper_text: str,
        metadata: Dict[str, Any],
        paper_map: Dict[str, Any],
        section_breakdown: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        sections = self._select_sections(metadata, paper_text)
        math_sections = [
            section
            for section in sections
            if any(keyword in section.get("title", "").lower() for keyword in ("method", "approach", "model", "training", "analysis", "results"))
        ]
        source = self._format_sections_for_prompt(math_sections or sections[:3], 2600)
        section_notes = "\n".join(
            f"- {section.get('title', 'Untitled section')}: {section.get('math_focus', 'not central')}"
            for section in section_breakdown
        )
        prompt = f"""Identify the most important mathematical or scoring ideas in this paper and explain them for a non-expert reader.

Rules:
- Only include equations, objectives, scoring rules, update rules, or decision functions that appear to matter to the paper.
- If the exact equation text is not recoverable from the PDF extraction, provide a short descriptive label instead of inventing notation.
- Keep each explanation concrete and tied to the paper's method or evaluation.

Paper title: {metadata.get('title', 'Unknown')}
Math relevance: {paper_map.get('math_relevance', 'Unknown')}
Section hints:
{section_notes or '- None'}

Source excerpts:
{source[:9000]}

Return strict JSON:
{{"formulas": [{{"latex": "...", "plain_explanation": "...", "intuition": "what this computes at a high level before any symbols", "prerequisites": ["concept needed to understand this"], "where_it_appears": "which part of method/evaluation this drives", "symbols": {{"x": "meaning or unknown"}}, "importance": "why it matters in this paper"}}]}}"""

        result = await self._chat_json(
            "You recover and explain the most important mathematical ideas from research papers.",
            prompt,
            {"formulas": []},
        )
        items = result.get("formulas", []) if isinstance(result, dict) else []
        return items if isinstance(items, list) else []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def extract_terms(self, paper_text: str) -> List[Dict[str, str]]:
        if self.client is None:
            return []

        prompt = f"""Extract the most important paper-specific terms from the text below.

Rules:
- Prefer methods, datasets, benchmarks, models, metrics, and core concepts.
- Avoid generic research words like "paper", "method", "result", "performance", unless they are part of a specific named term.
- Keep the list short and high-signal: at most 16 terms.
- Definitions must be grounded in how the term is used in this paper.
- Mentions should be a rough estimate, not an invented exact count.

Text:
{paper_text[:14000]}

Return strict JSON:
{{"terms": [{{"term": "name", "category": "method|dataset|metric|concept", "definition": "paper-grounded definition", "mentions": 5}}]}}"""

        result = await self._chat_json(
            "You extract high-signal research terms from papers. Be selective and avoid generic terms.",
            prompt,
            {"terms": []},
        )
        items = result.get("terms", []) if isinstance(result, dict) else []
        return items if isinstance(items, list) else []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def synthesize_distillation(
        self,
        metadata: Dict[str, Any],
        paper_map: Dict[str, Any],
        section_breakdown: List[Dict[str, Any]],
        results_view: Dict[str, Any],
        formula_explanations: List[Dict[str, Any]],
        terms: List[Dict[str, Any]],
        table_interpretations: Optional[List[Dict[str, Any]]] = None,
        figure_interpretations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        section_notes = "\n\n".join(
            (
                f"## {section.get('title', 'Untitled section')}\n"
                f"Summary: {section.get('summary', '')}\n"
                f"Why it matters: {section.get('why_it_matters', '')}\n"
                f"Key points: {'; '.join(self._coerce_list(section.get('key_points')))}\n"
                f"Evidence: {'; '.join(self._coerce_list(section.get('evidence')))}"
            )
            for section in section_breakdown
        )
        formulas_text = "\n".join(
            f"- {formula.get('latex', 'Math idea')}: {formula.get('plain_explanation', '')}"
            for formula in formula_explanations[:6]
        )
        key_terms = "\n".join(
            f"- {term.get('term', '')}: {term.get('definition', '')}"
            for term in terms[:10]
        )
        artifact_notes = "\n".join(
            f"- [{item.get('artifact_type', 'artifact')}] {item.get('label', 'Unknown')} ({item.get('section_title', 'Unknown')}): {item.get('what_it_shows', '')} Why it matters: {item.get('why_it_matters', '')}"
            for item in [*(table_interpretations or []), *(figure_interpretations or []), *self._normalize_artifact_interpretations(results_view.get('artifact_interpretations'))]
        )
        prompt = f"""Synthesize a final paper distillation from prior structured passes.

Audience:
- A naive but serious reader who wants to understand the whole paper in concise form.

Rules:
- Be detailed enough that the reader can follow the paper's full arc without reading every section.
- Keep the writing plain-English, but retain the actual technical content.
- Include method, evidence, and limitations.
- The ELI5 walkthrough should be progressive and substantial, not a single short paragraph.
- The quick summary should still be short.
- Prefer normalized artifact interpretations when explaining results, comparisons, and evidence.
- If evidence is weak or extraction is partial, say that explicitly instead of smoothing it over.

Paper metadata:
- Title: {metadata.get('title', 'Unknown')}
- Authors: {", ".join(metadata.get('authors', []))}
- Abstract: {metadata.get('abstract', 'Not available')}

Paper map:
{json.dumps(paper_map, ensure_ascii=True)}

Section breakdown:
{section_notes[:12000]}

Results view:
{json.dumps(results_view, ensure_ascii=True)}

Math ideas:
{formulas_text or '- None available'}

Key terms:
{key_terms or '- None extracted'}

Artifact interpretations:
{artifact_notes or '- None interpreted'}

Return strict JSON:
{{
  "quick_summary": "2-4 sentence overview",
  "guided_walkthrough": "multi-paragraph guided walkthrough of the whole paper",
  "eli5_explanation": "substantial plain-language walkthrough for a non-expert",
  "technical_summary": "detailed but concise technical summary covering method and evidence",
  "problem_and_motivation": "why this paper exists",
  "prior_work_and_gap": "what was attempted before this paper and what specific gap or limitation it addresses",
  "core_intuition": "the central idea of the paper in one plain-English paragraph before any formulas or notation",
  "authors_claims": "what the paper explicitly asserts as its contribution and conclusion",
  "evidence_assessment": "what the extracted evidence actually supports; note any gap between this and authors_claims",
  "method_deep_dive": "how the approach works",
  "results_and_evidence": "what evidence the paper shows",
  "limitations_and_caveats": "limitations, tradeoffs, or missing evidence",
  "key_contributions": ["specific contribution"],
  "key_findings": ["specific finding or result"],
  "reader_takeaways": ["what the reader should remember"],
  "section_breakdown": [{{"title": "section", "summary": "summary", "why_it_matters": "why it matters"}}]
}}"""

        fallback = {
            "quick_summary": metadata.get("abstract", "Summary unavailable"),
            "guided_walkthrough": metadata.get("abstract", "Walkthrough unavailable"),
            "eli5_explanation": metadata.get("abstract", "Simple explanation unavailable"),
            "technical_summary": metadata.get("abstract", "Technical summary unavailable"),
            "problem_and_motivation": metadata.get("abstract", ""),
            "prior_work_and_gap": metadata.get("abstract", ""),
            "core_intuition": paper_map.get("proposed_solution", ""),
            "authors_claims": metadata.get("abstract", ""),
            "evidence_assessment": results_view.get("results_summary", ""),
            "method_deep_dive": "Method summary unavailable",
            "results_and_evidence": results_view.get("results_summary", "Results summary unavailable"),
            "limitations_and_caveats": "; ".join(self._coerce_list(results_view.get("caveats"))),
            "key_contributions": [],
            "key_findings": [],
            "reader_takeaways": [],
            "section_breakdown": [
                {
                    "title": section.get("title", "Untitled section"),
                    "summary": section.get("summary", ""),
                    "why_it_matters": section.get("why_it_matters", ""),
                }
                for section in section_breakdown
            ],
        }
        result = await self._chat_json(
            "You synthesize multi-pass paper analyses into a coherent, reader-friendly distillation.",
            prompt,
            fallback,
        )
        if isinstance(result, dict):
            return result
        return fallback

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
    )
    async def repair_distillation(
        self,
        synthesis: Dict[str, Any],
        metadata: Dict[str, Any],
        paper_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""Expand this research paper distillation where it is too shallow for a non-expert reader.

Rules:
- Keep all claims grounded in the existing synthesis and paper map.
- Strengthen only the guided walkthrough, ELI5 explanation, method explanation, and limitations.
- Do not rewrite the quick summary unless necessary.

Paper title: {metadata.get('title', 'Unknown')}
Paper map: {json.dumps(paper_map, ensure_ascii=True)}
Current synthesis: {json.dumps(synthesis, ensure_ascii=True)}

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
}}"""

        fallback = {
            "guided_walkthrough": synthesis.get("guided_walkthrough", ""),
            "eli5_explanation": synthesis.get("eli5_explanation", ""),
            "method_deep_dive": synthesis.get("method_deep_dive", ""),
            "limitations_and_caveats": synthesis.get("limitations_and_caveats", ""),
            "prior_work_and_gap": synthesis.get("prior_work_and_gap", ""),
            "core_intuition": synthesis.get("core_intuition", ""),
            "authors_claims": synthesis.get("authors_claims", ""),
            "evidence_assessment": synthesis.get("evidence_assessment", ""),
        }
        result = await self._chat_json(
            "You deepen shallow research paper summaries without inventing facts.",
            prompt,
            fallback,
        )
        if not isinstance(result, dict):
            return synthesis

        synthesis.update({
            "guided_walkthrough": result.get("guided_walkthrough", synthesis.get("guided_walkthrough")),
            "eli5_explanation": result.get("eli5_explanation", synthesis.get("eli5_explanation")),
            "method_deep_dive": result.get("method_deep_dive", synthesis.get("method_deep_dive")),
            "limitations_and_caveats": result.get("limitations_and_caveats", synthesis.get("limitations_and_caveats")),
            "prior_work_and_gap": result.get("prior_work_and_gap", synthesis.get("prior_work_and_gap")),
            "core_intuition": result.get("core_intuition", synthesis.get("core_intuition")),
            "authors_claims": result.get("authors_claims", synthesis.get("authors_claims")),
            "evidence_assessment": result.get("evidence_assessment", synthesis.get("evidence_assessment")),
        })
        return synthesis

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
            f"## {field}\n{(summary_json.get(field) or '')[:1400]}"
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

    async def generate_summary(self, paper_text: str, metadata: Dict) -> Dict[str, Any]:
        paper_map = await self.map_paper(paper_text, metadata)
        section_breakdown = await self.distill_sections(paper_text, metadata, paper_map)
        table_interpretations, figure_interpretations = await self._gather_artifact_interpretations(metadata, paper_map, section_breakdown)
        results_view = await self.extract_results_view(
            metadata,
            section_breakdown,
            paper_map,
            table_interpretations,
            figure_interpretations,
        )
        formula_explanations = await self.explain_math_from_sections(paper_text, metadata, paper_map, section_breakdown)
        terms = await self.extract_terms(paper_text)
        synthesis = await self.synthesize_distillation(
            metadata,
            paper_map,
            section_breakdown,
            results_view,
            formula_explanations,
            terms,
            table_interpretations,
            figure_interpretations,
        )

        if (
            len((synthesis.get("eli5_explanation") or "").strip()) < 420
            or len((synthesis.get("guided_walkthrough") or "").strip()) < 800
        ):
            synthesis = await self.repair_distillation(synthesis, metadata, paper_map)

        synthesis["paper_map"] = paper_map
        synthesis["results_view"] = results_view
        synthesis["terms"] = terms
        synthesis["formula_explanations"] = formula_explanations
        synthesis["table_interpretations"] = table_interpretations
        synthesis["figure_interpretations"] = figure_interpretations
        return synthesis

    async def _gather_artifact_interpretations(
        self,
        metadata: Dict[str, Any],
        paper_map: Dict[str, Any],
        section_breakdown: List[Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if self.client is None:
            return [], []
        table_result, figure_result = await self._gather_or_default(
            self.interpret_tables(metadata, paper_map, section_breakdown),
            self.interpret_figures(metadata, paper_map, section_breakdown),
        )
        return table_result, figure_result

    async def _gather_or_default(self, *coroutines):
        results = await self._safe_gather(*coroutines)
        normalized = []
        for item in results:
            normalized.append([] if isinstance(item, Exception) else item)
        return tuple(normalized)

    async def _safe_gather(self, *coroutines):
        return await asyncio.gather(*coroutines, return_exceptions=True)
