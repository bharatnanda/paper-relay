import React, { useState } from 'react';
import {
  Box,
  Chip,
  InputAdornment,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { DistilledTerm } from '../../types';

interface TermGlossaryProps {
  terms: DistilledTerm[];
}

export const TermGlossary: React.FC<TermGlossaryProps> = ({ terms }) => {
  const [query, setQuery] = useState('');

  const filtered = query.trim()
    ? terms.filter(
        (t) =>
          t.term.toLowerCase().includes(query.toLowerCase()) ||
          t.definition.toLowerCase().includes(query.toLowerCase())
      )
    : terms;

  return (
    <Paper sx={{ p: { xs: 2, md: 3 }, borderRadius: 5 }}>
      <Stack spacing={2}>
        <Typography variant="h6">Term Glossary</Typography>
        <TextField
          size="small"
          placeholder="Search terms or definitions…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
          sx={{ maxWidth: 400 }}
        />
        {filtered.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No terms match "{query}".
          </Typography>
        ) : (
          <Box sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Term</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Definition</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filtered.map((term, i) => (
                  <TableRow key={`${term.term}-${i}`}>
                    <TableCell sx={{ fontWeight: 600, whiteSpace: 'nowrap' }}>{term.term}</TableCell>
                    <TableCell>
                      <Chip label={term.category} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell sx={{ color: 'text.secondary' }}>{term.definition}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}
      </Stack>
    </Paper>
  );
};
