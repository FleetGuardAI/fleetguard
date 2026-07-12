import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';

/**
 * FleetGuard Application Root
 * Routes:
 *   /            → Marketing landing page
 *   /dashboard   → Owner BI Dashboard
 *   /dashboard/* → Dashboard sub-routes (catch-all for sidebar nav)
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/dashboard/*" element={<Dashboard />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
