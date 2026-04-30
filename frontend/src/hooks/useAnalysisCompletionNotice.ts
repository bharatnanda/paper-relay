import { useEffect, useRef, useState } from 'react';
import { PaperAnalysis } from '../types';

export const useAnalysisCompletionNotice = (
  paperId: string | undefined,
  analysis: PaperAnalysis | null,
) => {
  const [completionNoticeOpen, setCompletionNoticeOpen] = useState(false);
  const previousStatusRef = useRef<PaperAnalysis['status'] | null>(null);

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
        notification.onclick = () => {
          window.focus();
          notification.close();
        };
      }
    }

    if (analysis.status === 'failed') sessionStorage.removeItem(watchKey);
    previousStatusRef.current = analysis.status;
  }, [analysis, paperId]);

  return {
    completionNoticeOpen,
    closeCompletionNotice: () => setCompletionNoticeOpen(false),
  };
};
