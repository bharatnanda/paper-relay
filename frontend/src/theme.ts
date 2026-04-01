import { alpha, createTheme } from '@mui/material/styles';

export const createAppTheme = (mode: 'light' | 'dark') => {
  const isDark = mode === 'dark';
  const primary = isDark ? '#8fb8ff' : '#2154d6';
  const secondary = isDark ? '#67d5c0' : '#0f8f79';
  const accent = isDark ? '#f3b783' : '#ca6b14';
  const backgroundDefault = isDark ? '#08111f' : '#f4f6fb';
  const backgroundPaper = isDark ? '#101a2b' : '#ffffff';
  const borderColor = isDark ? alpha('#dfe7ff', 0.08) : alpha('#16315f', 0.08);

  return createTheme({
    palette: {
      mode,
      primary: { main: primary },
      secondary: { main: secondary },
      warning: { main: accent },
      background: {
        default: backgroundDefault,
        paper: backgroundPaper,
      },
      text: {
        primary: isDark ? '#edf3ff' : '#15233b',
        secondary: isDark ? '#9fb0cd' : '#60708e',
      },
      divider: borderColor,
    },
    shape: {
      borderRadius: 3,
    },
    typography: {
      fontFamily: '"Manrope", "Avenir Next", "Segoe UI", sans-serif',
      allVariants: {
        overflowWrap: 'anywhere',
      },
      h1: { fontWeight: 800, letterSpacing: '-0.04em' },
      h2: { fontWeight: 800, letterSpacing: '-0.04em' },
      h3: { fontWeight: 800, letterSpacing: '-0.04em' },
      h4: { fontWeight: 780, letterSpacing: '-0.03em' },
      h5: { fontWeight: 760, letterSpacing: '-0.02em' },
      h6: { fontWeight: 760, letterSpacing: '-0.02em' },
      button: { fontWeight: 700, textTransform: 'none' },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundImage: isDark
              ? 'radial-gradient(circle at top, rgba(33,84,214,0.18), transparent 28%), radial-gradient(circle at 80% 10%, rgba(15,143,121,0.14), transparent 25%), linear-gradient(180deg, #07101d 0%, #0b1323 100%)'
              : 'radial-gradient(circle at top, rgba(33,84,214,0.10), transparent 28%), radial-gradient(circle at 80% 10%, rgba(15,143,121,0.08), transparent 22%), linear-gradient(180deg, #f6f8fc 0%, #eef3fb 100%)',
            backgroundAttachment: 'fixed',
          },
          a: {
            color: 'inherit',
          },
          '#root': {
            minHeight: '100vh',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            backgroundColor: alpha(backgroundPaper, isDark ? 0.72 : 0.8),
            backdropFilter: 'blur(18px)',
            borderBottom: `1px solid ${borderColor}`,
            boxShadow: 'none',
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            border: `1px solid ${borderColor}`,
            boxShadow: isDark
              ? '0 20px 50px rgba(1, 7, 20, 0.38)'
              : '0 20px 50px rgba(32, 62, 118, 0.08)',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            border: `1px solid ${borderColor}`,
            boxShadow: isDark
              ? '0 22px 60px rgba(1, 7, 20, 0.34)'
              : '0 18px 45px rgba(27, 54, 103, 0.08)',
          },
        },
      },
      MuiButton: {
        defaultProps: {
          disableElevation: true,
        },
        styleOverrides: {
          root: {
            borderRadius: 14,
            paddingInline: 18,
            minHeight: 42,
          },
          containedPrimary: {
            boxShadow: isDark
              ? '0 10px 24px rgba(33, 84, 214, 0.34)'
              : '0 12px 26px rgba(33, 84, 214, 0.22)',
          },
        },
      },
      MuiTextField: {
        defaultProps: {
          variant: 'outlined',
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            backgroundColor: isDark ? alpha('#dfe7ff', 0.03) : alpha('#ffffff', 0.65),
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 12,
          },
        },
      },
      MuiTabs: {
        styleOverrides: {
          indicator: {
            height: 3,
            borderRadius: 999,
          },
        },
      },
    },
  });
};
