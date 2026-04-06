// frontend/src/components/paper/FormulaBlock.tsx
import React from 'react';
import { Box, Chip, Stack, Typography } from '@mui/material';
import { BlockMath } from 'react-katex';
import { FormulaExplanation } from '../../types';

interface FormulaBlockProps {
  formula: FormulaExplanation;
}

export const FormulaBlock: React.FC<FormulaBlockProps> = ({ formula }) => (
  <Stack spacing={1.25}>
    {formula.intuition ? (
      <Typography variant="body2" color="text.secondary" fontStyle="italic" data-testid="formula-intuition">
        {formula.intuition}
      </Typography>
    ) : null}
    {formula.latex ? (
      <Box
        sx={{
          overflowX: 'auto',
          bgcolor: 'action.hover',
          borderRadius: 3,
          px: 2,
          py: 1.5,
          '.katex-display': { margin: 0 },
        }}
      >
        <BlockMath math={formula.latex} errorColor="#cc2f2f" />
      </Box>
    ) : null}
    <Typography variant="body2" color="text.secondary">
      {formula.plain_explanation}
    </Typography>
    {formula.prerequisites?.length ? (
      <Stack direction="row" spacing={0.75} flexWrap="wrap">
        {formula.prerequisites.map((p) => (
          <Chip key={p} label={p} size="small" variant="outlined" sx={{ mb: 0.5 }} />
        ))}
      </Stack>
    ) : null}
    {formula.where_it_appears ? (
      <Typography variant="caption" color="text.secondary">
        {formula.where_it_appears}
      </Typography>
    ) : null}
    {formula.importance ? (
      <Chip label={formula.importance} size="small" variant="outlined" sx={{ alignSelf: 'flex-start' }} />
    ) : null}
  </Stack>
);
