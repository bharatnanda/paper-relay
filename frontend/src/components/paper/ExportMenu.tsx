import React from 'react';
import { Menu, MenuItem } from '@mui/material';
import ArticleIcon from '@mui/icons-material/Article';
import CodeIcon from '@mui/icons-material/Code';
import { API_BASE_URL } from '../../services/api';

interface ExportMenuProps {
  anchorEl: HTMLElement | null;
  onClose: () => void;
  paperId: string;
  paperTitle?: string;
  token: string;
}

export const ExportMenu: React.FC<ExportMenuProps> = ({ anchorEl, onClose, paperId, paperTitle, token }) => {

  const handleExport = async (format: 'pdf' | 'md') => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/papers/${paperId}/export?format=${format}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      if (!response.ok) {
        throw new Error('Export failed');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Use paper title for filename if available, otherwise use ID
      const safeName = (paperTitle || paperId)
        .replace(/[^a-z0-9]/gi, '_')
        .toLowerCase()
        .substring(0, 50);
      a.download = `${safeName}.${format}`;
      
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Export error:', err);
    } finally {
      onClose();
    }
  };

  return (
    <Menu
      anchorEl={anchorEl}
      open={Boolean(anchorEl)}
      onClose={onClose}
    >
      <MenuItem onClick={() => { handleExport('pdf'); onClose(); }}>
        <ArticleIcon sx={{ mr: 1 }} />
        PDF
      </MenuItem>
      <MenuItem onClick={() => { handleExport('md'); onClose(); }}>
        <CodeIcon sx={{ mr: 1 }} />
        Markdown
      </MenuItem>
    </Menu>
  );
};
