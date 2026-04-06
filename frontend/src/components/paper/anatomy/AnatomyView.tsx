import React from 'react';
import { Stack } from '@mui/material';
import { PaperAnalysis, FormulaExplanation } from '../../../types';
import { ProblemSection } from './ProblemSection';
import { PriorArtSection } from './PriorArtSection';
import { IdeaSection } from './IdeaSection';
import { MethodSection } from './MethodSection';
import { EvidenceSection } from './EvidenceSection';
import { VerdictSection } from './VerdictSection';
import { TakeawaysSection } from './TakeawaysSection';

interface AnatomyViewProps {
  summary: NonNullable<PaperAnalysis['summary']>;
}

export const AnatomyView: React.FC<AnatomyViewProps> = ({ summary }) => {
  const formulas: FormulaExplanation[] = summary.formula_explanations ?? [];

  const artifactInterpretations =
    summary.artifact_interpretations ??
    summary.results_view?.artifact_interpretations ??
    [
      ...(summary.table_interpretations ?? []),
      ...(summary.figure_interpretations ?? []),
    ];

  return (
    <Stack spacing={2}>
      {summary.problem_and_motivation && (
        <ProblemSection content={summary.problem_and_motivation} />
      )}
      {summary.prior_work_and_gap && (
        <PriorArtSection content={summary.prior_work_and_gap} />
      )}
      {summary.core_intuition && (
        <IdeaSection content={summary.core_intuition} />
      )}
      {summary.method_deep_dive && (
        <MethodSection content={summary.method_deep_dive} formulas={formulas} />
      )}
      {(summary.results_and_evidence || artifactInterpretations.length > 0) && (
        <EvidenceSection
          content={summary.results_and_evidence}
          resultsView={summary.results_view}
          artifactInterpretations={artifactInterpretations}
          figureCaptions={summary.figure_captions}
          tables={summary.tables}
        />
      )}
      {summary.authors_claims && summary.evidence_assessment && (
        <VerdictSection
          authorsClaim={summary.authors_claims}
          evidenceAssessment={summary.evidence_assessment}
        />
      )}
      {summary.reader_takeaways?.length ? (
        <TakeawaysSection items={summary.reader_takeaways} />
      ) : null}
    </Stack>
  );
};
