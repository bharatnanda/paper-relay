import React from 'react';
import { Box, Paper, Stack, Typography } from '@mui/material';

interface TakeawaysSectionProps {
  items: string[];
}

export const TakeawaysSection: React.FC<TakeawaysSectionProps> = ({ items }) => (
  <Paper sx={{ p: 2.5, borderRadius: 4 }}>
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(202,107,20,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
          ✅
        </Box>
        <Typography variant="h6">Takeaways</Typography>
      </Stack>
      <Stack spacing={1}>
        {items.map((item, i) => (
          <Box
            key={i}
            sx={{
              pl: 1.5,
              py: 0.75,
              borderLeft: '3px solid',
              borderColor: 'warning.main',
              borderRadius: '0 6px 6px 0',
              bgcolor: 'action.hover',
            }}
          >
            <Typography variant="body2" color="text.secondary">{item}</Typography>
          </Box>
        ))}
      </Stack>
    </Stack>
  </Paper>
);
