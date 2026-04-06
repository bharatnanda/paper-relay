import React from 'react';
import { Box, Paper, Stack, Typography } from '@mui/material';

interface ProblemSectionProps {
  content: string;
}

export const ProblemSection: React.FC<ProblemSectionProps> = ({ content }) => (
  <Paper sx={{ p: 2.5, borderRadius: 4 }}>
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(33,84,214,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
          🎯
        </Box>
        <Typography variant="h6">Problem &amp; Motivation</Typography>
      </Stack>
      <Typography variant="body1" color="text.secondary">{content}</Typography>
    </Stack>
  </Paper>
);
