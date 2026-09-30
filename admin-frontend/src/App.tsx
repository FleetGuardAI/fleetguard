import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import SupportTickets from './pages/SupportTickets';
import PasswordResets from './pages/PasswordResets';
import DocumentVerification from './pages/DocumentVerification';
import AuditLogs from './pages/AuditLogs';

import type { ReactElement } from 'react';

function ProtectedRoute({ children }: { children: ReactElement }) {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="tickets" element={<SupportTickets />} />
            <Route path="password-resets" element={<PasswordResets />} />
            <Route path="documents" element={<DocumentVerification />} />
            <Route path="audit-logs" element={<AuditLogs />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
