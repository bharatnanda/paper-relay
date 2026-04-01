export interface User {
  user_id: string;
  email: string;
  token: string;
  papers_count: number;
}

export interface Paper {
  id: string;
  arxiv_id: string;
  title: string;
  authors: string[];
  created_at: string;
}

export interface PaperAnalysis {
  paper_id: string;
  status: 'pending' | 'processing' | 'complete' | 'failed';
  title?: string;
  authors?: string[];
  arxiv_id?: string;
  pdf_url?: string;
  progress_step?: string;
  progress_percent?: number;
  error_message?: string;
  summary?: {
    quick: string;
    eli5: string;
    technical: string;
    key_contributions: string[];
    key_findings?: string[];
    formula_explanations: FormulaExplanation[];
    figure_captions?: FigureCaption[];
    tables?: ExtractedTable[];
    guided_walkthrough?: string;
    problem_and_motivation?: string;
    method_deep_dive?: string;
    results_and_evidence?: string;
    limitations_and_caveats?: string;
    reader_takeaways?: string[];
    section_breakdown?: DistilledSection[];
    paper_map?: PaperMap;
    results_view?: ResultsView;
    artifact_interpretations?: ArtifactInterpretation[];
    table_interpretations?: ArtifactInterpretation[];
    figure_interpretations?: ArtifactInterpretation[];
    terms?: DistilledTerm[];
  };
  knowledge_graph?: KnowledgeGraph;
}

export interface DistilledSection {
  title: string;
  summary: string;
  why_it_matters?: string;
  key_points?: string[];
  evidence?: string[];
}

export interface PaperMap {
  main_question?: string;
  paper_type?: string;
  proposed_solution?: string;
  reader_orientation?: string;
  priority_sections?: string[];
  math_relevance?: string;
  results_focus?: string;
  likely_limitations?: string[];
}

export interface ResultsView {
  evaluation_setup?: string;
  results_summary?: string;
  strongest_evidence?: string[];
  caveats?: string[];
  artifact_interpretations?: ArtifactInterpretation[];
}

export interface ArtifactInterpretation {
  artifact_type: 'table' | 'figure' | string;
  label: string;
  section_title?: string;
  what_it_shows: string;
  why_it_matters?: string;
  confidence?: 'high' | 'medium' | 'low' | string;
}

export interface DistilledTerm {
  term: string;
  category: string;
  definition: string;
  mentions: number;
}

export interface FormulaExplanation {
  latex: string;
  plain_explanation: string;
  symbols: Record<string, string>;
  importance: string;
}

export interface FigureCaption {
  label: string;
  caption: string;
  page: number;
  section_title?: string;
  context_before?: string;
  context_after?: string;
  context?: string;
}

export interface ExtractedTable {
  title: string;
  page: number;
  section_title?: string;
  header?: string[];
  row_count?: number;
  column_count?: number;
  context_before?: string;
  context_after?: string;
  context?: string;
  rows: string[][];
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNode {
  id: string;
  label: string;
  category: string;
  definition: string;
  value: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
}
