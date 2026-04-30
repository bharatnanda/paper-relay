from unittest.mock import AsyncMock, MagicMock, patch

from app.services.analysis_pipeline import AnalysisPipelineResult
from app.schemas.paper import AnalysisSummary
from app.workers.tasks import process_paper_task


def _make_fake_db(paper, analysis):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [paper, analysis]
    return mock_db


class TestProcessPaperTask:
    @patch("app.models.database.SessionLocal")
    @patch("app.workers.tasks.KnowledgeGraphBuilder")
    @patch("app.workers.tasks.AnalysisPipeline")
    @patch("app.workers.tasks.PDFParser")
    @patch("app.workers.tasks.IngestionService")
    def test_process_paper_task_persists_new_anatomy_fields(
        self,
        mock_ingestion_class,
        mock_parser_class,
        mock_pipeline_class,
        mock_kg_builder_class,
        mock_session_local,
    ):
        paper = MagicMock()
        paper.id = "paper-123"
        paper.title = "Test Paper"
        paper.authors = ["Author A"]
        paper.abstract = "Abstract text"
        paper.arxiv_id = "1234.5678"
        paper.pdf_url = "https://example.com/paper.pdf"

        analysis = MagicMock()
        analysis.paper_id = "paper-123"
        analysis.summary_json = None
        analysis.knowledge_graph_json = None
        analysis.processing_status = "pending"
        analysis.progress_step = None
        analysis.progress_percent = 0
        analysis.error_message = None

        mock_db = _make_fake_db(paper, analysis)
        mock_session_local.return_value = mock_db

        mock_ingestion = MagicMock()
        mock_ingestion.download_pdf = AsyncMock(return_value=b"%PDF-test")
        mock_ingestion_class.return_value = mock_ingestion

        parsed = {
            "text": "Paper text",
            "sections": [{"title": "Intro", "content": "Section text"}],
            "formulas": [],
            "figure_captions": [],
            "tables": [],
        }
        mock_parser = MagicMock()
        mock_parser.parse_pdf.return_value = parsed
        mock_parser_class.return_value = mock_parser

        mock_pipeline = MagicMock()
        mock_pipeline.run = AsyncMock(return_value=AnalysisPipelineResult(
            summary=AnalysisSummary.model_validate({
                "quick": "Quick summary.",
                "guided_walkthrough": "W" * 900,
                "eli5": "E" * 500,
                "technical": "Technical summary.",
                "problem_and_motivation": "Problem statement.",
                "prior_work_and_gap": "Prior work and gap.",
                "core_intuition": "Core intuition.",
                "authors_claims": "Authors claims.",
                "evidence_assessment": "Evidence assessment.",
                "bottom_line_verdict": "The paper is promising but needs broader validation.",
                "method_deep_dive": "Method details.",
                "results_and_evidence": "Results details.",
                "limitations_and_caveats": "Limitations.",
                "key_contributions": ["Contribution"],
                "key_findings": ["Finding"],
                "reader_takeaways": ["Takeaway"],
                "section_breakdown": [{"title": "Intro", "summary": "Summary"}],
            }),
            critique={"needs_revision": False, "overall_assessment": "Looks good.", "issues": []},
            formula_explanations=[],
            terms=[{"term": "Transformer", "category": "method", "definition": "A model", "mentions": 3}],
            paper_map={"main_question": "Q", "proposed_solution": "S", "math_relevance": "light"},
            section_breakdown=[{"title": "Intro", "summary": "Summary"}],
            results_view={
                "evaluation_setup": "Eval setup",
                "results_summary": "Result summary",
                "strongest_evidence": ["Evidence"],
                "caveats": ["Caveat"],
                "artifact_interpretations": [],
            },
            table_interpretations=[],
            figure_interpretations=[],
            relationship_triples=[{"source": "Transformer", "target": "Benchmark", "relationship": "evaluates"}],
        ))
        mock_pipeline_class.return_value = mock_pipeline

        mock_kg_builder = MagicMock()
        mock_kg_builder.build.return_value = {"nodes": [], "edges": []}
        mock_kg_builder_class.return_value = mock_kg_builder

        process_paper_task("paper-123", "1234.5678")

        assert analysis.processing_status == "complete"
        assert analysis.summary_json["prior_work_and_gap"] == "Prior work and gap."
        assert analysis.summary_json["core_intuition"] == "Core intuition."
        assert analysis.summary_json["authors_claims"] == "Authors claims."
        assert analysis.summary_json["evidence_assessment"] == "Evidence assessment."
        assert analysis.summary_json["bottom_line_verdict"] == "The paper is promising but needs broader validation."
        assert analysis.summary_json["quick"] == "Quick summary."
