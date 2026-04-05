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


def test_build_without_triples_is_backward_compatible():
    from app.services.knowledge_graph import KnowledgeGraphBuilder
    builder = KnowledgeGraphBuilder()
    terms = [
        {"term": "Transformer", "category": "method", "definition": "Attn model", "mentions": 5},
    ]
    # Should not raise — relationship_triples defaults to None
    result = builder.build(terms, "some text")
    assert "nodes" in result
    assert "edges" in result
