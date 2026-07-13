import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import HomePage from './pages/HomePage';

/**
 * FleetGuard Application Root
 * Routes:
 *   /            → Marketing landing page
 *   /homepage    → Migrated RoutePay landing page (temporary)
 *   /dashboard   → Owner BI Dashboard
 *   /dashboard/* → Dashboard sub-routes (catch-all for sidebar nav)
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/homepage" element={<HomePage />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/dashboard/*" element={<Dashboard />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
