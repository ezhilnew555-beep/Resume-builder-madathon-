import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { ResumeUploadPage } from './pages/ResumeUploadPage';
import { ResumeReviewPage } from './pages/ResumeReviewPage';
import { JobMatchPage } from './pages/JobMatchPage';
import { ProfileConnectionsPage } from './pages/ProfileConnectionsPage';
import { ResumeBuilderPage } from './pages/ResumeBuilderPage';
import { LearningRoadmapPage } from './pages/LearningRoadmapPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="upload" element={<ResumeUploadPage />} />
            <Route path="review" element={<ResumeReviewPage />} />
            <Route path="job-match" element={<JobMatchPage />} />
            <Route path="connections" element={<ProfileConnectionsPage />} />
            <Route path="builder" element={<ResumeBuilderPage />} />
            <Route path="roadmap" element={<LearningRoadmapPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
