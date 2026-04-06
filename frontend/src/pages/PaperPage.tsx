// frontend/src/pages/PaperPage.tsx
import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Button, Container, Drawer, Paper, Snackbar, Alert,
  Stack, Tab, Tabs, Typography, useMediaQuery,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import OpenInNewRoundedIcon from '@mui/icons-material/OpenInNewRounded';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import { useAuth } from '../hooks/useAuth';
import { AppErrorInfo, getApiErrorInfo, papersAPI } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { ProcessingProgress } from '../components/common/ProcessingProgress';
import { WorkspaceHeader } from '../components/paper/WorkspaceHeader';
import { PaperAtAGlance } from '../components/paper/PaperAtAGlance';
import { AnatomyView } from '../components/paper/anatomy/AnatomyView';
import { ChatPanel } from '../components/paper/ChatPanel';
import { KnowledgeGraphViz } from '../components/paper/KnowledgeGraphViz';
import { TermGlossary } from '../components/paper/TermGlossary';
import { FormulaBlock } from '../components/paper/FormulaBlock';
import { PaperAnalysis, FormulaExplanation } from '../types';

type ReadingLevel = 'general' | 'technical' | 'eli5';
type RightPanel = 'paper' | 'chat' | null;

const getProcessingFailureHint = (errorMessage?: string) => {
  const normalized = errorMessage?.toLowerCase() || '';
  if (normalized.includes('download pdf'))
    return 'PaperRelay could not download the PDF from arXiv. Retry in a moment, or confirm that the paper PDF is publicly accessible.';
  if (normalized.includes('parsing'))
    return 'The PDF was found but could not be parsed cleanly. Retrying may help for transient extraction issues.';
  if (normalized.includes('ai processing') || normalized.includes('service unavailable') || normalized.includes('timeout'))
    return 'The paper was fetched, but the analysis step could not finish. Retry after the upstream service recovers.';
  return 'Retry the analysis. If the same paper keeps failing, inspect the backend and worker logs.';
};

export const PaperPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [displaySummary, setDisplaySummary] = useState<PaperAnalysis['summary']>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppErrorInfo | null>(null);
  const [tab, setTab] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [readingLevel, setReadingLevel] = useState<ReadingLevel>('general');
  const [rightPanel, setRightPanel] = useState<RightPanel>(null);
  const [reformatError, setReformatError] = useState(false);
  const [completionNoticeOpen, setCompletionNoticeOpen] = useState(false);
  const previousStatusRef = useRef<PaperAnalysis['status'] | null>(null);

  // Fetch + poll
  useEffect(() => {
    if (!user || !paperId) { navigate('/'); return; }
    let mounted = true;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const fetchAnalysis = async () => {
      try {
        const result = await papersAPI.getAnalysis(paperId, user.token);
        if (!mounted) return;
        setAnalysis(result);
        setDisplaySummary(result.summary);
        setError(null);
        if (result.status === 'processing' || result.status === 'pending')
          timeoutId = setTimeout(fetchAnalysis, 3000);
      } catch (err: any) {
        if (!mounted) return;
        setError(getApiErrorInfo(err, 'Failed to load the paper analysis.'));
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchAnalysis();
    return () => { mounted = false; if (timeoutId) clearTimeout(timeoutId); };
  }, [paperId, user, navigate, reloadKey]);

  // Completion notification
  useEffect(() => {
    if (!paperId || !analysis) return;
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
        notification.onclick = () => { window.focus(); notification.close(); };
      }
    }
    if (analysis.status === 'failed') sessionStorage.removeItem(watchKey);
    previousStatusRef.current = analysis.status;
  }, [analysis, paperId]);

  // Reading level change — calls reformat, merges fields into displaySummary
  const handleReadingLevelChange = async (level: ReadingLevel) => {
    setReadingLevel(level);
    if (level === 'general') {
      setDisplaySummary(analysis?.summary);
      return;
    }
    if (!paperId || !user) return;
    try {
      const { reformatted_fields } = await papersAPI.reformat(paperId, level, user.token);
      setDisplaySummary((prev) => prev ? { ...prev, ...reformatted_fields } : prev);
    } catch {
      setReformatError(true);
      setReadingLevel('general');
      setDisplaySummary(analysis?.summary);
    }
  };

  const handleRightPanelChange = (panel: RightPanel) => setRightPanel(panel);

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
                <Button variant="contained" onClick={() => { setLoading(true); setError(null); setReloadKey((v) => v + 1); }}>Retry</Button>
                <Button variant="outlined" onClick={() => navigate('/library')}>Back to library</Button>
              </Stack>
            }
          />
        </Box>
      </Container>
    );
  }

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
                <Button variant="contained" onClick={() => navigate('/')}>Analyze another paper</Button>
                <Button variant="outlined" onClick={() => setReloadKey((v) => v + 1)}>Refresh status</Button>
              </Stack>
            ) : undefined}
          />
        </Box>
      </Container>
    );
  }

  const originalPaperUrl = analysis.pdf_url || (analysis.arxiv_id ? `https://arxiv.org/pdf/${analysis.arxiv_id}.pdf` : '');
  const isMathHeavy = analysis.summary?.paper_map?.math_relevance === 'heavy';

  const renderPaperViewer = (embedded: boolean) => (
    <Paper sx={{ p: { xs: 2, md: 2.5 }, borderRadius: embedded ? 6 : 0, display: 'flex', flexDirection: 'column', height: embedded ? 'calc(100vh - 168px)' : '100%', minHeight: embedded ? 680 : '100vh', boxShadow: embedded ? undefined : 'none' }}>
      <Stack spacing={2} sx={{ height: '100%' }}>
        <Stack direction="row" spacing={1.25} justifyContent="space-between" alignItems="flex-start">
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="overline" color="text.secondary">Original paper</Typography>
            <Typography variant="h6">Source PDF</Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            {originalPaperUrl && (
              <Button size="small" variant="outlined" endIcon={<OpenInNewRoundedIcon />} component="a" href={originalPaperUrl} target="_blank" rel="noreferrer">Open</Button>
            )}
            {!embedded && (
              <Button size="small" variant="text" startIcon={<CloseRoundedIcon />} onClick={() => setRightPanel(null)}>Close</Button>
            )}
          </Stack>
        </Stack>
        <Box sx={{ flex: 1, minHeight: 0, overflow: 'hidden', borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
          {originalPaperUrl ? (
            <Box component="iframe" src={originalPaperUrl} title={analysis.title || 'Original paper PDF'} sx={{ width: '100%', height: '100%', minHeight: embedded ? 560 : '100vh', border: 0 }} />
          ) : (
            <Stack spacing={2} justifyContent="center" alignItems="flex-start" sx={{ p: 3, height: '100%' }}>
              <Typography>No source PDF URL is available for this paper.</Typography>
            </Stack>
          )}
        </Box>
      </Stack>
    </Paper>
  );

  const renderRightPanel = () => {
    if (rightPanel === 'paper') return renderPaperViewer(true);
    if (rightPanel === 'chat') return (
      <ChatPanel paperId={paperId!} token={user!.token} onClose={() => setRightPanel(null)} />
    );
    return null;
  };

  const showRightColumn = rightPanel !== null && isDesktop;

  return (
    <Container maxWidth={showRightColumn ? 'xl' : 'lg'}>
      <Box sx={{ display: 'grid', gap: 3, gridTemplateColumns: showRightColumn ? 'minmax(0, 1.45fr) minmax(360px, 0.9fr)' : 'minmax(0, 1fr)', alignItems: 'start' }}>
        <Box sx={{ display: 'grid', gap: 3, minWidth: 0 }}>

          <WorkspaceHeader
            readingLevel={readingLevel}
            onReadingLevelChange={handleReadingLevelChange}
            rightPanel={rightPanel}
            onRightPanelChange={handleRightPanelChange}
            hasPaperUrl={!!originalPaperUrl}
          />

          <Paper sx={{ p: { xs: 3, md: 4 }, borderRadius: 6 }}>
            {analysis.summary?.paper_map && (
              <Box sx={{ mb: 3 }}>
                <PaperAtAGlance
                  paperMap={analysis.summary.paper_map}
                  critique={analysis.summary.critique}
                />
              </Box>
            )}

            <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
              <Tab label="Anatomy" />
              {isMathHeavy && <Tab label="Math" />}
              <Tab label="Knowledge Graph" />
            </Tabs>

            {/* Anatomy tab */}
            {tab === 0 && displaySummary && (
              <AnatomyView summary={displaySummary!} />
            )}

            {/* Math tab — only shown when math_relevance === 'heavy' */}
            {isMathHeavy && tab === 1 && displaySummary && (
              <Stack spacing={2}>
                <Typography variant="h5">Formula explanations</Typography>
                {displaySummary.formula_explanations?.length ? (
                  displaySummary.formula_explanations.map((f: FormulaExplanation, i: number) => (
                    <Paper key={f.latex || i} sx={{ p: 2.5, borderRadius: 5 }}>
                      <FormulaBlock formula={f} />
                    </Paper>
                  ))
                ) : (
                  <Paper sx={{ p: 3, borderRadius: 5 }}>
                    <Typography color="text.secondary">No equation-level explanation was recovered for this paper.</Typography>
                  </Paper>
                )}
              </Stack>
            )}

            {/* Knowledge Graph tab — index depends on whether Math tab is shown */}
            {tab === (isMathHeavy ? 2 : 1) && (
              <>
                {analysis.knowledge_graph ? (
                  <Stack spacing={3}>
                    <KnowledgeGraphViz data={analysis.knowledge_graph} />
                    {analysis.summary?.terms?.length ? (
                      <TermGlossary terms={analysis.summary.terms} />
                    ) : null}
                  </Stack>
                ) : (
                  <Typography>No knowledge graph data available for this paper.</Typography>
                )}
              </>
            )}
          </Paper>
        </Box>

        {showRightColumn && (
          <Box sx={{ position: 'sticky', top: 24, alignSelf: 'start' }}>
            {renderRightPanel()}
          </Box>
        )}
      </Box>

      {/* Mobile drawer for right panels */}
      <Drawer
        anchor="right"
        open={rightPanel !== null && !isDesktop}
        onClose={() => setRightPanel(null)}
        PaperProps={{ sx: { width: '100%', maxWidth: 960 } }}
      >
        {renderRightPanel()}
      </Drawer>

      <Snackbar open={reformatError} autoHideDuration={5000} onClose={() => setReformatError(false)} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert severity="error" variant="filled" onClose={() => setReformatError(false)}>
          Could not reformat the paper. Reverted to General view.
        </Alert>
      </Snackbar>

      <Snackbar open={completionNoticeOpen} autoHideDuration={6000} onClose={() => setCompletionNoticeOpen(false)} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert onClose={() => setCompletionNoticeOpen(false)} severity="success" variant="filled" sx={{ width: '100%' }}>
          {analysis.title ? `Analysis ready: ${analysis.title}` : 'Paper analysis is ready.'}
        </Alert>
      </Snackbar>
    </Container>
  );
};
