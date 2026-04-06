import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CritiqueIndicator } from '../CritiqueIndicator';

const critique = {
  needs_revision: true,
  overall_assessment: 'Some issues found.',
  issues: [
    { field: 'results', severity: 'high' as const, type: 'overclaim' as const, description: 'Overclaims generalization.', suggested_fix: 'Qualify the claim.' },
    { field: 'method', severity: 'low' as const, type: 'vague_method' as const, description: 'Method is underspecified.', suggested_fix: 'Add detail.' },
  ],
};

test('renders chip with issue count', () => {
  render(<CritiqueIndicator critique={critique} />);
  expect(screen.getByText(/2 quality notes/i)).toBeInTheDocument();
});

test('renders nothing when no issues', () => {
  const { container } = render(<CritiqueIndicator critique={{ ...critique, issues: [] }} />);
  expect(container.firstChild).toBeNull();
});

test('opens drawer with issue list on chip click', async () => {
  render(<CritiqueIndicator critique={critique} />);
  await userEvent.click(screen.getByText(/2 quality notes/i));
  expect(screen.getByText('Overclaims generalization.')).toBeInTheDocument();
  expect(screen.getByText('Method is underspecified.')).toBeInTheDocument();
});
