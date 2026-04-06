import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button } from '@mui/material';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
  error?: string;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open, title, message, confirmLabel = 'Confirm', onConfirm, onCancel, loading = false, error,
}) => (
  <Dialog open={open} onClose={onCancel} PaperProps={{ sx: { borderRadius: 4, p: 1 } }}>
    <DialogTitle sx={{ fontWeight: 700 }}>{title}</DialogTitle>
    <DialogContent>
      <DialogContentText>{message}</DialogContentText>
    </DialogContent>
    {error && (
      <DialogContent sx={{ pt: 0 }}>
        <DialogContentText color="error" variant="body2">{error}</DialogContentText>
      </DialogContent>
    )}
    <DialogActions sx={{ px: 3, pb: 2 }}>
      <Button onClick={onCancel} disabled={loading}>Cancel</Button>
      <Button onClick={onConfirm} variant="contained" color="error" disabled={loading}>
        {loading ? 'Deleting…' : confirmLabel}
      </Button>
    </DialogActions>
  </Dialog>
);
