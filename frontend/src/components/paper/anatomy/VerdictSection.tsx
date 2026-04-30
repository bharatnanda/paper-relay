import React from 'react';
import { Box, Grid, Paper, Stack, Typography } from '@mui/material';

interface VerdictSectionProps {
  verdict?: string;
  authorsClaim?: string;
  evidenceAssessment?: string;
}

export const VerdictSection: React.FC<VerdictSectionProps> = ({ verdict, authorsClaim, evidenceAssessment }) => (
  <Paper sx={{ p: 2.5, borderRadius: 4 }}>
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(33,84,214,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
          ⚖️
        </Box>
        <Typography variant="h6">Verdict</Typography>
      </Stack>
      {verdict && (
        <Paper
          sx={{
            p: 2.25,
            borderRadius: 3,
            bgcolor: 'rgba(33,84,214,0.05)',
            border: '1px solid',
            borderColor: 'rgba(33,84,214,0.16)',
          }}
        >
          <Typography variant="overline" color="primary" display="block" sx={{ mb: 0.75 }}>
            Bottom line
          </Typography>
          <Typography variant="body1" color="text.secondary">{verdict}</Typography>
        </Paper>
      )}

      {(authorsClaim || evidenceAssessment) && (
        <Grid container spacing={1.5}>
          {authorsClaim && (
            <Grid item xs={12} sm={6}>
              <Paper
                sx={{
                  p: 2,
                  borderRadius: 3,
                  bgcolor: 'rgba(33,84,214,0.04)',
                  border: '1px solid',
                  borderColor: 'rgba(33,84,214,0.14)',
                  height: '100%',
                }}
              >
                <Typography variant="overline" color="primary" display="block" sx={{ mb: 0.75 }}>
                  Authors claim
                </Typography>
                <Typography variant="body2" color="text.secondary">{authorsClaim}</Typography>
              </Paper>
            </Grid>
          )}
          {evidenceAssessment && (
            <Grid item xs={12} sm={6}>
              <Paper
                sx={{
                  p: 2,
                  borderRadius: 3,
                  bgcolor: 'rgba(15,143,121,0.04)',
                  border: '1px solid',
                  borderColor: 'rgba(15,143,121,0.14)',
                  height: '100%',
                }}
              >
                <Typography variant="overline" color="secondary" display="block" sx={{ mb: 0.75 }}>
                  Evidence shows
                </Typography>
                <Typography variant="body2" color="text.secondary">{evidenceAssessment}</Typography>
              </Paper>
            </Grid>
          )}
        </Grid>
      )}
    </Stack>
  </Paper>
);
