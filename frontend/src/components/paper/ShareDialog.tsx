import React, { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, Box, IconButton, Typography, Alert, Stack } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckRoundedIcon from '@mui/icons-material/CheckRounded';
import { AppErrorInfo, getApiErrorInfo, shareAPI } from '../../services/api';
import { ErrorBanner } from '../common/ErrorBanner';

interface ShareDialogProps {
  open: boolean;
  onClose: () => void;
  paperId: string;
  paperTitle: string;
  token: string;
}

export const ShareDialog: React.FC<ShareDialogProps> = ({ open, onClose, paperId, paperTitle, token }) => {
  const [shareUrl, setShareUrl] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppErrorInfo | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!open) return;
    setCopied(false);

    const createShareLink = async () => {
      if (shareUrl) return; // Don't create duplicate links
      
      setLoading(true);
      setError(null);
      
      try {
        const data = await shareAPI.createShareLink(paperId, token);
        setShareUrl(`${window.location.origin}${data.share_url}`);
      } catch (err: any) {
        setError(getApiErrorInfo(err, 'Failed to create the share link.'));
        console.error('Share link creation error:', err);
      } finally {
        setLoading(false);
      }
    };
    
    createShareLink();
  }, [open, paperId, token, shareUrl]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
  };
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Share This Paper</DialogTitle>
      <DialogContent>
        {loading ? <Box sx={{ textAlign: 'center', py: 4 }}>Creating...</Box> : error ? (
          <Box sx={{ py: 2 }}>
            <ErrorBanner title={error.title} message={error.message} hint={error.hint} />
          </Box>
        ) : (
          <Stack spacing={2}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Copy this public link to share "{paperTitle}".
            </Typography>
            <TextField fullWidth value={shareUrl} InputProps={{ readOnly: true, endAdornment: <IconButton onClick={handleCopy}><ContentCopyIcon /></IconButton> }} sx={{ mb: 1 }} />
            {copied ? <Alert icon={<CheckRoundedIcon fontSize="inherit" />} severity="success">Share link copied.</Alert> : null}
          </Stack>
        )}
      </DialogContent>
      <DialogActions><Button onClick={onClose}>Close</Button></DialogActions>
    </Dialog>
  );
};
