import { useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { papersAPI } from '../services/api';
import { PaperAnalysis, User } from '../types';

export type ReadingLevel = 'general' | 'technical' | 'eli5';

interface UsePaperReadingLevelParams {
  paperId: string | undefined;
  user: User | null;
  analysis: PaperAnalysis | null;
  setDisplaySummary: Dispatch<SetStateAction<PaperAnalysis['summary']>>;
}

export const usePaperReadingLevel = ({
  paperId,
  user,
  analysis,
  setDisplaySummary,
}: UsePaperReadingLevelParams) => {
  const [readingLevel, setReadingLevel] = useState<ReadingLevel>('general');
  const [reformatError, setReformatError] = useState(false);

  const handleReadingLevelChange = async (level: ReadingLevel) => {
    setReadingLevel(level);

    if (level === 'general') {
      setDisplaySummary(analysis?.summary);
      return;
    }

    if (!paperId || !user) {
      return;
    }

    try {
      const { reformatted_fields } = await papersAPI.reformat(paperId, level, user.token);
      setDisplaySummary((prev) => (prev ? { ...prev, ...reformatted_fields } : prev));
    } catch {
      setReformatError(true);
      setReadingLevel('general');
      setDisplaySummary(analysis?.summary);
    }
  };

  return {
    readingLevel,
    reformatError,
    closeReformatError: () => setReformatError(false),
    handleReadingLevelChange,
  };
};
