import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Container, Paper, Alert, Stack, Chip } from '@mui/material';
import TravelExploreRoundedIcon from '@mui/icons-material/TravelExploreRounded';
import { AppErrorInfo, getApiErrorInfo, shareAPI } from '../services/api';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { ArtifactInterpretation } from '../types';

export const SharedPaperPage: React.FC = () => {
  const { shareToken } = useParams<{ shareToken: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppErrorInfo | null>(null);

  useEffect(() => {
    let active = true;

    const fetchSharedPaper = async () => {
      try {
        const payload = await shareAPI.getSharedPaper(shareToken || '');
        if (!active) return;
        setData(payload);
      } catch (err: any) {
        if (!active) return;
        setError(getApiErrorInfo(err, 'Failed to load the shared paper.'));
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchSharedPaper();

    return () => {
      active = false;
    };
  }, [shareToken]);

  if (loading) return <Container maxWidth="lg"><Box sx={{ mt: 8 }}><Paper sx={{ p: 4, borderRadius: 6, textAlign: 'center' }}><Typography>Loading shared paper...</Typography></Paper></Box></Container>;
  if (error || !data) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 8 }}>
          <ErrorBanner
            title={error?.title || 'Share link unavailable'}
            message={error?.message || 'This share link is invalid or expired.'}
            hint={error?.hint}
          />
        </Box>
      </Container>
    );
  }

  const artifactInterpretations = data.analysis.summary?.artifact_interpretations
    || data.analysis.summary?.results_view?.artifact_interpretations
    || [
      ...(data.analysis.summary?.table_interpretations || []),
      ...(data.analysis.summary?.figure_interpretations || []),
    ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'grid', gap: 3 }}>
        <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 6 }}>
          <Stack spacing={2}>
            <Chip icon={<TravelExploreRoundedIcon />} label="Shared analysis" color="primary" variant="outlined" sx={{ alignSelf: 'flex-start' }} />
            <Typography variant="h3">{data.paper.title}</Typography>
            <Typography variant="body1" color="text.secondary">{data.paper.authors?.join(', ')}</Typography>
            <Alert severity="info">You&apos;re viewing a public share link. <a href="/">Create your own analysis</a>.</Alert>
          </Stack>
        </Paper>
        <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 6 }}>
          {data.analysis.summary && (
            <>
              <Typography variant="h5" gutterBottom>Quick summary</Typography>
              <Typography paragraph color="text.secondary">{data.analysis.summary.quick}</Typography>
              {data.analysis.summary.problem_and_motivation ? (
                <>
                  <Typography variant="h6" gutterBottom>Problem and motivation</Typography>
                  <Typography paragraph color="text.secondary">{data.analysis.summary.problem_and_motivation}</Typography>
                </>
              ) : null}
              <Typography variant="h6" gutterBottom>Key contributions</Typography>
              <Stack spacing={1.25} sx={{ mb: 3 }}>
                {data.analysis.summary.key_contributions?.map((c: string, i: number) => (
                  <Paper key={c.substring(0, 50) + i} sx={{ p: 2.25, borderRadius: 4 }}>
                    <Typography>{c}</Typography>
                  </Paper>
                ))}
              </Stack>
              {data.analysis.summary.guided_walkthrough ? (
                <>
                  <Typography variant="h6" gutterBottom>Guided walkthrough</Typography>
                  <Typography paragraph color="text.secondary">{data.analysis.summary.guided_walkthrough}</Typography>
                </>
              ) : null}
              {artifactInterpretations?.length ? (
                <>
                  <Typography variant="h6" gutterBottom>Interpreted evidence</Typography>
                  <Stack spacing={1.25} sx={{ mb: 3 }}>
                    {artifactInterpretations.map((item: ArtifactInterpretation, index: number) => (
                      <Paper key={`${item.label}-${index}`} sx={{ p: 2.25, borderRadius: 4 }}>
                        <Stack spacing={0.75}>
                          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                            <Typography fontWeight={700}>{item.label}</Typography>
                            <Chip
                              size="small"
                              label={item.artifact_type === 'table' ? 'Table' : item.artifact_type === 'figure' ? 'Figure' : item.artifact_type}
                              variant="outlined"
                            />
                          </Stack>
                          <Typography variant="body2" color="text.secondary">{item.what_it_shows}</Typography>
                          {item.why_it_matters ? (
                            <Typography variant="body2">
                              <strong>Why it matters:</strong> {item.why_it_matters}
                            </Typography>
                          ) : null}
                        </Stack>
                      </Paper>
                    ))}
                  </Stack>
                </>
              ) : null}
              <Typography variant="h6" gutterBottom>ELI5</Typography>
              <Typography paragraph color="text.secondary">{data.analysis.summary.eli5}</Typography>
            </>
          )}
        </Paper>
      </Box>
    </Container>
  );
};
