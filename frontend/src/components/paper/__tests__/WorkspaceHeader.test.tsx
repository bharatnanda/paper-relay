import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WorkspaceHeader } from '../WorkspaceHeader';

const defaultProps = {
  readingLevel: 'general' as const,
  onReadingLevelChange: vi.fn(),
  rightPanel: null as 'paper' | 'chat' | null,
  onRightPanelChange: vi.fn(),
  hasPaperUrl: true,
};

test('renders reading level options', () => {
  render(<WorkspaceHeader {...defaultProps} />);
  expect(screen.getByText('General')).toBeInTheDocument();
  expect(screen.getByText('Technical')).toBeInTheDocument();
  expect(screen.getByText('ELI5')).toBeInTheDocument();
});

test('calls onReadingLevelChange when Technical is clicked', async () => {
  const spy = vi.fn();
  render(<WorkspaceHeader {...defaultProps} onReadingLevelChange={spy} />);
  await userEvent.click(screen.getByText('Technical'));
  expect(spy).toHaveBeenCalledWith('technical');
});

test('clicking Chat sets rightPanel to chat', async () => {
  const spy = vi.fn();
  render(<WorkspaceHeader {...defaultProps} onRightPanelChange={spy} />);
  await userEvent.click(screen.getByText('Chat with paper'));
  expect(spy).toHaveBeenCalledWith('chat');
});

test('clicking Chat when chat is active sets rightPanel to null', async () => {
  const spy = vi.fn();
  render(<WorkspaceHeader {...defaultProps} rightPanel="chat" onRightPanelChange={spy} />);
  await userEvent.click(screen.getByText('Hide chat'));
  expect(spy).toHaveBeenCalledWith(null);
});
