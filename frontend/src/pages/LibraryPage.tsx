import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Container, Grid, TextField, InputAdornment, Paper, Stack, Chip } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import LibraryBooksRoundedIcon from '@mui/icons-material/LibraryBooksRounded';
import { useAuth } from '../hooks/useAuth';
import { AppErrorInfo, getApiErrorInfo, papersAPI } from '../services/api';
import { PaperCard } from '../components/library/PaperCard';
import { Paper as PaperItem } from '../types';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorBanner } from '../components/common/ErrorBanner';

export const LibraryPage: React.FC = () => {
  const { user } = useAuth();
  const [papers, setPapers] = useState<PaperItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppErrorInfo | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }

    papersAPI.listPapers(user.token)
      .then((data) => {
        setPapers(data);
        setLoading(false);
      })
      .catch((err: any) => {
        setError(getApiErrorInfo(err, 'Failed to load your library.'));
        setLoading(false);
        console.error('Library fetch error:', err);
      });
  }, [user, navigate]);

  if (loading) return <LoadingSpinner message="Loading your library..." />;
  if (error) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4 }}>
          <ErrorBanner
            title={error.title}
            message={error.message}
            hint={error.hint}
            onClose={() => setError(null)}
          />
        </Box>
      </Container>
    );
  }

  const filteredPapers = papers.filter(paper =>
    (paper.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (paper.arxiv_id || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 6, mb: 3 }}>
          <Stack spacing={2}>
            <Chip
              icon={<LibraryBooksRoundedIcon />}
              label={`${papers.length} saved ${papers.length === 1 ? 'paper' : 'papers'}`}
              color="primary"
              variant="outlined"
              sx={{ alignSelf: 'flex-start' }}
            />
            <Typography variant="h3">Your research library</Typography>
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 720 }}>
              Reopen earlier analyses, filter by title or arXiv ID, and jump back into the distilled view without rerunning the pipeline.
            </Typography>
            <TextField
              fullWidth
              placeholder="Search by title or arXiv ID"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
              sx={{ maxWidth: 640 }}
            />
          </Stack>
        </Paper>

        {filteredPapers.length === 0 ? (
          <Paper sx={{ textAlign: 'center', py: 8, px: 3, borderRadius: 6 }}>
            <Typography variant="h5" color="text.primary">
              {searchQuery ? 'No papers match your search' : 'No papers yet'}
            </Typography>
            {!searchQuery && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Analyze your first paper to get started!
              </Typography>
            )}
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {filteredPapers.map((paper) => (
              <Grid item xs={12} sm={6} md={4} key={paper.id}>
                <PaperCard
                  id={paper.id}
                  title={paper.title}
                  authors={paper.authors}
                  arxiv_id={paper.arxiv_id}
                  created_at={paper.created_at}
                  token={user?.token || ''}
                />
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </Container>
  );
};
