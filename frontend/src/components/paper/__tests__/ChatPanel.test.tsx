import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { ChatPanel } from '../ChatPanel';

vi.mock('../../../services/api', () => ({
  papersAPI: {
    chat: vi.fn().mockResolvedValue({ reply: 'The key equation balances reconstruction and KL divergence.' }),
  },
}));

import { papersAPI } from '../../../services/api';

test('renders starter prompts when no messages', () => {
  render(<ChatPanel paperId="p1" token="tok" onClose={vi.fn()} />);
  expect(screen.getByText(/explain the key equation/i)).toBeInTheDocument();
  expect(screen.getByText(/does the evaluation actually prove/i)).toBeInTheDocument();
});

test('sends message and shows reply', async () => {
  render(<ChatPanel paperId="p1" token="tok" onClose={vi.fn()} />);
  const input = screen.getByPlaceholderText(/ask/i);
  await userEvent.type(input, 'What is the main idea?');
  await userEvent.click(screen.getByRole('button', { name: /send/i }));

  expect(screen.getByText('What is the main idea?')).toBeInTheDocument();
  await waitFor(() =>
    expect(screen.getByText('The key equation balances reconstruction and KL divergence.')).toBeInTheDocument()
  );
});

test('clears input after send', async () => {
  render(<ChatPanel paperId="p1" token="tok" onClose={vi.fn()} />);
  const input = screen.getByPlaceholderText(/ask/i);
  await userEvent.type(input, 'Hello');
  await userEvent.click(screen.getByRole('button', { name: /send/i }));
  expect(input).toHaveValue('');
});

test('clicking starter prompt sends it', async () => {
  render(<ChatPanel paperId="p1" token="tok" onClose={vi.fn()} />);
  const prompt = screen.getByText(/explain the key equation/i);
  await userEvent.click(prompt);
  await waitFor(() =>
    expect(papersAPI.chat).toHaveBeenCalledWith(
      'p1',
      expect.arrayContaining([expect.objectContaining({ content: expect.stringContaining('key equation') })]),
      'tok'
    )
  );
});

test('calls onClose when close button clicked', async () => {
  const onClose = vi.fn();
  render(<ChatPanel paperId="p1" token="tok" onClose={onClose} />);
  await userEvent.click(screen.getByRole('button', { name: /close/i }));
  expect(onClose).toHaveBeenCalled();
});
