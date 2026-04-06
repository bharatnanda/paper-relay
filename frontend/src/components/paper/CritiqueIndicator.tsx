import React, { useState } from 'react';
import { Box, Chip, Divider, Drawer, Stack, Typography } from '@mui/material';
import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded';
import { PaperAnalysis } from '../../types';

type Critique = NonNullable<NonNullable<PaperAnalysis['summary']>['critique']>;

interface CritiqueIndicatorProps {
  critique: Critique;
}

const severityColor = (s: string): 'error' | 'warning' | 'default' => {
  if (s === 'high') return 'error';
  if (s === 'medium') return 'warning';
  return 'default';
};

export const CritiqueIndicator: React.FC<CritiqueIndicatorProps> = ({ critique }) => {
  const [open, setOpen] = useState(false);

  if (!critique.issues?.length) return null;

  return (
    <>
      <Chip
        icon={<WarningAmberRoundedIcon />}
        label={`${critique.issues.length} quality note${critique.issues.length !== 1 ? 's' : ''}`}
        color="warning"
        variant="outlined"
        size="small"
        onClick={() => setOpen(true)}
        sx={{ cursor: 'pointer' }}
      />
      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        keepMounted
        PaperProps={{ sx: { width: { xs: '100%', sm: 400 }, p: 3 } }}
      >
        <Typography variant="h6" gutterBottom>Quality notes</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {critique.overall_assessment}
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Stack spacing={2}>
          {critique.issues.map((issue, i) => (
            <Box key={i}>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.75 }}>
                <Chip size="small" label={issue.severity} color={severityColor(issue.severity)} />
                <Chip size="small" label={issue.type.replace(/_/g, ' ')} variant="outlined" />
                <Typography variant="caption" color="text.secondary">{issue.field}</Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">{issue.description}</Typography>
              {issue.suggested_fix && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, pl: 1, borderLeft: '2px solid', borderColor: 'divider' }}>
                  Fix: {issue.suggested_fix}
                </Typography>
              )}
            </Box>
          ))}
        </Stack>
      </Drawer>
    </>
  );
};
