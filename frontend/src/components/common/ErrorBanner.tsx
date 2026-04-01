import React from 'react';
import { Alert, AlertTitle, Box, Paper } from '@mui/material';

interface ErrorBannerProps {
  title?: string;
  message: string;
  hint?: string;
  actions?: React.ReactNode;
  onClose?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ title = 'Error', message, hint, actions, onClose }) => {
  return (
    <Paper sx={{ borderRadius: 5, overflow: 'hidden' }}>
      <Alert severity="error" onClose={onClose} sx={{ borderRadius: 5 }}>
        <AlertTitle>{title}</AlertTitle>
        <Box>{message}</Box>
        {hint ? <Box sx={{ mt: 1, color: 'text.secondary' }}>{hint}</Box> : null}
        {actions ? <Box sx={{ mt: 2 }}>{actions}</Box> : null}
      </Alert>
    </Paper>
  );
};
