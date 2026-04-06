import React from 'react';
import { Box, Button, Paper, Stack, Typography } from '@mui/material';
import MenuBookRoundedIcon from '@mui/icons-material/MenuBookRounded';
import ChatRoundedIcon from '@mui/icons-material/ChatRounded';

type ReadingLevel = 'general' | 'technical' | 'eli5';
type RightPanel = 'paper' | 'chat' | null;

interface WorkspaceHeaderProps {
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
    <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 6 }}>
      <Stack spacing={2}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} justifyContent="space-between" alignItems={{ md: 'flex-start' }}>
          <Box>
            <Typography variant="overline" color="text.secondary">Analysis workspace</Typography>
            <Typography variant="h3">Distilled paper view</Typography>
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 640, mt: 0.5 }}>
              Read the paper as a guided walkthrough — problem, method, evidence, and verdict.
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
            {/* Reading level segmented control */}
            <Box
              sx={{
                display: 'inline-flex',
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: '10px',
                overflow: 'hidden',
              }}
            >
              {LEVELS.map(({ value, label }) => (
                <Box
                  key={value}
                  component="button"
                  onClick={() => onReadingLevelChange(value)}
                  sx={{
                    px: 1.75,
                    py: 0.75,
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
                  }}
                >
                  {label}
                </Box>
              ))}
            </Box>

            {hasPaperUrl && (
              <Button
                variant={rightPanel === 'paper' ? 'contained' : 'outlined'}
                startIcon={<MenuBookRoundedIcon />}
                onClick={handlePaperToggle}
                size="small"
              >
                {rightPanel === 'paper' ? 'Hide paper' : 'View paper'}
              </Button>
            )}

            <Button
              variant={rightPanel === 'chat' ? 'contained' : 'outlined'}
              startIcon={<ChatRoundedIcon />}
              onClick={handleChatToggle}
              size="small"
            >
              Chat
            </Button>
          </Stack>
        </Stack>
      </Stack>
    </Paper>
  );
};
