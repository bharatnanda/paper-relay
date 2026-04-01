import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Typography, Container, Tabs, Tab, Paper, Stack, Chip, Divider, Button, Drawer, IconButton, Snackbar, Alert, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import FunctionsRoundedIcon from '@mui/icons-material/FunctionsRounded';
import AccountTreeRoundedIcon from '@mui/icons-material/AccountTreeRounded';
import MenuBookRoundedIcon from '@mui/icons-material/MenuBookRounded';
import OpenInNewRoundedIcon from '@mui/icons-material/OpenInNewRounded';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import { useAuth } from '../hooks/useAuth';
import { AppErrorInfo, getApiErrorInfo, papersAPI } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { ProcessingProgress } from '../components/common/ProcessingProgress';
import { KnowledgeGraphViz } from '../components/paper/KnowledgeGraphViz';
import { FormulaBlock } from '../components/paper/FormulaBlock';
import { PaperAnalysis, FormulaExplanation, DistilledSection, DistilledTerm, ArtifactInterpretation } from '../types';

const getProcessingFailureHint = (errorMessage?: string) => {
  const normalized = errorMessage?.toLowerCase() || '';

  if (normalized.includes('download pdf')) {
    return 'PaperRelay could not download the PDF from arXiv. Retry in a moment, or confirm that the paper PDF is publicly accessible.';
  }

  if (normalized.includes('parsing')) {
    return 'The PDF was found but could not be parsed cleanly. Retrying may help for transient extraction issues.';
  }

  if (normalized.includes('ai processing') || normalized.includes('service unavailable') || normalized.includes('timeout')) {
    return 'The paper was fetched, but the analysis step could not finish. Retry after the upstream service recovers.';
  }

  return 'Retry the analysis. If the same paper keeps failing, inspect the backend and worker logs.';
};

export const PaperPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));
  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppErrorInfo | null>(null);
  const [tab, setTab] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [paperViewerOpen, setPaperViewerOpen] = useState(false);
  const [completionNoticeOpen, setCompletionNoticeOpen] = useState(false);
  const previousStatusRef = useRef<PaperAnalysis['status'] | null>(null);

  useEffect(() => {
    if (!user || !paperId) {
      navigate('/');
      return;
    }

    let mounted = true;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const fetchAnalysis = async () => {
      try {
        const result = await papersAPI.getAnalysis(paperId, user.token);
        if (!mounted) return;

        setAnalysis(result);
        setError(null);
        if (result.status === 'processing' || result.status === 'pending') {
          timeoutId = setTimeout(fetchAnalysis, 3000);
        }
      } catch (err: any) {
        if (!mounted) return;
        setError(getApiErrorInfo(err, 'Failed to load the paper analysis.'));
        console.error('Paper analysis fetch error:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchAnalysis();

    return () => {
      mounted = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [paperId, user, navigate, reloadKey]);

  useEffect(() => {
    if (!paperId || !analysis) {
      return;
    }

    const watchKey = `paperrelay-analysis-watch:${paperId}`;
    const notifiedKey = `paperrelay-analysis-complete:${paperId}`;
    const permissionKey = `paperrelay-notification-permission-requested:${paperId}`;
    const previousStatus = previousStatusRef.current;

    if (analysis.status === 'processing' || analysis.status === 'pending') {
      sessionStorage.setItem(watchKey, '1');
      sessionStorage.removeItem(notifiedKey);

      if ('Notification' in window && Notification.permission === 'default' && !sessionStorage.getItem(permissionKey)) {
        sessionStorage.setItem(permissionKey, '1');
        Notification.requestPermission().catch(() => undefined);
      }
    }

    const wasBeingTracked = sessionStorage.getItem(watchKey) === '1';
    const alreadyNotified = sessionStorage.getItem(notifiedKey) === '1';
    const transitionedToComplete = analysis.status === 'complete' && previousStatus !== 'complete' && previousStatus !== null;
    const completedAfterWatch = analysis.status === 'complete' && wasBeingTracked && !alreadyNotified;

    if (transitionedToComplete || completedAfterWatch) {
      setCompletionNoticeOpen(true);
      sessionStorage.setItem(notifiedKey, '1');
      sessionStorage.removeItem(watchKey);

      if ('Notification' in window && Notification.permission === 'granted' && document.visibilityState === 'hidden') {
        const notification = new Notification('PaperRelay analysis ready', {
          body: analysis.title || 'Your paper distillation is complete.',
          tag: `paperrelay-analysis-${paperId}`,
        });
        notification.onclick = () => {
          window.focus();
          notification.close();
        };
      }
    }

    if (analysis.status === 'failed') {
      sessionStorage.removeItem(watchKey);
    }

    previousStatusRef.current = analysis.status;
  }, [analysis, paperId]);

  if (loading) return <LoadingSpinner message="Loading paper analysis..." />;
  if (error || !analysis) {
    return (
      <Container maxWidth="md">
        <Box sx={{ mt: 8 }}>
          <ErrorBanner
            title={error?.title || 'Paper not found'}
            message={error?.message || 'The requested paper analysis could not be loaded.'}
            hint={error?.hint}
            actions={
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                <Button variant="contained" onClick={() => {
                  setLoading(true);
                  setError(null);
                  setReloadKey((value) => value + 1);
                }}>
                  Retry
                </Button>
                <Button variant="outlined" onClick={() => navigate('/library')}>
                  Back to library
                </Button>
              </Stack>
            }
          />
        </Box>
      </Container>
    );
  }

  // Show progress stepper if still processing
  if (analysis.status === 'processing' || analysis.status === 'pending' || analysis.status === 'failed') {
    return (
      <Container maxWidth="md">
        <Box sx={{ mt: 8 }}>
          <ProcessingProgress
            progressStep={analysis.progress_step}
            progressPercent={analysis.progress_percent}
            status={analysis.status}
            errorMessage={analysis.error_message}
            errorHint={analysis.status === 'failed' ? getProcessingFailureHint(analysis.error_message) : undefined}
            actions={analysis.status === 'failed' ? (
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                <Button variant="contained" onClick={() => navigate('/')}>
                  Analyze another paper
                </Button>
                <Button variant="outlined" onClick={() => setReloadKey((value) => value + 1)}>
                  Refresh status
                </Button>
              </Stack>
            ) : undefined}
          />
        </Box>
      </Container>
    );
  }

  const artifactInterpretations = analysis.summary?.artifact_interpretations
    || analysis.summary?.results_view?.artifact_interpretations
    || [
      ...(analysis.summary?.table_interpretations || []),
      ...(analysis.summary?.figure_interpretations || []),
    ];
  const originalPaperUrl = analysis.pdf_url || (analysis.arxiv_id ? `https://arxiv.org/pdf/${analysis.arxiv_id}.pdf` : '');

  const renderPaperViewer = (embedded: boolean) => (
    <Paper
      sx={{
        p: { xs: 2, md: 2.5 },
        borderRadius: embedded ? 6 : 0,
        display: 'flex',
        flexDirection: 'column',
        height: embedded ? 'calc(100vh - 168px)' : '100%',
        minHeight: embedded ? 680 : '100vh',
        boxShadow: embedded ? undefined : 'none',
      }}
    >
      <Stack spacing={2} sx={{ height: '100%' }}>
        <Stack direction="row" spacing={1.25} justifyContent="space-between" alignItems="flex-start">
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="overline" color="text.secondary">
              Original paper
            </Typography>
            <Typography variant="h6">Source PDF</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Cross-check the distilled explanation against the original paper without leaving the workspace.
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            {originalPaperUrl ? (
              <Button
                size="small"
                variant="outlined"
                endIcon={<OpenInNewRoundedIcon />}
                component="a"
                href={originalPaperUrl}
                target="_blank"
                rel="noreferrer"
              >
                Open
              </Button>
            ) : null}
            {!embedded ? (
              <IconButton onClick={() => setPaperViewerOpen(false)} aria-label="Close paper viewer">
                <CloseRoundedIcon />
              </IconButton>
            ) : null}
          </Stack>
        </Stack>
        <Chip
          size="small"
          label={analysis.arxiv_id ? `arXiv ${analysis.arxiv_id}` : 'Original source'}
          variant="outlined"
          sx={{ alignSelf: 'flex-start' }}
        />
        {analysis.title ? (
          <Typography variant="body2" color="text.secondary">
            {analysis.title}
          </Typography>
        ) : null}
        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            overflow: 'hidden',
            borderRadius: 4,
            border: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.default',
          }}
        >
          {originalPaperUrl ? (
            <Box
              component="iframe"
              src={originalPaperUrl}
              title={analysis.title || 'Original paper PDF'}
              sx={{ width: '100%', height: '100%', minHeight: embedded ? 560 : '100vh', border: 0, bgcolor: '#fff' }}
            />
          ) : (
            <Stack spacing={2} justifyContent="center" alignItems="flex-start" sx={{ p: 3, height: '100%' }}>
              <Typography variant="body1">No source PDF URL is available for this paper.</Typography>
              {analysis.arxiv_id ? (
                <Button
                  variant="outlined"
                  endIcon={<OpenInNewRoundedIcon />}
                  component="a"
                  href={`https://arxiv.org/abs/${analysis.arxiv_id}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open arXiv page
                </Button>
              ) : null}
            </Stack>
          )}
        </Box>
      </Stack>
    </Paper>
  );

  return (
    <Container maxWidth={paperViewerOpen && isDesktop ? 'xl' : 'lg'}>
      <Box
        sx={{
          display: 'grid',
          gap: 3,
          gridTemplateColumns: paperViewerOpen && isDesktop ? 'minmax(0, 1.45fr) minmax(360px, 0.9fr)' : 'minmax(0, 1fr)',
          alignItems: 'start',
        }}
      >
        <Box sx={{ display: 'grid', gap: 3, minWidth: 0 }}>
        <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 6 }}>
          <Stack spacing={2}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} justifyContent="space-between">
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="overline" color="text.secondary">
                  Analysis workspace
                </Typography>
                <Typography variant="h3">Distilled paper view</Typography>
                <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 760, mt: 1 }}>
                  Read the paper as a guided walkthrough: what problem it tackles, how the method works, what evidence it shows, where the caveats are, and which concepts connect across the paper.
                </Typography>
              </Box>
              <Stack direction="row" spacing={1} alignItems="flex-start" flexWrap="wrap">
                <Chip icon={<AutoAwesomeRoundedIcon />} label="LLM summary" color="primary" variant="outlined" />
                <Chip icon={<FunctionsRoundedIcon />} label="Formula explanations" color="secondary" variant="outlined" />
                <Chip icon={<AccountTreeRoundedIcon />} label="Knowledge graph" color="warning" variant="outlined" />
                <Button
                  variant={paperViewerOpen ? 'contained' : 'outlined'}
                  startIcon={<MenuBookRoundedIcon />}
                  onClick={() => setPaperViewerOpen(true)}
                  sx={{ ml: { md: 1 } }}
                >
                  View paper
                </Button>
                {paperViewerOpen && isDesktop ? (
                  <Button variant="text" onClick={() => setPaperViewerOpen(false)}>
                    Hide paper
                  </Button>
                ) : null}
              </Stack>
            </Stack>
            <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mt: 1 }}>
              <Tab label="Summary" />
              <Tab label="Walkthrough" />
              <Tab label="Math" />
              <Tab label="Knowledge Graph" />
            </Tabs>
          </Stack>
        </Paper>

        <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 6 }}>
          {tab === 0 && analysis.summary && (
            <Stack spacing={3}>
              <Box>
                <Typography variant="h5" gutterBottom>Quick summary</Typography>
                <Typography variant="body1" color="text.secondary">{analysis.summary.quick}</Typography>
              </Box>
              {analysis.summary.problem_and_motivation ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Problem and motivation</Typography>
                    <Typography variant="body1" color="text.secondary">{analysis.summary.problem_and_motivation}</Typography>
                  </Box>
                </>
              ) : null}
              {analysis.summary.method_deep_dive ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>How the paper works</Typography>
                    <Typography variant="body1" color="text.secondary">{analysis.summary.method_deep_dive}</Typography>
                  </Box>
                </>
              ) : null}
              {analysis.summary.results_and_evidence || analysis.summary.technical ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Results and evidence</Typography>
                    <Typography variant="body1" color="text.secondary">
                      {analysis.summary.results_and_evidence || analysis.summary.technical}
                    </Typography>
                    {analysis.summary.results_view?.evaluation_setup ? (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1.25 }}>
                        <strong>Evaluation setup:</strong> {analysis.summary.results_view.evaluation_setup}
                      </Typography>
                    ) : null}
                  </Box>
                </>
              ) : null}
              {analysis.summary.results_view?.strongest_evidence?.length ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Strongest evidence</Typography>
                    <Stack spacing={1.25}>
                      {analysis.summary.results_view.strongest_evidence.map((item: string, index: number) => (
                        <Paper key={`${item.substring(0, 40)}-${index}`} sx={{ p: 2.25, borderRadius: 4 }}>
                          <Typography>{item}</Typography>
                        </Paper>
                      ))}
                    </Stack>
                  </Box>
                </>
              ) : null}
              {artifactInterpretations?.length ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Interpreted evidence from figures and tables</Typography>
                    <Stack spacing={1.5}>
                      {artifactInterpretations.map((item: ArtifactInterpretation, index: number) => (
                        <Paper key={`${item.label}-${index}`} sx={{ p: 2.5, borderRadius: 4 }}>
                          <Stack spacing={1}>
                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                              <Typography variant="subtitle1" fontWeight={700}>{item.label}</Typography>
                              <Chip
                                size="small"
                                label={item.artifact_type === 'table' ? 'Table' : item.artifact_type === 'figure' ? 'Figure' : item.artifact_type}
                                variant="outlined"
                              />
                              {item.confidence ? (
                                <Chip
                                  size="small"
                                  label={`${item.confidence} confidence`}
                                  color={item.confidence === 'high' ? 'success' : item.confidence === 'low' ? 'warning' : 'default'}
                                  variant="outlined"
                                />
                              ) : null}
                            </Stack>
                            {item.section_title ? (
                              <Typography variant="body2" color="text.secondary">
                                Section: {item.section_title}
                              </Typography>
                            ) : null}
                            <Typography variant="body2" color="text.secondary">{item.what_it_shows}</Typography>
                            {item.why_it_matters ? (
                              <Typography variant="body2">
                                <strong>Why it matters:</strong> {item.why_it_matters}
                              </Typography>
                            ) : null}
                          </Stack>
                        </Paper>
                      ))}
                    </Stack>
                  </Box>
                </>
              ) : null}
              <Divider />
              <Box>
                <Typography variant="h6" gutterBottom>Key contributions</Typography>
                <Stack spacing={1.25}>
                  {analysis.summary.key_contributions.map((c: string, i: number) => (
                    <Paper key={c.substring(0, 50) + i} sx={{ p: 2.25, borderRadius: 4 }}>
                      <Typography>{c}</Typography>
                    </Paper>
                  ))}
                </Stack>
              </Box>
              {analysis.summary.key_findings?.length ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Key findings</Typography>
                    <Stack spacing={1.25}>
                      {analysis.summary.key_findings.map((finding: string, i: number) => (
                        <Paper key={finding.substring(0, 50) + i} sx={{ p: 2.25, borderRadius: 4 }}>
                          <Typography>{finding}</Typography>
                        </Paper>
                      ))}
                    </Stack>
                  </Box>
                </>
              ) : null}
              {analysis.summary.section_breakdown?.length ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Section-by-section walkthrough</Typography>
                    <Stack spacing={1.5}>
                      {analysis.summary.section_breakdown.map((section: DistilledSection, index: number) => (
                        <Paper key={`${section.title}-${index}`} sx={{ p: 2.5, borderRadius: 4 }}>
                          <Stack spacing={1}>
                            <Typography variant="subtitle1" fontWeight={700}>{section.title}</Typography>
                            <Typography variant="body2" color="text.secondary">{section.summary}</Typography>
                            {section.why_it_matters ? (
                              <Typography variant="body2">
                                <strong>Why it matters:</strong> {section.why_it_matters}
                              </Typography>
                            ) : null}
                          </Stack>
                        </Paper>
                      ))}
                    </Stack>
                  </Box>
                </>
              ) : (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Technical summary</Typography>
                    <Typography variant="body1" color="text.secondary">{analysis.summary.technical}</Typography>
                  </Box>
                </>
              )}
              {analysis.summary.terms?.length ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Key terms to know</Typography>
                    <Stack spacing={1.25}>
                      {analysis.summary.terms.map((term: DistilledTerm, index: number) => (
                        <Paper key={`${term.term}-${index}`} sx={{ p: 2.25, borderRadius: 4 }}>
                          <Stack spacing={0.75}>
                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                              <Typography variant="subtitle2">{term.term}</Typography>
                              <Chip size="small" label={term.category} variant="outlined" />
                            </Stack>
                            <Typography variant="body2" color="text.secondary">{term.definition}</Typography>
                          </Stack>
                        </Paper>
                      ))}
                    </Stack>
                  </Box>
                </>
              ) : null}
              {analysis.summary.limitations_and_caveats ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Limitations and caveats</Typography>
                    <Typography variant="body1" color="text.secondary">{analysis.summary.limitations_and_caveats}</Typography>
                  </Box>
                </>
              ) : null}
              {analysis.summary.figure_captions?.length ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Figures mentioned in the paper</Typography>
                    <Stack spacing={1.25}>
                      {analysis.summary.figure_captions.map((item, i) => (
                        <Paper key={`${item.caption}-${i}`} sx={{ p: 2.25, borderRadius: 4 }}>
                          <Stack spacing={0.75}>
                            <Typography variant="body2" color="text.secondary">
                              Page {item.page + 1}{item.section_title ? ` • ${item.section_title}` : ''}
                            </Typography>
                            <Typography>{item.caption}</Typography>
                            {item.context ? (
                              <Typography variant="body2" color="text.secondary">
                                Context: {item.context}
                              </Typography>
                            ) : null}
                          </Stack>
                        </Paper>
                      ))}
                    </Stack>
                  </Box>
                </>
              ) : null}
              {analysis.summary.tables?.length ? (
                <>
                  <Divider />
                  <Box>
                    <Typography variant="h6" gutterBottom>Extracted table snapshots</Typography>
                    <Stack spacing={2}>
                      {analysis.summary.tables.map((table, i) => (
                        <Paper key={`${table.title}-${i}`} sx={{ p: 2.25, borderRadius: 4 }}>
                          <Typography variant="subtitle2">{table.title}</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                            Page {table.page + 1}{table.section_title ? ` • ${table.section_title}` : ''}{table.row_count ? ` • ${table.row_count} rows` : ''}
                          </Typography>
                          {table.context ? (
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                              Context: {table.context}
                            </Typography>
                          ) : null}
                          <Box sx={{ overflowX: 'auto' }}>
                      <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', minWidth: 420 }}>
                              <Box component="tbody">
                                {table.rows.map((row, rowIndex) => (
                                  <Box component="tr" key={`${table.title}-${rowIndex}`}>
                                    {row.map((cell, cellIndex) => (
                                      <Box
                                        component="td"
                                        key={`${table.title}-${rowIndex}-${cellIndex}`}
                                        sx={{
                                          borderBottom: '1px solid',
                                          borderColor: 'divider',
                                          py: 1,
                                          pr: 2,
                                          verticalAlign: 'top',
                                          fontSize: 14,
                                          color: 'text.secondary',
                                          wordBreak: 'break-word',
                                        }}
                                      >
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
                  </Box>
                </>
              ) : null}
            </Stack>
          )}
          {tab === 1 && analysis.summary && (
            <Stack spacing={2}>
              <Paper sx={{ p: 3, borderRadius: 5 }}>
                <Typography variant="h5" gutterBottom>Guided walkthrough</Typography>
                <Typography variant="body1" color="text.secondary">
                  {analysis.summary.guided_walkthrough || analysis.summary.technical}
                </Typography>
              </Paper>
              <Paper sx={{ p: 3, borderRadius: 5 }}>
                <Typography variant="h5" gutterBottom>Explain it simply</Typography>
                <Typography variant="body1" color="text.secondary">{analysis.summary.eli5}</Typography>
              </Paper>
              {analysis.summary.reader_takeaways?.length ? (
                <Paper sx={{ p: 3, borderRadius: 5 }}>
                  <Typography variant="h6" gutterBottom>What to remember</Typography>
                  <Stack spacing={1.25}>
                    {analysis.summary.reader_takeaways.map((item: string, index: number) => (
                      <Paper key={`${item.substring(0, 40)}-${index}`} sx={{ p: 2, borderRadius: 4 }}>
                        <Typography>{item}</Typography>
                      </Paper>
                    ))}
                  </Stack>
                </Paper>
              ) : null}
            </Stack>
          )}
          {tab === 2 && analysis.summary && (
            <Stack spacing={2}>
              <Typography variant="h5">Formula explanations</Typography>
              {analysis.summary.formula_explanations?.length ? (
                analysis.summary.formula_explanations.map((f: FormulaExplanation, i: number) => (
                  <Paper key={f.latex || i} sx={{ p: 2.5, borderRadius: 5 }}>
                    <FormulaBlock formula={f} />
                  </Paper>
                ))
              ) : (
                <Paper sx={{ p: 3, borderRadius: 5 }}>
                  <Typography variant="body1" color="text.secondary">
                    No equation-level explanation was recovered for this paper. If the PDF extraction did not preserve explicit formulas, PaperRelay falls back to higher-level method explanations in the walkthrough.
                  </Typography>
                </Paper>
              )}
            </Stack>
          )}
          {tab === 3 && analysis.knowledge_graph && (
            <KnowledgeGraphViz data={analysis.knowledge_graph} />
          )}
          {tab === 3 && !analysis.knowledge_graph && (
            <Box>
              <Typography variant="h6" gutterBottom>Knowledge Graph</Typography>
              <Typography>No knowledge graph data available for this paper.</Typography>
            </Box>
          )}
        </Paper>
        </Box>
        {paperViewerOpen && isDesktop ? (
          <Box sx={{ position: 'sticky', top: 24, alignSelf: 'start' }}>
            {renderPaperViewer(true)}
          </Box>
        ) : null}
      </Box>
      <Drawer
        anchor="right"
        open={paperViewerOpen && !isDesktop}
        onClose={() => setPaperViewerOpen(false)}
        PaperProps={{ sx: { width: '100%', maxWidth: 960 } }}
      >
        {renderPaperViewer(false)}
      </Drawer>
      <Snackbar
        open={completionNoticeOpen}
        autoHideDuration={6000}
        onClose={() => setCompletionNoticeOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setCompletionNoticeOpen(false)}
          severity="success"
          variant="filled"
          sx={{ width: '100%' }}
        >
          {analysis.title ? `Analysis ready: ${analysis.title}` : 'Paper analysis is ready.'}
        </Alert>
      </Snackbar>
    </Container>
  );
};
