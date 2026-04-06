import React from 'react';
import { Box, Paper, Stack, Typography } from '@mui/material';
import { FormulaBlock } from '../FormulaBlock';
import { FormulaExplanation } from '../../../types';

interface MethodSectionProps {
  content: string;
  formulas: FormulaExplanation[];
}

export const MethodSection: React.FC<MethodSectionProps> = ({ content, formulas }) => {
  const methodFormulas = formulas.filter(
    (f) => f.where_it_appears?.toLowerCase().includes('method')
  );

  return (
    <Paper sx={{ p: 2.5, borderRadius: 4 }}>
      <Stack spacing={1.5}>
        <Stack direction="row" spacing={1.25} alignItems="center">
          <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(128,0,200,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
            ⚙️
          </Box>
          <Typography variant="h6">Method Deep Dive</Typography>
        </Stack>
        <Typography variant="body1" color="text.secondary">{content}</Typography>
        {methodFormulas.length > 0 && (
          <Stack spacing={1.25}>
            {methodFormulas.map((f, i) => (
              <Paper key={f.latex || i} sx={{ p: 2, borderRadius: 3, bgcolor: 'rgba(128,0,200,0.04)', border: '1px solid', borderColor: 'rgba(128,0,200,0.12)' }}>
                <FormulaBlock formula={f} />
              </Paper>
            ))}
          </Stack>
        )}
      </Stack>
    </Paper>
  );
};
