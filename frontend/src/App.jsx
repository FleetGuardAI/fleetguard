import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import Dashboard from './pages/Dashboard';
import HomePage from './pages/HomePage';
import Downloads from './pages/Downloads';

/**
 * FleetGuard Application Root
 * Routes:
 *   /            → Marketing landing page
 *   /login       → Authentication page
 *   /register    → Company and admin registration page
 *   /forgot-password → Password reset request/reset page
 *   /downloads       → Downloads page for mobile apps
 *   /homepage    → Migrated RoutePay landing page (temporary)
 *   /dashboard   → Owner BI Dashboard
 *   /dashboard/* → Dashboard sub-routes (catch-all for sidebar nav)
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/downloads" element={<Downloads />} />
      <Route path="/homepage" element={<HomePage />} />
      <Route path="/dashboard/*" element={<Dashboard />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
