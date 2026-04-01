import React from 'react';
import { Box, Stepper, Step, StepLabel, Typography, LinearProgress, Paper, Stack } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import ErrorIcon from '@mui/icons-material/Error';

const STEPS = [
  'Downloading paper',
  'Parsing PDF',
  'Generating AI summaries',
  'Explaining formulas',
  'Extracting key terms',
  'Building knowledge graph',
  'Saving results'
];

interface ProcessingProgressProps {
  progressStep?: string;
  progressPercent?: number;
  status: string;
  errorMessage?: string;
  errorHint?: string;
  actions?: React.ReactNode;
}

export const ProcessingProgress: React.FC<ProcessingProgressProps> = ({
  progressStep,
  progressPercent = 0,
  status,
  errorMessage,
  errorHint,
  actions
}) => {
  // Determine active step based on progress
  const getActiveStep = () => {
    if (status === 'complete') return STEPS.length;
    if (status === 'failed') return STEPS.length;
    if (!progressStep) return 0;
    
    const stepIndex = STEPS.findIndex(step => progressStep.toLowerCase().includes(step.toLowerCase()));
    return stepIndex >= 0 ? stepIndex : 0;
  };

  const activeStep = getActiveStep();

  if (status === 'complete') {
    return (
      <Paper sx={{ mt: 3, textAlign: 'center', p: 4, borderRadius: 6 }}>
        <CheckCircleIcon color="success" sx={{ fontSize: 60, mb: 2 }} />
        <Typography variant="h6" color="success.main">Analysis Complete!</Typography>
      </Paper>
    );
  }

  if (status === 'failed') {
    return (
      <Paper sx={{ mt: 3, textAlign: 'center', p: 4, borderRadius: 6 }}>
        <Stack spacing={2} alignItems="center">
          <ErrorIcon color="error" sx={{ fontSize: 60 }} />
          <Typography variant="h6" color="error.main">Processing failed</Typography>
          {errorMessage && (
            <Typography variant="body2" color="text.primary" sx={{ maxWidth: 560 }}>
              {errorMessage}
            </Typography>
          )}
          {errorHint && (
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 560 }}>
              {errorHint}
            </Typography>
          )}
          {actions ? <Box sx={{ pt: 1 }}>{actions}</Box> : null}
        </Stack>
      </Paper>
    );
  }

  return (
    <Paper sx={{ mt: 2, maxWidth: 760, mx: 'auto', p: { xs: 3, md: 4 }, borderRadius: 6 }}>
      <Stack spacing={3}>
        <Box sx={{ textAlign: 'center' }}>
          <HourglassEmptyIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
          <Typography variant="h5">Processing your paper</Typography>
          <Typography variant="body2" color="text.secondary">
            This usually takes a couple of minutes.
          </Typography>
        </Box>

        <Box>
          <LinearProgress
            variant="determinate"
            value={progressPercent}
            sx={{ mb: 1.5, borderRadius: 999, height: 10 }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
            {progressPercent}% complete. {progressStep || 'Starting...'}
          </Typography>
        </Box>

        <Stepper activeStep={activeStep} orientation="vertical" connector={null}>
          {STEPS.map((step, index) => (
            <Step key={step}>
              <StepLabel
                icon={
                  index < activeStep ? (
                    <CheckCircleIcon color="success" fontSize="small" />
                  ) : index === activeStep ? (
                    <HourglassEmptyIcon color="primary" fontSize="small" />
                  ) : (
                    <Box sx={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid', borderColor: 'divider' }} />
                  )
                }
              >
                <Typography
                  variant="body2"
                  color={index <= activeStep ? 'text.primary' : 'text.secondary'}
                  fontWeight={index === activeStep ? 700 : 500}
                >
                  {step}
                </Typography>
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Stack>
    </Paper>
  );
};
