import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { alpha } from '@mui/material/styles';
import {
  Box,
  TextField,
  Button,
  Typography,
  Container,
  Stack,
  Paper,
  Chip,
} from '@mui/material';
import BoltRoundedIcon from '@mui/icons-material/BoltRounded';
import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import HubRoundedIcon from '@mui/icons-material/HubRounded';
import MenuBookRoundedIcon from '@mui/icons-material/MenuBookRounded';
import LoginRoundedIcon from '@mui/icons-material/LoginRounded';
import { useAuth } from '../hooks/useAuth';
import { AppErrorInfo, getApiErrorInfo, papersAPI } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorBanner } from '../components/common/ErrorBanner';

const ARXIV_URL_PATTERN = /^https?:\/\/(www\.)?arxiv\.org\/(abs|pdf)\/\d{4}\.\d{4,5}(\.pdf)?$/;

const validateArxivUrl = (url: string): boolean => {
  return ARXIV_URL_PATTERN.test(url);
};

export const HomePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppErrorInfo | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    const nextUrl = searchParams.get('arxiv_url');
    if (nextUrl) {
      setUrl(nextUrl);
      sessionStorage.setItem('pending-arxiv-url', nextUrl);
      return;
    }

    const pendingUrl = sessionStorage.getItem('pending-arxiv-url');
    if (pendingUrl) {
      setUrl(pendingUrl);
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateArxivUrl(url)) {
      setError({
        title: 'Invalid arXiv URL',
        message: 'Please enter a valid arXiv URL.',
        hint: 'Use a standard arXiv abstract or PDF link, such as https://arxiv.org/abs/2301.12345.',
      });
      return;
    }

    if (!user) {
      sessionStorage.setItem('pending-arxiv-url', url);
      navigate('/login');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await papersAPI.analyze(url, user.token);
      sessionStorage.removeItem('pending-arxiv-url');
      navigate(`/paper/${result.paper_id}`);
    } catch (err: any) {
      setError(getApiErrorInfo(err, 'Failed to analyze the paper.'));
      console.error('Paper analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ display: 'grid', gap: 4 }}>
        <Paper
          sx={{
            position: 'relative',
            overflow: 'hidden',
            p: { xs: 3, md: 5 },
            borderRadius: 7,
            background: (theme) =>
              `linear-gradient(145deg, ${alpha(theme.palette.primary.main, 0.14)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
          }}
        >
          <Box
            sx={{
              position: 'absolute',
              inset: 'auto -80px -110px auto',
              width: 240,
              height: 240,
              borderRadius: '50%',
              bgcolor: (theme) => alpha(theme.palette.primary.main, 0.12),
              filter: 'blur(6px)',
            }}
          />
          <Stack spacing={2.5} sx={{ position: 'relative' }}>
            <Chip
              icon={<BoltRoundedIcon />}
              label="Research distillation"
              color="primary"
              variant="outlined"
              sx={{ alignSelf: 'flex-start' }}
            />
            <Typography variant="h2" sx={{ maxWidth: 680 }}>
              Turn dense arXiv papers into something you can actually use.
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 720, fontWeight: 500 }}>
              PaperRelay pulls out the main idea, explains the math, surfaces important terms, and builds a lightweight concept graph you can scan fast.
            </Typography>

            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
              <Paper sx={{ p: 2, borderRadius: 5, bgcolor: (theme) => alpha(theme.palette.background.paper, 0.78) }}>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                  <TextField
                    fullWidth
                    label="Paste an arXiv URL"
                    placeholder="https://arxiv.org/abs/2301.12345"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={loading}
                  />
                  <Button type="submit" variant="contained" size="large" disabled={loading || !url} sx={{ minWidth: { md: 180 } }}>
                    Analyze
                  </Button>
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5 }}>
                  Works with standard arXiv abstract or PDF URLs.
                </Typography>
              </Paper>
            </Box>
          </Stack>
        </Paper>

        {loading && <LoadingSpinner message="Fetching metadata, downloading the paper, and starting analysis..." />}
        {error && (
          <ErrorBanner
            title={error.title}
            message={error.message}
            hint={error.hint}
            onClose={() => setError(null)}
          />
        )}

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          {[
            {
              icon: <PsychologyRoundedIcon color="primary" />,
              title: 'Explain the difficult parts',
              body: 'Get a fast summary, a plain-English version, and a more technical breakdown grounded in the paper.',
            },
            {
              icon: <HubRoundedIcon color="secondary" />,
              title: 'See the concept map',
              body: 'Important terms and relationships are surfaced visually so you can spot the structure of the paper.',
            },
            {
              icon: <MenuBookRoundedIcon color="warning" />,
              title: 'Keep a reusable library',
              body: 'Save papers, reopen them later, export the result, or create a share link for collaborators.',
            },
          ].map((item) => (
            <Paper key={item.title} sx={{ flex: 1, p: 3, borderRadius: 5 }}>
              <Stack spacing={1.5}>
                {item.icon}
                <Typography variant="h6">{item.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {item.body}
                </Typography>
              </Stack>
            </Paper>
          ))}
        </Stack>

        {!user && (
          <Paper sx={{ p: 3, borderRadius: 5 }}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ xs: 'flex-start', sm: 'center' }} justifyContent="space-between">
              <Box>
                <Typography variant="h6">Sign in to keep your paper library</Typography>
                <Typography variant="body2" color="text.secondary">
                  Magic-link sign-in keeps the flow light while preserving your saved analyses.
                </Typography>
              </Box>
              <Button href="/login" variant="outlined" startIcon={<LoginRoundedIcon />}>
                Sign in
              </Button>
            </Stack>
          </Paper>
        )}
      </Box>
    </Container>
  );
};
