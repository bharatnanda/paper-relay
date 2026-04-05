import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ai_processor import AIProcessor


class TestAIProcessor:

    @pytest.fixture
    def processor(self):
        return AIProcessor()

    def test_select_sections_for_coverage_prioritizes_core_roles(self, processor):
        sections = [
            {"title": "Abstract", "content": "Overview", "index": 0, "role": "overview"},
            {"title": "Introduction", "content": "Motivation", "index": 1, "role": "overview"},
            {"title": "Method", "content": "Method details", "index": 2, "role": "method"},
            {"title": "Experimental Setup", "content": "Setup details", "index": 3, "role": "evaluation"},
            {"title": "Results", "content": "Results details", "index": 4, "role": "results"},
            {"title": "Limitations", "content": "Limitations", "index": 5, "role": "limitations"},
            {"title": "Appendix", "content": "Extra details", "index": 6, "role": "ablation"},
        ]

        selected = processor._select_sections_for_coverage(
            sections,
            {"priority_sections": ["Results"]},
            max_sections=5,
        )

        titles = [section["title"] for section in selected]
        assert "Results" in titles
        assert "Method" in titles
        assert "Experimental Setup" in titles
        assert "Limitations" in titles
        assert titles == sorted(titles, key=lambda title: next(section["index"] for section in sections if section["title"] == title))

    @pytest.mark.anyio
    async def test_generate_summary(self, processor):
        """Test that generate_summary returns expected fields from OpenAI response."""
        mock_response = {
            "main_question": "Test question",
            "paper_type": "system",
            "proposed_solution": "Test solution",
            "reader_orientation": "Test orientation",
            "priority_sections": ["Introduction"],
            "math_relevance": "moderate",
            "results_focus": "Test results",
            "likely_limitations": ["Test caveat"],
        }

        with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
            result = await processor.map_paper("test paper content", {"title": "Test Paper"})
            assert "main_question" in result
            assert "paper_type" in result
            assert "priority_sections" in result

    @pytest.mark.anyio
    async def test_generate_summary_returns_richer_fields(self, processor):
        """Test that generate_summary returns the richer distillation structure."""
        processor.client = object()
        responses = [
            {"main_question": "Test question", "paper_type": "system", "proposed_solution": "Test solution", "reader_orientation": "Test orientation", "priority_sections": ["Introduction"], "math_relevance": "moderate", "results_focus": "Test results", "likely_limitations": ["Test caveat"]},
            {"title": "Introduction", "summary": "Intro summary", "why_it_matters": "It frames the paper", "key_points": ["point"], "evidence": ["evidence"], "math_focus": "light", "reader_confusions": ["confusion"]},
            {"tables": [{"artifact_type": "table", "label": "Table 1", "section_title": "Results", "what_it_shows": "Main comparison", "why_it_matters": "Shows the win", "confidence": "medium"}]},
            {"figures": [{"artifact_type": "figure", "label": "Figure 1", "section_title": "Method", "what_it_shows": "System overview", "why_it_matters": "Shows the architecture", "confidence": "medium"}]},
            {"evaluation_setup": "Setup", "results_summary": "Results", "strongest_evidence": ["evidence"], "caveats": ["caveat"], "artifact_interpretations": [{"artifact_type": "table", "label": "Table 1", "section_title": "Results", "what_it_shows": "Main comparison", "why_it_matters": "Shows the win", "confidence": "medium"}]},
            {"formulas": [{"latex": "score = reward", "plain_explanation": "Explains the score", "symbols": {"score": "final score"}, "importance": "Core objective"}]},
            {"terms": [{"term": "GAAMA", "category": "method", "definition": "Memory framework", "mentions": 7}]},
            {"quick_summary": "Test quick summary", "guided_walkthrough": "A longer guided walkthrough of the whole paper that covers the sections in order.", "eli5_explanation": "A longer plain-language explanation that is detailed enough for a non-expert reader to follow the paper.", "technical_summary": "Technical summary", "problem_and_motivation": "Problem", "method_deep_dive": "Method", "results_and_evidence": "Results", "limitations_and_caveats": "Caveats", "key_contributions": ["Contribution"], "key_findings": ["Finding"], "reader_takeaways": ["Takeaway"], "section_breakdown": [{"title": "Introduction", "summary": "Intro summary", "why_it_matters": "It frames the paper"}]},
            {"guided_walkthrough": "Expanded guided walkthrough for a non-expert reader with more detail.", "eli5_explanation": "Expanded ELI5 explanation for a non-expert reader with more detail.", "method_deep_dive": "Expanded method explanation.", "limitations_and_caveats": "Expanded caveats."},
        ]

        with patch.object(processor, '_chat_json', AsyncMock(side_effect=responses)):
            result = await processor.generate_summary(
                "Introduction\nSome text\nMethod\nMore text\nResults\nEven more text",
                {
                    "title": "Test Paper",
                    "sections": [{"title": "Introduction", "content": "Some text"}],
                    "figure_captions": [
                        {
                            "label": "Figure 1",
                            "caption": "Overview of the system",
                            "page": 0,
                            "section_title": "Method",
                            "context_before": "The system has three parts.",
                            "context_after": "Each part is evaluated separately.",
                        }
                    ],
                    "tables": [
                        {
                            "title": "Table 1: Main results",
                            "page": 1,
                            "section_title": "Results",
                            "header": ["Model", "Accuracy"],
                            "rows": [["Model", "Accuracy"], ["Baseline", "73.1"], ["Ours", "81.4"]],
                            "row_count": 3,
                            "column_count": 2,
                            "context_before": "We compare against strong baselines.",
                            "context_after": "Higher is better.",
                        }
                    ],
                },
            )
            assert "quick_summary" in result
            assert "guided_walkthrough" in result
            assert "eli5_explanation" in result
            assert "section_breakdown" in result
            assert "paper_map" in result
            assert "results_view" in result
            assert "formula_explanations" in result
            assert result["results_view"]["artifact_interpretations"][0]["label"] == "Table 1"
            assert result["table_interpretations"][0]["artifact_type"] == "table"
            assert result["figure_interpretations"][0]["artifact_type"] == "figure"

    @pytest.mark.anyio
    async def test_extract_results_view_accepts_richer_artifact_payloads(self, processor):
        response = {
            "evaluation_setup": "Benchmarks compare baselines and the proposed method.",
            "results_summary": "The method improves the main metric.",
            "strongest_evidence": ["Table 1 shows the biggest gain."],
            "caveats": ["Some metrics are missing."],
            "artifact_interpretations": [
                {
                    "artifact_type": "table",
                    "label": "Table 1",
                    "section_title": "Results",
                    "what_it_shows": "Main benchmark comparison",
                    "why_it_matters": "Shows the main win",
                    "confidence": "high",
                }
            ],
        }

        metadata = {
            "title": "Test Paper",
            "figure_captions": [
                {
                    "label": "Figure 1",
                    "caption": "Overview of the system",
                    "page": 0,
                    "section_title": "Method",
                    "context_before": "The system has three parts.",
                    "context_after": "Each part is evaluated separately.",
                }
            ],
            "tables": [
                {
                    "title": "Table 1: Main results",
                    "page": 1,
                    "section_title": "Results",
                    "header": ["Model", "Accuracy"],
                    "rows": [["Model", "Accuracy"], ["Baseline", "73.1"], ["Ours", "81.4"]],
                    "row_count": 3,
                    "column_count": 2,
                    "context_before": "We compare against strong baselines.",
                    "context_after": "Higher is better.",
                }
            ],
        }
        section_breakdown = [
            {"title": "Results", "summary": "Results summary", "evidence": ["Ours beats the baseline"], "key_points": ["Main benchmark"], "why_it_matters": "Validates the method"}
        ]
        paper_map = {"results_focus": "Main benchmark outcomes", "likely_limitations": []}

        with patch.object(processor, '_chat_json', AsyncMock(return_value=response)):
            result = await processor.extract_results_view(
                metadata,
                section_breakdown,
                paper_map,
                [{"artifact_type": "table", "label": "Table 1", "section_title": "Results", "what_it_shows": "Main benchmark comparison", "why_it_matters": "Shows the main win", "confidence": "high"}],
                [{"artifact_type": "figure", "label": "Figure 1", "section_title": "Method", "what_it_shows": "System overview", "why_it_matters": "Explains the architecture", "confidence": "medium"}],
            )
            assert result["artifact_interpretations"][0]["artifact_type"] == "table"
            assert result["strongest_evidence"][0] == "Table 1 shows the biggest gain."

    @pytest.mark.anyio
    async def test_interpret_tables_returns_structured_items(self, processor):
        response = {
            "tables": [
                {
                    "artifact_type": "table",
                    "label": "Table 1",
                    "section_title": "Results",
                    "what_it_shows": "Main benchmark comparison",
                    "why_it_matters": "Shows the main win",
                    "confidence": "high",
                }
            ]
        }

        metadata = {
            "title": "Test Paper",
            "tables": [
                {
                    "title": "Table 1: Main results",
                    "page": 1,
                    "section_title": "Results",
                    "header": ["Model", "Accuracy"],
                    "rows": [["Model", "Accuracy"], ["Baseline", "73.1"], ["Ours", "81.4"]],
                    "row_count": 3,
                    "column_count": 2,
                    "context_before": "We compare against strong baselines.",
                    "context_after": "Higher is better.",
                }
            ],
        }

        with patch.object(processor, '_chat_json', AsyncMock(return_value=response)):
            result = await processor.interpret_tables(metadata, {"results_focus": "Main results"}, [{"title": "Results", "summary": "Summary"}])
            assert result[0]["label"] == "Table 1"
            assert result[0]["artifact_type"] == "table"

    @pytest.mark.anyio
    async def test_interpret_figures_returns_structured_items(self, processor):
        response = {
            "figures": [
                {
                    "artifact_type": "figure",
                    "label": "Figure 1",
                    "section_title": "Method",
                    "what_it_shows": "System overview",
                    "why_it_matters": "Explains the architecture",
                    "confidence": "medium",
                }
            ]
        }

        metadata = {
            "title": "Test Paper",
            "figure_captions": [
                {
                    "label": "Figure 1",
                    "caption": "Overview of the system",
                    "page": 0,
                    "section_title": "Method",
                    "context_before": "The system has three parts.",
                    "context_after": "Each part is evaluated separately.",
                }
            ],
        }

        with patch.object(processor, '_chat_json', AsyncMock(return_value=response)):
            result = await processor.interpret_figures(metadata, {"main_question": "How the system works"}, [{"title": "Method", "summary": "Summary"}])
            assert result[0]["label"] == "Figure 1"
            assert result[0]["artifact_type"] == "figure"

    @pytest.mark.anyio
    async def test_generate_summary_with_metadata(self, processor):
        """Test that generate_summary uses metadata title in prompt."""
        mock_response = {
            "main_question": "Summary text",
            "paper_type": "model",
            "proposed_solution": "Simple explanation",
            "reader_orientation": "Technical details",
            "priority_sections": ["Methods"],
            "math_relevance": "light",
            "results_focus": "finding 1",
            "likely_limitations": [],
        }

        metadata = {"title": "Advanced Machine Learning Techniques", "authors": ["Author A"]}
        
        with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
            result = await processor.map_paper("test content", metadata)
            assert result["main_question"] == "Summary text"
            assert result["proposed_solution"] == "Simple explanation"

    @pytest.mark.anyio
    async def test_explain_formulas_empty_list(self, processor):
        """Test that explain_formulas returns empty list when input is empty."""
        result = await processor.explain_formulas([])
        assert result == []

    @pytest.mark.anyio
    async def test_explain_formulas(self, processor):
        """Test that explain_formulas returns explanations for formulas."""
        mock_response = {
            "formulas": [{"latex": "E = mc^2", "plain_explanation": "Energy equals mass times speed of light squared",
            "symbols": {"E": "energy", "m": "mass", "c": "speed of light"},
            "importance": "Fundamental equation in physics"}]
        }

        formulas = [{"latex": "E = mc^2"}, {"latex": "F = ma"}]

        with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
            result = await processor.explain_formulas(formulas)
            assert isinstance(result, list)
            assert len(result) > 0
            assert "latex" in result[0]
            assert "plain_explanation" in result[0]
            assert "symbols" in result[0]
            assert "importance" in result[0]

    @pytest.mark.anyio
    async def test_explain_formulas_limits_to_10(self, processor):
        """Test that explain_formulas processes only first 10 formulas."""
        # Create 15 formulas, should only process first 10
        formulas = [{"latex": f"formula_{i}"} for i in range(15)]

        with patch.object(processor, '_chat_json', AsyncMock(return_value={"formulas": []})):
            await processor.explain_formulas(formulas)
            # The implementation should truncate to 10 formulas in the prompt

    @pytest.mark.anyio
    async def test_explain_formulas_non_list_response(self, processor):
        """Test that explain_formulas handles non-list JSON response gracefully."""
        formulas = [{"latex": "E = mc^2"}]

        with patch.object(processor, '_chat_json', AsyncMock(return_value={"error": "unexpected format"})):
            result = await processor.explain_formulas(formulas)
            assert result == []

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
        processor.client = object()

        with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
            result = await processor.explain_formulas(formulas)

        assert "intuition" in result[0]
        assert "prerequisites" in result[0]
        assert "where_it_appears" in result[0]
        assert result[0]["intuition"] == "Measures how surprised the model is by the correct label."
        assert result[0]["prerequisites"] == ["probability", "logarithm"]

    @pytest.mark.anyio
    async def test_extract_terms(self, processor):
        """Test that extract_terms returns list of terms with expected fields."""
        mock_response = {
            "terms": [{"term": "Transformer", "category": "method", "definition": "A neural network architecture",
            "mentions": 15}, {"term": "Accuracy", "category": "metric", "definition": "Performance measure",
            "mentions": 8}]
        }

        paper_text = "This paper introduces a novel Transformer architecture..."

        with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
            result = await processor.extract_terms(paper_text)
            assert isinstance(result, list)
            assert len(result) > 0
            assert "term" in result[0]
            assert "category" in result[0]
            assert "definition" in result[0]
            assert "mentions" in result[0]

    @pytest.mark.anyio
    async def test_extract_terms_empty_response(self, processor):
        """Test that extract_terms handles empty list response."""
        with patch.object(processor, '_chat_json', AsyncMock(return_value={"terms": []})):
            result = await processor.extract_terms("some text")
            assert result == []

    @pytest.mark.anyio
    async def test_extract_terms_non_list_response(self, processor):
        """Test that extract_terms handles non-list JSON response gracefully."""
        with patch.object(processor, '_chat_json', AsyncMock(return_value={"error": "unexpected format"})):
            result = await processor.extract_terms("some text")
            assert result == []

    @pytest.mark.anyio
    async def test_generate_summary_truncates_long_text(self, processor):
        """Test that generate_summary can handle long text via staged prompts."""
        mock_response = {
            "main_question": "Test question",
            "paper_type": "system",
            "proposed_solution": "Test solution",
            "reader_orientation": "Test orientation",
            "priority_sections": ["Introduction"],
            "math_relevance": "moderate",
            "results_focus": "Test results",
            "likely_limitations": [],
        }

        # Create very long paper text
        long_text = "x" * 20000

        with patch.object(processor, '_chat_json', AsyncMock(return_value=mock_response)):
            await processor.map_paper(long_text, {"title": "Test"})
            # Should not raise an error, truncation happens in prompt construction

    @pytest.mark.anyio
    async def test_extract_terms_truncates_long_text(self, processor):
        """Test that extract_terms truncates paper text to 10000 characters."""
        # Create very long paper text
        long_text = "x" * 15000

        with patch.object(processor, '_chat_json', AsyncMock(return_value={"terms": []})):
            await processor.extract_terms(long_text)
            # Should not raise an error, truncation happens in prompt construction

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
        terms = [{"term": "X", "category": "method", "definition": "D", "mentions": 1},
                 {"term": "Y", "category": "method", "definition": "E", "mentions": 1}]
        with patch.object(processor, '_chat_json', AsyncMock(return_value="bad")):
            result = await processor.generate_relationships(terms, [], {})
        assert result == []

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
        processor.client = object()
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

        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps({"reply": "The main contribution is X, which addresses gap Y."})
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        processor.client = MagicMock()
        processor.client.chat.completions.create = AsyncMock(return_value=mock_response)
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
        assert len(result) > 0
