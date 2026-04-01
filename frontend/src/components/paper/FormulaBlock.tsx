import React from 'react';
import { Box, Chip, Stack, Typography } from '@mui/material';
import { BlockMath } from 'react-katex';
import { FormulaExplanation } from '../../types';

interface FormulaBlockProps {
  formula: FormulaExplanation;
}

export const FormulaBlock: React.FC<FormulaBlockProps> = ({ formula }) => {
  return (
    <Stack spacing={1.25}>
      {formula.latex ? (
        <Box
          sx={{
            overflowX: 'auto',
            bgcolor: 'action.hover',
            borderRadius: 3,
            px: 2,
            py: 1.5,
            '.katex-display': {
              margin: 0,
            },
          }}
        >
          <BlockMath math={formula.latex} errorColor="#cc2f2f" />
        </Box>
      ) : null}
      <Typography variant="body2" color="text.secondary">
        {formula.plain_explanation}
      </Typography>
      {formula.importance ? (
        <Chip label={formula.importance} size="small" variant="outlined" sx={{ alignSelf: 'flex-start' }} />
      ) : null}
    </Stack>
  );
};
