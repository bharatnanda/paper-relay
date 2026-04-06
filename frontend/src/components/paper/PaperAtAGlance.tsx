import React from 'react';
import { Box, Chip, Paper, Stack, Typography } from '@mui/material';
import ArticleRoundedIcon from '@mui/icons-material/ArticleRounded';
import FunctionsRoundedIcon from '@mui/icons-material/FunctionsRounded';
import { PaperMap, PaperAnalysis } from '../../types';
import { CritiqueIndicator } from './CritiqueIndicator';

interface PaperAtAGlanceProps {
  paperMap: PaperMap;
  critique?: NonNullable<PaperAnalysis['summary']>['critique'];
}

export const PaperAtAGlance: React.FC<PaperAtAGlanceProps> = ({ paperMap, critique }) => (
  <Paper sx={{ p: 2, borderRadius: 4, bgcolor: 'rgba(33,84,214,0.03)', border: '1px solid', borderColor: 'rgba(33,84,214,0.1)' }}>
    <Stack spacing={1}>
      <Typography variant="overline" color="text.secondary">At a glance</Typography>
      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
        {paperMap.paper_type && (
          <Chip
            icon={<ArticleRoundedIcon />}
            label={paperMap.paper_type}
            color="primary"
            variant="outlined"
            size="small"
          />
        )}
        {paperMap.math_relevance && (
          <Chip
            icon={<FunctionsRoundedIcon />}
            label={`Math: ${paperMap.math_relevance}`}
            variant="outlined"
            size="small"
          />
        )}
        {paperMap.results_focus && (
          <Chip label={paperMap.results_focus} variant="outlined" size="small" />
        )}
        {critique?.issues?.length ? (
          <Box sx={{ ml: 'auto' }}>
            <CritiqueIndicator critique={critique} />
          </Box>
        ) : null}
      </Stack>
      {paperMap.reader_orientation && (
        <Typography variant="body2" color="text.secondary">{paperMap.reader_orientation}</Typography>
      )}
    </Stack>
  </Paper>
);
