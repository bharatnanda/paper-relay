import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from app.schemas.paper import AnalysisSummary
from app.services.ai_processor import AIProcessor


@dataclass
class AnalysisPipelineResult:
    summary: AnalysisSummary
    critique: Dict[str, Any]
    formula_explanations: List[Dict[str, Any]]
    terms: List[Dict[str, Any]]
    paper_map: Dict[str, Any]
    section_breakdown: List[Dict[str, Any]]
    results_view: Dict[str, Any]
    table_interpretations: List[Dict[str, Any]]
    figure_interpretations: List[Dict[str, Any]]
    relationship_triples: List[Dict[str, str]]


class AnalysisPipeline:
    def __init__(self, processor: Optional[AIProcessor] = None):
        self.processor = processor or AIProcessor()

    async def run(
        self,
        *,
        parsed: Dict[str, Any],
        paper: Any,
        update_progress: Callable[[str, int], None],
    ) -> AnalysisPipelineResult:
        summary_metadata = {
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract,
            "arxiv_id": paper.arxiv_id,
            "sections": parsed.get("sections", []),
            "figure_captions": parsed.get("figure_captions", [])[:12],
            "tables": parsed.get("tables", [])[:8],
        }

        update_progress("Mapping the paper...", 40)
        paper_map = await self.processor.map_paper(parsed["text"], summary_metadata)

        update_progress("Distilling major sections...", 50)
        section_breakdown = await self.processor.distill_sections(parsed["text"], summary_metadata, paper_map)

        update_progress("Extracting evidence and math...", 60)
        formulas_task = self.processor.explain_formulas(parsed["formulas"])
        terms_task = self.processor.extract_terms(parsed["text"])
        table_interp_task = self.processor.interpret_tables(summary_metadata, paper_map, section_breakdown)
        figure_interp_task = self.processor.interpret_figures(summary_metadata, paper_map, section_breakdown)

        formula_explanations, terms, table_interpretations, figure_interpretations = await asyncio.gather(
            formulas_task,
            terms_task,
            table_interp_task,
            figure_interp_task,
            return_exceptions=True,
        )

        if isinstance(formula_explanations, Exception):
            formula_explanations = []
        if isinstance(terms, Exception):
            terms = []
        if isinstance(table_interpretations, Exception):
            table_interpretations = []
        if isinstance(figure_interpretations, Exception):
            figure_interpretations = []

        results_view = await self.processor.extract_results_view(
            summary_metadata,
            section_breakdown,
            paper_map,
            table_interpretations,
            figure_interpretations,
        )
        if isinstance(results_view, Exception):
            results_view = {
                "evaluation_setup": "Evaluation setup unavailable",
                "results_summary": "Results summary unavailable",
                "strongest_evidence": [],
                "caveats": [],
                "artifact_interpretations": [*table_interpretations, *figure_interpretations],
            }

        if not formula_explanations:
            update_progress("Recovering key math ideas...", 68)
            fallback_math = await self.processor.explain_math_from_sections(
                parsed["text"],
                summary_metadata,
                paper_map,
                section_breakdown,
            )
            if fallback_math:
                formula_explanations = fallback_math

        update_progress("Generating concept relationships...", 72)
        try:
            relationship_triples = await self.processor.generate_relationships(
                terms, section_breakdown, paper_map
            )
        except Exception:
            relationship_triples = []

        update_progress("Synthesizing final distillation...", 76)
        summary = await self.processor.synthesize_distillation(
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
        try:
            critique = await self.processor.critique_distillation(
                summary, paper_map, section_breakdown, results_view, summary_metadata
            )
        except Exception:
            critique = {"needs_revision": False, "overall_assessment": "", "issues": []}

        if critique.get("needs_revision"):
            update_progress("Revising based on critique...", 84)
            try:
                summary = await self.processor.revise_with_critique(
                    summary, critique, paper_map, summary_metadata
                )
            except Exception:
                pass

        if (
            len((summary.get("eli5") or "").strip()) < 420
            or len((summary.get("guided_walkthrough") or "").strip()) < 800
        ):
            update_progress("Deepening the walkthrough...", 88)
            summary = await self.processor.repair_distillation(summary, summary_metadata, paper_map)

        summary = AnalysisSummary.model_validate({
            **summary.model_dump(),
            "critique": critique,
            "formula_explanations": formula_explanations,
            "figure_captions": parsed.get("figure_captions", []),
            "tables": parsed.get("tables", []),
            "paper_map": paper_map,
            "section_breakdown": summary.section_breakdown or section_breakdown,
            "results_view": results_view,
            "artifact_interpretations": results_view.get("artifact_interpretations") or [],
            "table_interpretations": table_interpretations,
            "figure_interpretations": figure_interpretations,
            "terms": terms,
        })

        return AnalysisPipelineResult(
            summary=summary,
            critique=critique,
            formula_explanations=formula_explanations,
            terms=terms,
            paper_map=paper_map,
            section_breakdown=section_breakdown,
            results_view=results_view,
            table_interpretations=table_interpretations,
            figure_interpretations=figure_interpretations,
            relationship_triples=relationship_triples,
        )
