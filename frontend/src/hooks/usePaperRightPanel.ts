import { useState } from 'react';

export type RightPanel = 'paper' | 'chat' | null;

export const usePaperRightPanel = () => {
  const [rightPanel, setRightPanel] = useState<RightPanel>(null);

  return {
    rightPanel,
    setRightPanel,
    closeRightPanel: () => setRightPanel(null),
  };
};
