from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional
from datetime import datetime

class PaperMetadata(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: str
    published: Optional[datetime] = None
    categories: List[str] = []

class PaperAnalysisRequest(BaseModel):
    arxiv_url: str

class PaperAnalysisResponse(BaseModel):
    paper_id: str
    status: str = "pending"
    message: str = "Processing started"


class CritiqueIssue(BaseModel):
    field: str
    severity: Literal["high", "medium", "low"]
    type: Literal["overclaim", "missing_caveat", "vague_method", "evidence_gap", "coverage_gap"]
    description: str
    suggested_fix: str


class CritiqueSummary(BaseModel):
    needs_revision: bool
    overall_assessment: str
    issues: List[CritiqueIssue] = Field(default_factory=list)


class DistilledSection(BaseModel):
    title: str
    summary: str
    why_it_matters: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)


class PaperMap(BaseModel):
    main_question: Optional[str] = None
    paper_type: Optional[str] = None
    proposed_solution: Optional[str] = None
    reader_orientation: Optional[str] = None
    priority_sections: List[str] = Field(default_factory=list)
    math_relevance: Optional[str] = None
    results_focus: Optional[str] = None
    likely_limitations: List[str] = Field(default_factory=list)


class ArtifactInterpretation(BaseModel):
    artifact_type: str
    label: str
    section_title: Optional[str] = None
    what_it_shows: str
    why_it_matters: Optional[str] = None
    confidence: Optional[str] = None
    missing_context: Optional[str] = None


class ResultsView(BaseModel):
    evaluation_setup: Optional[str] = None
    results_summary: Optional[str] = None
    strongest_evidence: List[str] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)
    artifact_interpretations: List[ArtifactInterpretation] = Field(default_factory=list)


class DistilledTerm(BaseModel):
    term: str
    category: str
    definition: str
    mentions: int


class FormulaExplanation(BaseModel):
    latex: str
    plain_explanation: str
    symbols: Dict[str, str] = Field(default_factory=dict)
    importance: str
    intuition: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)
    where_it_appears: Optional[str] = None


class FigureCaption(BaseModel):
    label: str
    caption: str
    page: int
    section_title: Optional[str] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    context: Optional[str] = None


class ExtractedTable(BaseModel):
    title: str
    page: int
    section_title: Optional[str] = None
    header: List[str] = Field(default_factory=list)
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    context: Optional[str] = None
    rows: List[List[str]] = Field(default_factory=list)


class AnalysisSummary(BaseModel):
    quick: str
    eli5: str
    technical: str
    key_contributions: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    formula_explanations: List[FormulaExplanation] = Field(default_factory=list)
    figure_captions: List[FigureCaption] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    guided_walkthrough: Optional[str] = None
    problem_and_motivation: Optional[str] = None
    method_deep_dive: Optional[str] = None
    results_and_evidence: Optional[str] = None
    limitations_and_caveats: Optional[str] = None
    prior_work_and_gap: Optional[str] = None
    core_intuition: Optional[str] = None
    authors_claims: Optional[str] = None
    evidence_assessment: Optional[str] = None
    critique: Optional[CritiqueSummary] = None
    reader_takeaways: List[str] = Field(default_factory=list)
    section_breakdown: List[DistilledSection] = Field(default_factory=list)
    paper_map: Optional[PaperMap] = None
    results_view: Optional[ResultsView] = None
    artifact_interpretations: List[ArtifactInterpretation] = Field(default_factory=list)
    table_interpretations: List[ArtifactInterpretation] = Field(default_factory=list)
    figure_interpretations: List[ArtifactInterpretation] = Field(default_factory=list)
    terms: List[DistilledTerm] = Field(default_factory=list)

    @classmethod
    def from_storage(cls, summary_json: Optional[dict]) -> "AnalysisSummary":
        data = dict(summary_json or {})
        data.setdefault("quick", data.get("quick_summary", ""))
        data.setdefault("eli5", data.get("eli5_explanation", ""))
        data.setdefault("technical", data.get("technical_summary", ""))
        data.setdefault("method_deep_dive", data.get("technical"))
        data.setdefault("evidence_assessment", data.get("results_and_evidence"))
        return cls.model_validate(data)

    @classmethod
    def from_pipeline(
        cls,
        summary: dict,
        *,
        formula_explanations: Optional[List[dict]] = None,
        figure_captions: Optional[List[dict]] = None,
        tables: Optional[List[dict]] = None,
        section_breakdown: Optional[List[dict]] = None,
        paper_map: Optional[dict] = None,
        results_view: Optional[dict] = None,
        table_interpretations: Optional[List[dict]] = None,
        figure_interpretations: Optional[List[dict]] = None,
        terms: Optional[List[dict]] = None,
        critique: Optional[dict] = None,
    ) -> "AnalysisSummary":
        data = cls.from_storage(summary).model_dump()
        return cls(
            quick=data.get("quick", ""),
            eli5=data.get("eli5", ""),
            technical=data.get("technical", ""),
            key_contributions=data.get("key_contributions") or [],
            key_findings=data.get("key_findings") or [],
            formula_explanations=formula_explanations or [],
            figure_captions=figure_captions or [],
            tables=tables or [],
            guided_walkthrough=data.get("guided_walkthrough"),
            problem_and_motivation=data.get("problem_and_motivation"),
            method_deep_dive=data.get("method_deep_dive"),
            results_and_evidence=data.get("results_and_evidence"),
            limitations_and_caveats=data.get("limitations_and_caveats"),
            prior_work_and_gap=data.get("prior_work_and_gap"),
            core_intuition=data.get("core_intuition"),
            authors_claims=data.get("authors_claims"),
            evidence_assessment=data.get("evidence_assessment"),
            critique=critique,
            reader_takeaways=data.get("reader_takeaways") or [],
            section_breakdown=data.get("section_breakdown") or section_breakdown or [],
            paper_map=paper_map,
            results_view=results_view,
            artifact_interpretations=(results_view or {}).get("artifact_interpretations") or [],
            table_interpretations=table_interpretations or [],
            figure_interpretations=figure_interpretations or [],
            terms=terms or [],
        )


class PaperAnalysisComplete(BaseModel):
    paper_id: str
    status: str = "complete"
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    progress_step: Optional[str] = None
    progress_percent: Optional[int] = None
    error_message: Optional[str] = None
    summary: Optional[AnalysisSummary] = None
    knowledge_graph: Optional[dict] = None


class SharedPaperMetadata(BaseModel):
    id: str
    arxiv_id: Optional[str] = None
    title: str
    authors: List[str] = Field(default_factory=list)
    pdf_url: Optional[str] = None


class SharedPaperAnalysis(BaseModel):
    status: str
    summary: Optional[AnalysisSummary] = None
    knowledge_graph: Optional[dict] = None


class SharedPaperResponse(BaseModel):
    paper: SharedPaperMetadata
    analysis: SharedPaperAnalysis


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


class ReformatRequest(BaseModel):
    reading_level: Literal["general", "technical", "eli5"]


class ReformatResponse(BaseModel):
    reformatted_fields: dict[str, str]
