import asyncio

from app.models.analysis import PaperAnalysis
from app.models.paper import Paper
from app.services.analysis_pipeline import AnalysisPipeline
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
        result = asyncio.run(
            AnalysisPipeline().run(
                parsed=parsed,
                paper=paper,
                update_progress=update_progress,
            )
        )
        if result is None:
            analysis.processing_status = "failed"
            analysis.error_message = "AI processing failed - service unavailable or timeout"
            analysis.progress_percent = 100
            db.commit()
            return

        terms = result.terms
        paper_map = result.paper_map
        results_view = result.results_view
        relationship_triples = result.relationship_triples

        update_progress("Building knowledge graph...", 90)
        kg_builder = KnowledgeGraphBuilder()
        knowledge_graph = kg_builder.build(
            terms,
            parsed["text"],
            results_view.get("artifact_interpretations", []),
            results_view,
            paper_map,
            relationship_triples=relationship_triples,
        )

        update_progress("Saving results...", 90)
        analysis.summary_json = result.summary.model_dump()
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
