import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppErrorInfo, getApiErrorInfo, papersAPI } from '../services/api';
import { PaperAnalysis, User } from '../types';

interface UsePaperAnalysisResult {
  analysis: PaperAnalysis | null;
  displaySummary: PaperAnalysis['summary'];
  setDisplaySummary: React.Dispatch<React.SetStateAction<PaperAnalysis['summary']>>;
  loading: boolean;
  error: AppErrorInfo | null;
  reload: () => void;
}

export const usePaperAnalysis = (
  paperId: string | undefined,
  user: User | null,
): UsePaperAnalysisResult => {
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [displaySummary, setDisplaySummary] = useState<PaperAnalysis['summary']>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppErrorInfo | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

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
        setDisplaySummary(result.summary);
        setError(null);
        if (result.status === 'processing' || result.status === 'pending') {
          timeoutId = setTimeout(fetchAnalysis, 3000);
        }
      } catch (err: unknown) {
        if (!mounted) return;
        setError(getApiErrorInfo(err, 'Failed to load the paper analysis.'));
      } finally {
        if (mounted) setLoading(false);
      }
    };

    setLoading(true);
    fetchAnalysis();

    return () => {
      mounted = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [paperId, user, navigate, reloadKey]);

  return {
    analysis,
    displaySummary,
    setDisplaySummary,
    loading,
    error,
    reload: () => {
      setLoading(true);
      setError(null);
      setReloadKey((value) => value + 1);
    },
  };
};
