import React, { useState } from 'react';
import { alpha } from '@mui/material/styles';
import { Card, CardContent, CardActions, Button, Typography, Box, Stack, Chip, IconButton, Tooltip } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ShareIcon from '@mui/icons-material/Share';
import DownloadIcon from '@mui/icons-material/Download';
import ArrowOutwardRoundedIcon from '@mui/icons-material/ArrowOutwardRounded';
import { ShareDialog } from '../paper/ShareDialog';
import { ExportMenu } from '../paper/ExportMenu';

interface PaperCardProps {
  id: string;
  title: string;
  authors: string[];
  arxiv_id: string;
  created_at: string;
  token: string;
}

export const PaperCard: React.FC<PaperCardProps> = ({ id, title, authors, arxiv_id, created_at, token }) => {
  const navigate = useNavigate();
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const diff = new Date().getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  const getGradient = () => {
    const hash = arxiv_id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const gradients = [
      'linear-gradient(135deg, #1976d2, #42a5f5)',
      'linear-gradient(135deg, #4caf50, #81c784)',
      'linear-gradient(135deg, #ff9800, #ffb74d)',
      'linear-gradient(135deg, #9c27b0, #ba68c8)',
      'linear-gradient(135deg, #f44336, #e57373)'
    ];
    return gradients[Math.abs(hash) % gradients.length];
  };

  return (
    <>
    <Card
      sx={{
        borderRadius: 5,
        overflow: 'hidden',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 180ms ease, box-shadow 180ms ease',
        '&:hover': { transform: 'translateY(-3px)' },
      }}
    >
      <Box sx={{ minHeight: 136, background: getGradient(), padding: 2.25, color: 'white' }}>
        <Stack spacing={1.5}>
          <Chip
            label={arxiv_id}
            size="small"
            sx={{
              alignSelf: 'flex-start',
              bgcolor: alpha('#ffffff', 0.18),
              color: 'white',
              backdropFilter: 'blur(6px)',
            }}
          />
          <Typography variant="subtitle1" fontWeight={700} sx={{ lineHeight: 1.4 }}>
            {title || 'Untitled'}
          </Typography>
        </Stack>
      </Box>
      <CardContent sx={{ p: 2.5, minWidth: 0 }}>
        <Typography variant="body2" color="text.secondary">
          {authors?.[0] || 'Unknown'}{authors?.length > 1 ? ' et al.' : ''}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
          Saved {formatDate(created_at)}
        </Typography>
      </CardContent>
      <CardActions sx={{ p: 2.5, pt: 0, mt: 'auto', gap: 1 }}>
        <Button size="small" variant="contained" endIcon={<ArrowOutwardRoundedIcon />} onClick={() => navigate(`/paper/${id}`)} sx={{ flex: 1, minWidth: 0 }}>
          Open
        </Button>
        <Tooltip title="Share">
          <IconButton
            aria-label="Share paper"
            color="primary"
            onClick={() => setShareDialogOpen(true)}
            sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 4 }}
          >
            <ShareIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Export">
          <IconButton
            aria-label="Export paper"
            color="primary"
            onClick={(e) => setExportAnchorEl(e.currentTarget)}
            sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 4 }}
          >
            <DownloadIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </CardActions>
    </Card>

    <ShareDialog
      open={shareDialogOpen}
      onClose={() => setShareDialogOpen(false)}
      paperId={id}
      paperTitle={title}
      token={token}
    />

    <ExportMenu
      anchorEl={exportAnchorEl}
      onClose={() => setExportAnchorEl(null)}
      paperId={id}
      paperTitle={title}
      token={token}
    />
    </>
  );
};
