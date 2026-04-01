import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { alpha } from '@mui/material/styles';
import {
  Box,
  TextField,
  Button,
  Typography,
  Container,
  Alert,
  Paper,
  CircularProgress,
  Stack,
  Chip,
} from '@mui/material';
import MarkEmailReadRoundedIcon from '@mui/icons-material/MarkEmailReadRounded';
import MailOutlineRoundedIcon from '@mui/icons-material/MailOutlineRounded';
import VerifiedRoundedIcon from '@mui/icons-material/VerifiedRounded';
import { AppErrorInfo, authAPI, getApiErrorInfo } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { ErrorBanner } from '../components/common/ErrorBanner';

export const LoginPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppErrorInfo | null>(null);
  const [success, setSuccess] = useState('');
  const [verifying, setVerifying] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();
  const tokenFromUrl = searchParams.get('token');

  useEffect(() => {
    if (!tokenFromUrl) {
      return;
    }

    let active = true;

    const verifyToken = async () => {
      setVerifying(true);
      setError(null);
      try {
        const user = await authAPI.verifyMagicLink(tokenFromUrl);
        if (!active) return;
        login(user);
        navigate('/');
      } catch (err: any) {
        if (!active) return;
        setError(getApiErrorInfo(err, 'Magic link is invalid or expired.'));
      } finally {
        if (active) {
          setVerifying(false);
        }
      }
    };

    verifyToken();

    return () => {
      active = false;
    };
  }, [tokenFromUrl, login, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess('');

    try {
      await authAPI.requestMagicLink(email);
      setSuccess('Check your email for the magic link.');
    } catch (err: any) {
      setError(getApiErrorInfo(err, 'Failed to request the magic link.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ pt: { xs: 2, md: 4 } }}>
        <Paper
          sx={{
            p: { xs: 3, md: 4 },
            borderRadius: 7,
            background: (theme) =>
              `linear-gradient(145deg, ${alpha(theme.palette.primary.main, 0.12)}, ${alpha(theme.palette.secondary.main, 0.08)})`,
          }}
        >
          <Stack spacing={3}>
            <Stack spacing={1.5}>
              <Chip
                icon={<VerifiedRoundedIcon />}
                label="Passwordless sign-in"
                color="primary"
                variant="outlined"
                sx={{ alignSelf: 'flex-start' }}
              />
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                Sign in
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 460 }}>
                We send a one-time magic link to your inbox. Open it on this device and you’ll be signed in automatically.
              </Typography>
            </Stack>

            {error && <ErrorBanner title={error.title} message={error.message} hint={error.hint} onClose={() => setError(null)} />}
            {success && <Alert severity="success">{success}</Alert>}

            {verifying && (
              <Paper sx={{ p: 2.5, borderRadius: 4 }}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <CircularProgress size={22} />
                  <Box>
                    <Typography variant="subtitle1">Verifying your magic link</Typography>
                    <Typography variant="body2" color="text.secondary">
                      This usually completes in a moment.
                    </Typography>
                  </Box>
                </Stack>
              </Paper>
            )}

            <Box component="form" onSubmit={handleSubmit}>
              <Paper sx={{ p: 2, borderRadius: 5, bgcolor: (theme) => alpha(theme.palette.background.paper, 0.76) }}>
                <Stack spacing={2}>
                  <TextField
                    fullWidth
                    type="email"
                    label="Work or personal email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={loading}
                    required
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={loading || verifying || !email}
                    startIcon={<MailOutlineRoundedIcon />}
                  >
                    {loading ? 'Sending magic link...' : 'Send magic link'}
                  </Button>
                </Stack>
              </Paper>
            </Box>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Paper sx={{ flex: 1, p: 2.5, borderRadius: 4 }}>
                <Stack spacing={1}>
                  <MarkEmailReadRoundedIcon color="secondary" />
                  <Typography variant="subtitle1">Local development</Typography>
                  <Typography variant="body2" color="text.secondary">
                    When you run Docker Compose, emails are delivered to Mailpit at `http://localhost:8025`.
                  </Typography>
                </Stack>
              </Paper>
              <Paper sx={{ flex: 1, p: 2.5, borderRadius: 4 }}>
                <Stack spacing={1}>
                  <VerifiedRoundedIcon color="primary" />
                  <Typography variant="subtitle1">Session handling</Typography>
                  <Typography variant="body2" color="text.secondary">
                    After verification, the frontend stores a session token for the authenticated Phase 1 flows.
                  </Typography>
                </Stack>
              </Paper>
            </Stack>
          </Stack>
        </Paper>
      </Box>
    </Container>
  );
};
