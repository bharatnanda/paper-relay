import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { PaperPage } from './pages/PaperPage';
import { LibraryPage } from './pages/LibraryPage';
import { SharedPaperPage } from './pages/SharedPaperPage';
import { LoginPage } from './pages/LoginPage';
import { AppShell } from './components/layout/AppShell';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/paper/:paperId" element={<PaperPage />} />
          <Route path="/library" element={<LibraryPage />} />
          <Route path="/share/:shareToken" element={<SharedPaperPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
};
