import React, { useState } from 'react';
import { Box, Button, Chip, Collapse, Divider, Paper, Stack, Typography } from '@mui/material';
import { ArtifactInterpretation, FigureCaption, ExtractedTable } from '../../../types';

interface EvidenceSectionProps {
  content?: string;
  artifactInterpretations?: ArtifactInterpretation[];
  figureCaptions?: FigureCaption[];
  tables?: ExtractedTable[];
}

const confidenceColor = (c?: string): 'success' | 'warning' | 'default' => {
  if (c === 'high') return 'success';
  if (c === 'low' || c === 'medium') return 'warning';
  return 'default';
};

export const EvidenceSection: React.FC<EvidenceSectionProps> = ({
  content,
  artifactInterpretations = [],
  figureCaptions = [],
  tables = [],
}) => {
  const [rawOpen, setRawOpen] = useState(false);
  const hasRaw = figureCaptions.length > 0 || tables.length > 0;

  return (
    <Paper sx={{ p: 2.5, borderRadius: 4 }}>
      <Stack spacing={1.5}>
        <Stack direction="row" spacing={1.25} alignItems="center">
          <Box sx={{ width: 28, height: 28, borderRadius: 2, bgcolor: 'rgba(15,143,121,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
            📊
          </Box>
          <Typography variant="h6">Evidence &amp; Results</Typography>
        </Stack>

        {content && (
          <Typography variant="body1" color="text.secondary">{content}</Typography>
        )}

        {artifactInterpretations.length > 0 && (
          <Stack spacing={1.25}>
            {artifactInterpretations.map((item, i) => (
              <Paper key={`${item.label}-${i}`} sx={{ p: 2, borderRadius: 3 }}>
                <Stack spacing={0.75}>
                  <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                    <Typography variant="subtitle2" fontWeight={700}>{item.label}</Typography>
                    <Chip
                      size="small"
                      label={item.artifact_type === 'table' ? 'Table' : item.artifact_type === 'figure' ? 'Figure' : item.artifact_type}
                      variant="outlined"
                    />
                    {item.confidence && (
                      <Chip
                        size="small"
                        label={`${item.confidence} confidence`}
                        color={confidenceColor(item.confidence)}
                        variant="outlined"
                      />
                    )}
                  </Stack>
                  <Typography variant="body2" color="text.secondary">{item.what_it_shows}</Typography>
                  {item.why_it_matters && (
                    <Typography variant="body2">
                      <strong>Why it matters:</strong> {item.why_it_matters}
                    </Typography>
                  )}
                </Stack>
              </Paper>
            ))}
          </Stack>
        )}

        {hasRaw && (
          <>
            <Divider />
            <Button
              size="small"
              variant="text"
              onClick={() => setRawOpen((v) => !v)}
              sx={{ alignSelf: 'flex-start', color: 'text.secondary' }}
            >
              {rawOpen ? 'Hide raw extracts' : 'Show raw extracts'}
            </Button>
            <Collapse in={rawOpen}>
              <Stack spacing={1.25} sx={{ mt: 1 }}>
                {figureCaptions.map((item, i) => (
                  <Paper key={`fig-${i}`} sx={{ p: 2, borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Page {item.page + 1}{item.section_title ? ` · ${item.section_title}` : ''}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: 13 }}>{item.caption}</Typography>
                  </Paper>
                ))}
                {tables.map((table, i) => (
                  <Paper key={`tbl-${i}`} sx={{ p: 2, borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="subtitle2" color="text.secondary">{table.title}</Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      Page {table.page + 1}{table.section_title ? ` · ${table.section_title}` : ''}
                    </Typography>
                    <Box sx={{ overflowX: 'auto' }}>
                      <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', minWidth: 320 }}>
                        <Box component="tbody">
                          {table.rows.map((row, ri) => (
                            <Box component="tr" key={ri}>
                              {row.map((cell, ci) => (
                                <Box component="td" key={ci} sx={{ borderBottom: '1px solid', borderColor: 'divider', py: 0.75, pr: 1.5, fontSize: 12, color: 'text.secondary', verticalAlign: 'top' }}>
                                  {cell || '—'}
                                </Box>
                              ))}
                            </Box>
                          ))}
                        </Box>
                      </Box>
                    </Box>
                  </Paper>
                ))}
              </Stack>
            </Collapse>
          </>
        )}
      </Stack>
    </Paper>
  );
};
