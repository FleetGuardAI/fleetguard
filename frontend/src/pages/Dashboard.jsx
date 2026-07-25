import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import DashboardOverview from './DashboardOverview';
import { Loader } from '@/components/ui/Loader';

const Reports = lazy(() => import('./reports/Reports'));
const Vehicles = lazy(() => import('./vehicles/Vehicles'));
const Drivers = lazy(() => import('./drivers/Drivers'));
const Trips = lazy(() => import('./trips/Trips'));
const Fuel = lazy(() => import('./fuel/Fuel'));
const Expenses = lazy(() => import('./expenses/Expenses'));
const Payments = lazy(() => import('./payments/Payments'));
const Maintenance = lazy(() => import('./maintenance/Maintenance'));
const Tyres = lazy(() => import('./tyres/Tyres'));
const Assets = lazy(() => import('./assets/Assets'));
const Documents = lazy(() => import('./documents/Documents'));
const Alerts = lazy(() => import('./alerts/Alerts'));
const Notifications = lazy(() => import('./notifications/Notifications'));
const Profile = lazy(() => import('./Profile'));
const Settings = lazy(() => import('./settings/Settings'));
const UserManagement = lazy(() => import('./admin/UserManagement'));
const RolesPermissions = lazy(() => import('./admin/RolesPermissions'));
const AuditLogs = lazy(() => import('./admin/AuditLogs'));
const OpportunityFeedPage = lazy(() => import('./opportunities/OpportunityFeedPage'));

function RouteLoader() {
  return (
    <div className="flex items-center justify-center py-24 min-h-[400px]">
      <Loader size="lg" />
    </div>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={<RouteLoader />}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardOverview />} />
          <Route path="opportunities" element={<OpportunityFeedPage />} />
          <Route path="reports" element={<Reports />} />
          <Route path="vehicles/*" element={<Vehicles />} />
          <Route path="drivers/*" element={<Drivers />} />
          <Route path="trips/*" element={<Trips />} />
          <Route path="fuel/*" element={<Fuel />} />
          <Route path="expenses/*" element={<Expenses />} />
          <Route path="payments/*" element={<Payments />} />
          <Route path="maintenance/*" element={<Maintenance />} />
          <Route path="tyres/*" element={<Tyres />} />
          <Route path="assets/*" element={<Assets />} />
          <Route path="documents/*" element={<Documents />} />
          <Route path="alerts/*" element={<Alerts />} />
          <Route path="notifications/*" element={<Notifications />} />
          <Route path="profile/*" element={<Profile />} />
          <Route path="settings/*" element={<Settings />} />
          <Route path="admin/users/*" element={<UserManagement />} />
          <Route path="admin/roles/*" element={<RolesPermissions />} />
          <Route path="admin/audit/*" element={<AuditLogs />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
