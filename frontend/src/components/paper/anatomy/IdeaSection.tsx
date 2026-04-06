import React from 'react';
import { Box, Paper, Stack, Typography } from '@mui/material';

interface IdeaSectionProps {
  content: string;
}

export const IdeaSection: React.FC<IdeaSectionProps> = ({ content }) => (
  <Paper sx={{ p: 2.5, borderRadius: 4 }}>
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(202,107,20,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
          💡
        </Box>
        <Typography variant="h6">Core Intuition</Typography>
      </Stack>
      <Typography variant="body1" color="text.secondary">{content}</Typography>
    </Stack>
  </Paper>
);
