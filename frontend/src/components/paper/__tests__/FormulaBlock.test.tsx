// frontend/src/components/paper/__tests__/FormulaBlock.test.tsx
import { render, screen } from '@testing-library/react';
import { FormulaBlock } from '../FormulaBlock';

const baseFormula = {
  latex: 'E = mc^2',
  plain_explanation: 'Energy equals mass times speed of light squared.',
  symbols: { E: 'energy', m: 'mass', c: 'speed of light' },
  importance: 'Foundational',
};

test('renders plain_explanation', () => {
  render(<FormulaBlock formula={baseFormula} />);
  expect(screen.getByText('Energy equals mass times speed of light squared.')).toBeInTheDocument();
});

test('renders intuition when provided', () => {
  render(<FormulaBlock formula={{ ...baseFormula, intuition: 'Mass is frozen energy.' }} />);
  expect(screen.getByText('Mass is frozen energy.')).toBeInTheDocument();
});

test('renders each prerequisite as a chip', () => {
  render(<FormulaBlock formula={{ ...baseFormula, prerequisites: ['Special relativity', 'Classical mechanics'] }} />);
  expect(screen.getByText('Special relativity')).toBeInTheDocument();
  expect(screen.getByText('Classical mechanics')).toBeInTheDocument();
});

test('renders where_it_appears label when provided', () => {
  render(<FormulaBlock formula={{ ...baseFormula, where_it_appears: 'Section 3 — Method' }} />);
  expect(screen.getByText('Section 3 — Method')).toBeInTheDocument();
});

test('does not render intuition section when absent', () => {
  render(<FormulaBlock formula={baseFormula} />);
  expect(screen.queryByTestId('formula-intuition')).not.toBeInTheDocument();
});
