import React, { useEffect, useState } from 'react';
import { AppBar, Box, Button, CircularProgress, Container, Menu, MenuItem, Stack, Toolbar, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import MenuBookRoundedIcon from '@mui/icons-material/MenuBookRounded';
import LogoutRoundedIcon from '@mui/icons-material/LogoutRounded';
import LoginRoundedIcon from '@mui/icons-material/LoginRounded';
import PersonRoundedIcon from '@mui/icons-material/PersonRounded';
import KeyboardArrowDownRoundedIcon from '@mui/icons-material/KeyboardArrowDownRounded';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { authAPI } from '../../services/api';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, syncUser, hasHydrated } = useAuth();
  const [authReady, setAuthReady] = useState(false);
  const [accountAnchorEl, setAccountAnchorEl] = useState<null | HTMLElement>(null);
  const onLibrary = location.pathname === '/library';
  const onAnalyze = location.pathname === '/' || location.pathname.startsWith('/paper/');

  useEffect(() => {
    if (!hasHydrated) {
      return;
    }

    let active = true;

    const validateSession = async () => {
      if (!user) {
        if (active) {
          setAuthReady(true);
        }
        return;
      }

      try {
        const sessionUser = await authAPI.getSessionUser(user.token);
        if (!active) return;
        syncUser({
          user_id: sessionUser.user_id,
          email: sessionUser.email,
          papers_count: sessionUser.papers_count,
        });
      } catch {
        if (!active) return;
        logout();
        navigate('/login', { replace: true });
      } finally {
        if (active) {
          setAuthReady(true);
        }
      }
    };

    setAuthReady(false);
    validateSession();

    return () => {
      active = false;
    };
  }, [user?.token, hasHydrated, logout, navigate, syncUser]);

  const handleLogout = () => {
    setAccountAnchorEl(null);
    logout();
    navigate('/login', { replace: true });
  };

  const handleOpenAccountMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAccountAnchorEl(event.currentTarget);
  };

  const handleCloseAccountMenu = () => {
    setAccountAnchorEl(null);
  };

  const navigationButtonSx = (active: boolean) => ({
    fontWeight: 700,
    color: active ? undefined : 'text.primary',
    borderColor: active ? 'transparent' : (theme: any) => alpha(theme.palette.text.primary, 0.14),
    backgroundColor: active ? undefined : (theme: any) => alpha(theme.palette.background.paper, 0.9),
    '&:hover': active
      ? undefined
      : {
          borderColor: (theme: any) => alpha(theme.palette.primary.main, 0.32),
          backgroundColor: (theme: any) => alpha(theme.palette.primary.main, 0.08),
        },
  });

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="sticky">
        <Container maxWidth="xl">
          <Toolbar
            disableGutters
            sx={{
              minHeight: { xs: 84, md: 94 },
              gap: 2,
              py: 1.5,
              justifyContent: 'space-between',
            }}
          >
            <Box
              component={Link}
              to="/"
              sx={{
                textDecoration: 'none',
                color: 'inherit',
                flexShrink: 1,
                minWidth: 0,
              }}
            >
              <Box
                component="img"
                src="/wordmark.svg"
                alt="PaperRelay"
                sx={{
                  height: { xs: 34, md: 52 },
                  width: 'auto',
                  display: 'block',
                  maxWidth: { xs: 220, md: 300 },
                }}
              />
            </Box>

            <Stack
              direction="row"
              spacing={1.25}
              alignItems="center"
              sx={{ flexWrap: 'wrap', justifyContent: 'flex-end' }}
            >
              {user && (
                <Button
                  component={Link}
                  to="/"
                  color={onAnalyze ? 'primary' : 'inherit'}
                  variant={onAnalyze ? 'contained' : 'outlined'}
                  startIcon={<AutoAwesomeRoundedIcon />}
                  sx={navigationButtonSx(onAnalyze)}
                >
                  Analyze
                </Button>
              )}
              {user && (
                <Button
                  component={Link}
                  to="/library"
                  color={onLibrary ? 'primary' : 'inherit'}
                  variant={onLibrary ? 'contained' : 'outlined'}
                  startIcon={<MenuBookRoundedIcon />}
                  sx={navigationButtonSx(onLibrary)}
                >
                  Library
                </Button>
              )}
              {user ? (
                <>
                  <Button
                    color="inherit"
                    variant="outlined"
                    startIcon={<PersonRoundedIcon />}
                    endIcon={<KeyboardArrowDownRoundedIcon />}
                    onClick={handleOpenAccountMenu}
                    sx={{
                      fontWeight: 700,
                      color: 'text.primary',
                      borderColor: (theme) => alpha(theme.palette.text.primary, 0.14),
                      backgroundColor: (theme) => alpha(theme.palette.background.paper, 0.9),
                      maxWidth: { xs: 160, md: 260 },
                      '&:hover': {
                        borderColor: (theme) => alpha(theme.palette.primary.main, 0.32),
                        backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.08),
                      },
                      '.MuiButton-startIcon, .MuiButton-endIcon': {
                        color: 'inherit',
                      },
                    }}
                  >
                    <Box
                      component="span"
                      sx={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        display: 'block',
                      }}
                    >
                      {user.email}
                    </Box>
                  </Button>
                  <Menu
                    anchorEl={accountAnchorEl}
                    open={Boolean(accountAnchorEl)}
                    onClose={handleCloseAccountMenu}
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                    PaperProps={{
                      sx: {
                        mt: 1,
                        minWidth: 220,
                        borderRadius: 3,
                      },
                    }}
                  >
                    <MenuItem disabled sx={{ opacity: 1, fontWeight: 600 }}>
                      {user.email}
                    </MenuItem>
                    <MenuItem onClick={handleLogout}>
                      <LogoutRoundedIcon fontSize="small" sx={{ mr: 1.25 }} />
                      Sign out
                    </MenuItem>
                  </Menu>
                </>
              ) : (
                <Button component={Link} to="/login" variant="contained" startIcon={<LoginRoundedIcon />}>
                  Sign in
                </Button>
              )}
            </Stack>
          </Toolbar>
        </Container>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: { xs: 3, md: 5 } }}>
        {!authReady ? (
          <Box sx={{ minHeight: '50vh', display: 'grid', placeItems: 'center' }}>
            <Stack spacing={2} alignItems="center">
              <CircularProgress size={28} />
              <Typography variant="body2" color="text.secondary">
                Restoring your session...
              </Typography>
            </Stack>
          </Box>
        ) : (
          children
        )}
      </Container>
    </Box>
  );
};
