import React from 'react';
import { Routes, Route } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import DashboardOverview from './DashboardOverview';
import Reports from './Reports';
import Vehicles from './vehicles/Vehicles';
import Drivers from './drivers/Drivers';
import Trips from './trips/Trips';
import Fuel from './fuel/Fuel';
import Expenses from './expenses/Expenses';
import Payments from './payments/Payments';
import Maintenance from './maintenance/Maintenance';
import Documents from './documents/Documents';
import Alerts from './alerts/Alerts';
import Notifications from './notifications/Notifications';
import Profile from './Profile';
import Settings from './Settings';
import UserManagement from './admin/UserManagement';
import RolesPermissions from './admin/RolesPermissions';
import AuditLogs from './admin/AuditLogs';

export default function Dashboard() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardOverview />} />
        <Route path="reports" element={<Reports />} />
        <Route path="vehicles/*" element={<Vehicles />} />
        <Route path="drivers/*" element={<Drivers />} />
        <Route path="trips/*" element={<Trips />} />
        <Route path="fuel/*" element={<Fuel />} />
        <Route path="expenses/*" element={<Expenses />} />
        <Route path="payments/*" element={<Payments />} />
        <Route path="maintenance/*" element={<Maintenance />} />
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
  );
}
