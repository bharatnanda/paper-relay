import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Box, Container } from '@mui/material';
import { AppShell } from './components/layout/AppShell';
import { LoadingSpinner } from './components/common/LoadingSpinner';

const HomePage = lazy(() => import('./pages/HomePage').then((module) => ({ default: module.HomePage })));
const PaperPage = lazy(() => import('./pages/PaperPage').then((module) => ({ default: module.PaperPage })));
const LibraryPage = lazy(() => import('./pages/LibraryPage').then((module) => ({ default: module.LibraryPage })));
const SharedPaperPage = lazy(() => import('./pages/SharedPaperPage').then((module) => ({ default: module.SharedPaperPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then((module) => ({ default: module.LoginPage })));

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppShell>
        <Suspense
          fallback={
            <Container maxWidth="md">
              <Box sx={{ mt: 8 }}>
                <LoadingSpinner message="Loading page..." />
              </Box>
            </Container>
          }
        >
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/paper/:paperId" element={<PaperPage />} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/share/:shareToken" element={<SharedPaperPage />} />
          </Routes>
        </Suspense>
      </AppShell>
    </BrowserRouter>
  );
};
