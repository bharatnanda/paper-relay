import React from 'react';
import { Box, Chip, Paper, Stack, Typography } from '@mui/material';
import { PaperAnalysis, FormulaExplanation } from '../../../types';
import { ProblemSection } from './ProblemSection';
import { PriorArtSection } from './PriorArtSection';
import { IdeaSection } from './IdeaSection';
import { MethodSection } from './MethodSection';
import { EvaluationSection } from './EvaluationSection';
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

  const sections = [
    summary.problem_and_motivation ? {
      id: 'problem',
      label: 'Problem',
      node: <ProblemSection content={summary.problem_and_motivation} />,
    } : null,
    summary.prior_work_and_gap ? {
      id: 'prior-work',
      label: 'Prior Work',
      node: <PriorArtSection content={summary.prior_work_and_gap} />,
    } : null,
    summary.core_intuition ? {
      id: 'intuition',
      label: 'Core Idea',
      node: <IdeaSection content={summary.core_intuition} />,
    } : null,
    summary.method_deep_dive ? {
      id: 'method',
      label: 'Method',
      node: <MethodSection content={summary.method_deep_dive} formulas={formulas} />,
    } : null,
    summary.results_view?.evaluation_setup ? {
      id: 'evaluation',
      label: 'Evaluation',
      node: <EvaluationSection content={summary.results_view.evaluation_setup} />,
    } : null,
    (summary.results_and_evidence || artifactInterpretations.length > 0) ? {
      id: 'evidence',
      label: 'Evidence',
      node: (
        <EvidenceSection
          content={summary.results_and_evidence}
          artifactInterpretations={artifactInterpretations}
          figureCaptions={summary.figure_captions}
          tables={summary.tables}
        />
      ),
    } : null,
    (summary.bottom_line_verdict || summary.authors_claims || summary.evidence_assessment) ? {
      id: 'verdict',
      label: 'Verdict',
      node: (
        <VerdictSection
          verdict={summary.bottom_line_verdict}
          authorsClaim={summary.authors_claims}
          evidenceAssessment={summary.evidence_assessment}
        />
      ),
    } : null,
    summary.reader_takeaways?.length ? {
      id: 'takeaways',
      label: 'Takeaways',
      node: <TakeawaysSection items={summary.reader_takeaways} />,
    } : null,
  ].filter(Boolean) as Array<{ id: string; label: string; node: React.ReactNode }>;

  return (
    <Stack spacing={2}>
      {sections.length > 1 && (
        <Paper sx={{ p: 1.5, borderRadius: 4, position: 'sticky', top: 16, zIndex: 2, backdropFilter: 'blur(14px)' }}>
          <Stack spacing={1}>
            <Typography variant="overline" color="text.secondary">
              Jump To Section
            </Typography>
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              {sections.map((section) => (
                <Chip
                  key={section.id}
                  label={section.label}
                  clickable
                  onClick={() => document.getElementById(`anatomy-${section.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                  variant="outlined"
                  size="small"
                />
              ))}
            </Stack>
          </Stack>
        </Paper>
      )}

      {sections.map((section) => (
        <Box key={section.id} id={`anatomy-${section.id}`} sx={{ scrollMarginTop: 96 }}>
          {section.node}
        </Box>
      ))}
    </Stack>
  );
};
