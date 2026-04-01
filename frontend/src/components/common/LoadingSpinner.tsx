import React from 'react';
import { CircularProgress, Box, Typography, Paper } from '@mui/material';

interface LoadingSpinnerProps {
  size?: number;
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 40, message }) => {
  return (
    <Paper sx={{ p: 4, borderRadius: 6 }}>
      <Box display="flex" flexDirection="column" alignItems="center" gap={2} textAlign="center">
        <CircularProgress size={size} />
        {message && <Typography variant="body2" color="text.secondary">{message}</Typography>}
      </Box>
    </Paper>
  );
};
