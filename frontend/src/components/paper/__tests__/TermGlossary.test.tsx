import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TermGlossary } from '../TermGlossary';
import { DistilledTerm } from '../../../types';

const terms: DistilledTerm[] = [
  { term: 'Attention', category: 'method', definition: 'Weighted focus mechanism.', mentions: 5 },
  { term: 'BLEU', category: 'metric', definition: 'Translation quality metric.', mentions: 3 },
  { term: 'Transformer', category: 'concept', definition: 'Sequence-to-sequence model.', mentions: 8 },
];

test('renders all terms initially', () => {
  render(<TermGlossary terms={terms} />);
  expect(screen.getByText('Attention')).toBeInTheDocument();
  expect(screen.getByText('BLEU')).toBeInTheDocument();
  expect(screen.getByText('Transformer')).toBeInTheDocument();
});

test('filters terms by search query', async () => {
  render(<TermGlossary terms={terms} />);
  const input = screen.getByPlaceholderText(/search/i);
  await userEvent.type(input, 'attention');
  expect(screen.getByText('Attention')).toBeInTheDocument();
  expect(screen.queryByText('BLEU')).not.toBeInTheDocument();
  expect(screen.queryByText('Transformer')).not.toBeInTheDocument();
});

test('matches on definition text too', async () => {
  render(<TermGlossary terms={terms} />);
  const input = screen.getByPlaceholderText(/search/i);
  await userEvent.type(input, 'metric');
  expect(screen.getByText('BLEU')).toBeInTheDocument();
  expect(screen.queryByText('Attention')).not.toBeInTheDocument();
});

test('shows empty message when no match', async () => {
  render(<TermGlossary terms={terms} />);
  const input = screen.getByPlaceholderText(/search/i);
  await userEvent.type(input, 'zzznomatch');
  expect(screen.getByText(/no terms match/i)).toBeInTheDocument();
});
