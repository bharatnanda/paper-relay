import { render, screen } from '@testing-library/react';
import { AnatomyView } from '../anatomy/AnatomyView';

const summary = {
  quick: 'Quick summary',
  eli5: 'ELI5 summary',
  technical: 'Technical summary',
  key_contributions: [],
  formula_explanations: [],
  figure_captions: [],
  tables: [],
  problem_and_motivation: 'Why this paper exists',
  prior_work_and_gap: 'What came before and what was missing',
  core_intuition: 'The key idea',
  method_deep_dive: 'How the method works',
  results_and_evidence: 'What the experiments show',
  bottom_line_verdict: 'Promising contribution with evidence that looks credible inside the reported setup.',
  authors_claims: 'What the paper claims',
  evidence_assessment: 'What the evidence really supports',
  reader_takeaways: ['Takeaway'],
  results_view: {
    evaluation_setup: 'Compared against strong baselines on benchmark tasks.',
    results_summary: 'Strong results',
    strongest_evidence: [],
    caveats: [],
    artifact_interpretations: [],
  },
  artifact_interpretations: [],
  table_interpretations: [],
  figure_interpretations: [],
  terms: [],
};

test('renders evaluation setup as its own anatomy section', () => {
  render(<AnatomyView summary={summary} />);

  expect(screen.getByText('Evaluation Setup')).toBeInTheDocument();
  expect(screen.getByText('Compared against strong baselines on benchmark tasks.')).toBeInTheDocument();
  expect(screen.getByText('Evidence & Results')).toBeInTheDocument();
  expect(screen.getByText('Bottom line')).toBeInTheDocument();
  expect(screen.getByText('Promising contribution with evidence that looks credible inside the reported setup.')).toBeInTheDocument();
  expect(screen.getByText('Jump To Section')).toBeInTheDocument();
});
