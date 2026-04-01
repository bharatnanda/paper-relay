from typing import Dict, Any, List, Optional
import re


class KnowledgeGraphBuilder:
    RELATIONSHIP_PATTERNS = {
        "uses": ["uses", "employs", "utilizes"],
        "improves": ["improves", "enhances", "boosts"],
        "compares_to": ["compares to", "versus", "vs"],
        "solves": ["solves", "addresses", "tackles"],
        "builds_on": ["builds on", "extends", "based on"],
    }

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self._edge_keys = set()

    def build(
        self,
        terms: List[Dict[str, Any]],
        paper_text: str,
        artifact_interpretations: Optional[List[Dict[str, Any]]] = None,
        results_view: Optional[Dict[str, Any]] = None,
        paper_map: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.nodes = {}
        self.edges = []
        self._edge_keys = set()

        artifact_interpretations = artifact_interpretations or []
        results_view = results_view or {}
        paper_map = paper_map or {}

        self._create_term_nodes(terms)
        self._create_artifact_nodes(artifact_interpretations)
        self._create_results_nodes(results_view)
        self._create_focus_node(paper_map)

        self._connect_artifacts_to_terms(artifact_interpretations, terms)
        self._connect_results_to_terms(results_view, terms)
        self._connect_focus_to_terms(paper_map, terms)
        self._detect_text_relationships(terms, paper_text)

        return {"nodes": list(self.nodes.values()), "edges": self.edges}

    def _create_term_nodes(self, terms: List[Dict[str, Any]]) -> None:
        for term in terms:
            node_id = self._node_id(term["term"])
            self.nodes[node_id] = {
                "id": node_id,
                "label": term["term"],
                "category": term["category"],
                "definition": term.get("definition", ""),
                "value": term.get("mentions", 1),
            }

    def _create_artifact_nodes(self, artifact_interpretations: List[Dict[str, Any]]) -> None:
        for artifact in artifact_interpretations:
            label = artifact.get("label")
            if not label:
                continue
            node_id = self._node_id(f"artifact::{label}")
            self.nodes[node_id] = {
                "id": node_id,
                "label": label,
                "category": "evidence",
                "definition": artifact.get("what_it_shows", ""),
                "value": 3,
            }

    def _create_results_nodes(self, results_view: Dict[str, Any]) -> None:
        for index, finding in enumerate(results_view.get("strongest_evidence") or []):
            if not finding:
                continue
            node_id = self._node_id(f"finding::{index}::{finding[:40]}")
            self.nodes[node_id] = {
                "id": node_id,
                "label": f"Finding {index + 1}",
                "category": "finding",
                "definition": finding,
                "value": 2,
            }

    def _create_focus_node(self, paper_map: Dict[str, Any]) -> None:
        main_question = paper_map.get("main_question")
        if not main_question:
            return
        node_id = "paper_focus"
        self.nodes[node_id] = {
            "id": node_id,
            "label": "Paper focus",
            "category": "concept",
            "definition": main_question,
            "value": 2,
        }

    def _connect_artifacts_to_terms(self, artifact_interpretations: List[Dict[str, Any]], terms: List[Dict[str, Any]]) -> None:
        for artifact in artifact_interpretations:
            label = artifact.get("label")
            if not label:
                continue
            source_id = self._node_id(f"artifact::{label}")
            artifact_text = " ".join(
                part for part in (artifact.get("what_it_shows"), artifact.get("why_it_matters"), artifact.get("section_title")) if part
            )
            for term in self._terms_mentioned_in_text(artifact_text, terms):
                self._add_edge(source_id, self._node_id(term["term"]), "supports", 1.2)

    def _connect_results_to_terms(self, results_view: Dict[str, Any], terms: List[Dict[str, Any]]) -> None:
        for index, finding in enumerate(results_view.get("strongest_evidence") or []):
            if not finding:
                continue
            source_id = self._node_id(f"finding::{index}::{finding[:40]}")
            for term in self._terms_mentioned_in_text(finding, terms):
                self._add_edge(source_id, self._node_id(term["term"]), "supports", 1.1)

        for artifact in results_view.get("artifact_interpretations") or []:
            label = artifact.get("label")
            if not label:
                continue
            artifact_id = self._node_id(f"artifact::{label}")
            for index, finding in enumerate(results_view.get("strongest_evidence") or []):
                if finding and label.lower() in finding.lower():
                    finding_id = self._node_id(f"finding::{index}::{finding[:40]}")
                    self._add_edge(artifact_id, finding_id, "evidences", 1.0)

    def _connect_focus_to_terms(self, paper_map: Dict[str, Any], terms: List[Dict[str, Any]]) -> None:
        if "paper_focus" not in self.nodes:
            return
        focus_text = " ".join(
            part
            for part in (
                paper_map.get("main_question"),
                paper_map.get("proposed_solution"),
                paper_map.get("results_focus"),
            )
            if part
        )
        for term in self._terms_mentioned_in_text(focus_text, terms):
            self._add_edge("paper_focus", self._node_id(term["term"]), "centers_on", 1.0)

    def _detect_text_relationships(self, terms: List[Dict[str, Any]], paper_text: str) -> None:
        text_lower = paper_text.lower()
        sentences = [segment.strip() for segment in re.split(r'(?<=[.!?])\s+', text_lower) if segment.strip()]
        for i, t1 in enumerate(terms):
            for t2 in terms[i + 1:]:
                rel = self._find_relationship(t1["term"], t2["term"], sentences, text_lower)
                if rel:
                    self._add_edge(
                        self._node_id(t1["term"]),
                        self._node_id(t2["term"]),
                        rel,
                        0.9 if rel == "related_to" else 1.0,
                    )

    def _find_relationship(self, term1: str, term2: str, sentences: List[str], text: str) -> Optional[str]:
        term1_escaped = re.escape(term1.lower())
        term2_escaped = re.escape(term2.lower())

        for sentence in sentences:
            if term1.lower() not in sentence or term2.lower() not in sentence:
                continue
            for rel_type, patterns in self.RELATIONSHIP_PATTERNS.items():
                for pattern in patterns:
                    if re.search(f"{term1_escaped}.{{0,120}}{pattern}.{{0,120}}{term2_escaped}", sentence):
                        return rel_type
                    if re.search(f"{term2_escaped}.{{0,120}}{pattern}.{{0,120}}{term1_escaped}", sentence):
                        return rel_type

        if self._co_occur(term1.lower(), term2.lower(), text):
            return "related_to"
        return None

    def _terms_mentioned_in_text(self, text: str, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = (text or "").lower()
        return [term for term in terms if term.get("term") and term["term"].lower() in normalized]

    def _add_edge(self, source: str, target: str, edge_type: str, weight: float) -> None:
        if source == target or source not in self.nodes or target not in self.nodes:
            return
        key = (source, target, edge_type)
        if key in self._edge_keys:
            return
        self._edge_keys.add(key)
        self.edges.append(
            {
                "source": source,
                "target": target,
                "type": edge_type,
                "weight": weight,
            }
        )

    def _co_occur(self, term1: str, term2: str, text: str, window: int = 200) -> bool:
        pos1, pos2 = text.find(term1), text.find(term2)
        return pos1 != -1 and pos2 != -1 and abs(pos1 - pos2) < window

    def _node_id(self, label: str) -> str:
        normalized = re.sub(r"[^a-z0-9_]+", "_", label.lower().replace(" ", "_")).strip("_")
        return normalized or "node"
