import pytest

from app.services.knowledge_graph import KnowledgeGraphBuilder


class TestKnowledgeGraphBuilder:
    @pytest.fixture
    def builder(self):
        return KnowledgeGraphBuilder()

    def test_create_term_nodes(self, builder):
        terms = [{"term": "Transformer", "category": "method", "definition": "A neural network", "mentions": 10}]
        builder._create_term_nodes(terms)
        assert len(builder.nodes) == 1
        assert "transformer" in builder.nodes

    def test_detect_uses_relationship(self, builder):
        text = "our method uses transformers for better performance."
        sentences = [text]
        rel = builder._find_relationship("Method", "Transformers", sentences, text)
        assert rel == "uses"

    def test_build_graph_with_artifact_grounding(self, builder):
        terms = [
            {"term": "GAAMA", "category": "method", "definition": "Memory framework", "mentions": 6},
            {"term": "Accuracy", "category": "metric", "definition": "Main metric", "mentions": 5},
        ]
        artifact_interpretations = [
            {
                "artifact_type": "table",
                "label": "Table 1",
                "section_title": "Results",
                "what_it_shows": "GAAMA improves Accuracy over the baseline.",
                "why_it_matters": "This is the main benchmark result.",
                "confidence": "high",
            }
        ]
        results_view = {
            "strongest_evidence": ["Table 1 shows GAAMA improving Accuracy."],
            "artifact_interpretations": artifact_interpretations,
        }
        paper_map = {
            "main_question": "How can GAAMA improve retrieval quality?",
            "proposed_solution": "GAAMA augments memory retrieval.",
            "results_focus": "Accuracy on the benchmark.",
        }

        graph = builder.build(
            terms,
            "GAAMA improves Accuracy in the main experiment.",
            artifact_interpretations,
            results_view,
            paper_map,
        )

        node_ids = {node["id"] for node in graph["nodes"]}
        assert "gaama" in node_ids
        assert "accuracy" in node_ids
        assert "artifact_table_1" in node_ids
        assert "paper_focus" in node_ids

        edge_types = {(edge["source"], edge["target"], edge["type"]) for edge in graph["edges"]}
        assert ("artifact_table_1", "gaama", "supports") in edge_types
        assert ("artifact_table_1", "accuracy", "supports") in edge_types
        assert ("paper_focus", "gaama", "centers_on") in edge_types
