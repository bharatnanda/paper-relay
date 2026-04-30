import React from 'react';
import { Box, Button, Chip, Paper, Stack, Typography } from '@mui/material';
import MenuBookRoundedIcon from '@mui/icons-material/MenuBookRounded';
import ChatRoundedIcon from '@mui/icons-material/ChatRounded';

type ReadingLevel = 'general' | 'technical' | 'eli5';
type RightPanel = 'paper' | 'chat' | null;

interface WorkspaceHeaderProps {
  title?: string;
  authors?: string[];
  arxivId?: string;
  readingLevel: ReadingLevel;
  onReadingLevelChange: (level: ReadingLevel) => void;
  rightPanel: RightPanel;
  onRightPanelChange: (panel: RightPanel) => void;
  hasPaperUrl: boolean;
}

const LEVELS: { value: ReadingLevel; label: string }[] = [
  { value: 'general', label: 'General' },
  { value: 'technical', label: 'Technical' },
  { value: 'eli5', label: 'ELI5' },
];

export const WorkspaceHeader: React.FC<WorkspaceHeaderProps> = ({
  title,
  authors = [],
  arxivId,
  readingLevel,
  onReadingLevelChange,
  rightPanel,
  onRightPanelChange,
  hasPaperUrl,
}) => {
  const handlePaperToggle = () =>
    onRightPanelChange(rightPanel === 'paper' ? null : 'paper');

  const handleChatToggle = () =>
    onRightPanelChange(rightPanel === 'chat' ? null : 'chat');

  return (
    <Paper
      sx={{
        p: { xs: 2.5, md: 3.5 },
        borderRadius: 6,
        overflow: 'hidden',
        backgroundImage: 'linear-gradient(180deg, rgba(33,84,214,0.05) 0%, rgba(255,255,255,0) 72%)',
      }}
    >
      <Stack spacing={2.25}>
        <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2.5} justifyContent="space-between" alignItems={{ xl: 'flex-start' }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="overline" color="text.secondary">Analysis workspace</Typography>
            <Typography variant="h3" sx={{ maxWidth: 780 }}>
              {title || 'Distilled paper view'}
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 640, mt: 0.5 }}>
              Read the paper as a guided walkthrough — problem, method, evidence, and verdict.
            </Typography>
            {(authors.length > 0 || arxivId) && (
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ mt: 1.5 }}>
                {authors.length > 0 && (
                  <Chip
                    size="small"
                    label={authors.length > 3 ? `${authors.slice(0, 3).join(', ')} +${authors.length - 3}` : authors.join(', ')}
                    variant="outlined"
                  />
                )}
                {arxivId && <Chip size="small" label={`arXiv ${arxivId}`} variant="outlined" />}
              </Stack>
            )}
          </Box>
          <Stack spacing={1.25} sx={{ width: { xs: '100%', xl: 'auto' }, minWidth: 0 }}>
            {/* Reading level segmented control */}
            <Box
              sx={{
                display: 'inline-flex',
                alignSelf: { xs: 'stretch', xl: 'flex-end' },
                width: { xs: '100%', sm: 'auto' },
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 3,
                overflow: 'hidden',
                bgcolor: 'background.paper',
              }}
            >
              {LEVELS.map(({ value, label }) => (
                <Box
                  key={value}
                  component="button"
                  type="button"
                  onClick={() => onReadingLevelChange(value)}
                  aria-pressed={readingLevel === value}
                  sx={{
                    flex: 1,
                    px: 1.75,
                    py: 1,
                    border: 0,
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                    fontSize: 13,
                    fontWeight: readingLevel === value ? 700 : 500,
                    bgcolor: readingLevel === value ? 'primary.main' : 'transparent',
                    color: readingLevel === value ? 'primary.contrastText' : 'text.secondary',
                    transition: 'background 150ms, color 150ms',
                    '&:hover': {
                      bgcolor: readingLevel === value ? 'primary.main' : 'action.hover',
                    },
                    '&:focus-visible': {
                      outline: '2px solid',
                      outlineColor: 'primary.main',
                      outlineOffset: -2,
                    },
                  }}
                >
                  {label}
                </Box>
              ))}
            </Box>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ width: { xs: '100%', xl: 'auto' } }}>
              {hasPaperUrl && (
                <Button
                  variant={rightPanel === 'paper' ? 'contained' : 'outlined'}
                  startIcon={<MenuBookRoundedIcon />}
                  onClick={handlePaperToggle}
                  size="small"
                  sx={{ flex: { sm: 1 } }}
                >
                  {rightPanel === 'paper' ? 'Hide paper' : 'View paper'}
                </Button>
              )}

              <Button
                variant={rightPanel === 'chat' ? 'contained' : 'outlined'}
                startIcon={<ChatRoundedIcon />}
                onClick={handleChatToggle}
                size="small"
                sx={{ flex: { sm: 1 } }}
              >
                {rightPanel === 'chat' ? 'Hide chat' : 'Chat with paper'}
              </Button>
            </Stack>
          </Stack>
        </Stack>
      </Stack>
    </Paper>
  );
};
