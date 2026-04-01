import asyncio

from app.models.analysis import PaperAnalysis
from app.models.paper import Paper
from app.services.ai_processor import AIProcessor
from app.services.ingestion import IngestionService
from app.services.knowledge_graph import KnowledgeGraphBuilder
from app.services.pdf_parser import PDFParser
from app.workers.celery_app import celery_app


@celery_app.task
def process_paper_task(paper_id: str, arxiv_id: str):
    from app.models.database import SessionLocal

    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).first()
        if not paper or not analysis:
            return

        analysis.error_message = None
        db.commit()

        def update_progress(step: str, percent: int):
            analysis.progress_step = step
            analysis.progress_percent = percent
            db.commit()

        update_progress("Downloading paper...", 10)
        ingestion = IngestionService()
        pdf_bytes = asyncio.run(ingestion.download_pdf(paper.pdf_url))
        if not pdf_bytes:
            analysis.processing_status = "failed"
            analysis.error_message = "Failed to download PDF from arXiv"
            analysis.progress_percent = 100
            db.commit()
            return

        update_progress("Parsing PDF...", 25)
        parser = PDFParser()
        parsed = parser.parse_pdf(pdf_bytes)

        if parsed.get("error"):
            analysis.processing_status = "failed"
            analysis.error_message = f"PDF parsing failed: {parsed['error']}"
            analysis.progress_percent = 100
            db.commit()
            return

        if not parsed.get("text"):
            analysis.processing_status = "failed"
            analysis.error_message = "No text could be extracted from the PDF"
            analysis.progress_percent = 100
            db.commit()
            return

        update_progress("Generating AI summaries...", 30)

        async def process_all():
            processor = AIProcessor()
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
            paper_map = await processor.map_paper(parsed["text"], summary_metadata)

            update_progress("Distilling major sections...", 50)
            section_breakdown = await processor.distill_sections(parsed["text"], summary_metadata, paper_map)

            update_progress("Extracting evidence and math...", 60)
            formulas_task = processor.explain_formulas(parsed["formulas"])
            terms_task = processor.extract_terms(parsed["text"])
            table_interp_task = processor.interpret_tables(summary_metadata, paper_map, section_breakdown)
            figure_interp_task = processor.interpret_figures(summary_metadata, paper_map, section_breakdown)

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

            results_view = await processor.extract_results_view(
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
                fallback_math = await processor.explain_math_from_sections(
                    parsed["text"],
                    summary_metadata,
                    paper_map,
                    section_breakdown,
                )
                if fallback_math:
                    formula_explanations = fallback_math

            update_progress("Synthesizing final distillation...", 74)
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

            if (
                len((synthesis.get("eli5_explanation") or "").strip()) < 420
                or len((synthesis.get("guided_walkthrough") or "").strip()) < 800
            ):
                update_progress("Deepening the walkthrough...", 78)
                synthesis = await processor.repair_distillation(synthesis, summary_metadata, paper_map)

            return (
                synthesis,
                formula_explanations,
                terms,
                paper_map,
                section_breakdown,
                results_view,
                table_interpretations,
                figure_interpretations,
            )

        result = asyncio.run(process_all())
        if result is None:
            analysis.processing_status = "failed"
            analysis.error_message = "AI processing failed - service unavailable or timeout"
            analysis.progress_percent = 100
            db.commit()
            return

        (
            summary,
            formula_explanations,
            terms,
            paper_map,
            section_breakdown,
            results_view,
            table_interpretations,
            figure_interpretations,
        ) = result

        if isinstance(summary, Exception):
            raise summary

        update_progress("Building knowledge graph...", 80)
        kg_builder = KnowledgeGraphBuilder()
        knowledge_graph = kg_builder.build(
            terms,
            parsed["text"],
            results_view.get("artifact_interpretations", []),
            results_view,
            paper_map,
        )

        update_progress("Saving results...", 90)
        analysis.summary_json = {
            "quick": summary.get("quick_summary"),
            "eli5": summary.get("eli5_explanation"),
            "technical": summary.get("technical_summary"),
            "key_contributions": summary.get("key_contributions"),
            "key_findings": summary.get("key_findings"),
            "formula_explanations": formula_explanations,
            "figure_captions": parsed.get("figure_captions", []),
            "tables": parsed.get("tables", []),
            "guided_walkthrough": summary.get("guided_walkthrough"),
            "problem_and_motivation": summary.get("problem_and_motivation"),
            "method_deep_dive": summary.get("method_deep_dive"),
            "results_and_evidence": summary.get("results_and_evidence"),
            "limitations_and_caveats": summary.get("limitations_and_caveats"),
            "reader_takeaways": summary.get("reader_takeaways"),
            "section_breakdown": summary.get("section_breakdown") or section_breakdown,
            "paper_map": paper_map,
            "results_view": results_view,
            "artifact_interpretations": results_view.get("artifact_interpretations", []),
            "table_interpretations": table_interpretations,
            "figure_interpretations": figure_interpretations,
            "terms": terms,
        }
        analysis.knowledge_graph_json = knowledge_graph
        analysis.processing_status = "complete"
        analysis.progress_step = "Complete!"
        analysis.progress_percent = 100
        analysis.error_message = None
        db.commit()
    except Exception as exc:
        analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).first()
        if analysis:
            analysis.processing_status = "failed"
            analysis.error_message = f"Unexpected error: {str(exc)}"
            analysis.progress_percent = 100
            db.commit()
    finally:
        db.close()
