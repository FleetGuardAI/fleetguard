import React from 'react';
import { Routes, Route } from 'react-router-dom';
import HardwareAssetsDashboard from './HardwareAssetsDashboard';
import DeviceDetails from './DeviceDetails';

export default function Assets() {
  return (
    <Routes>
      <Route index element={<HardwareAssetsDashboard />} />
      <Route path=":id" element={<DeviceDetails />} />
    </Routes>
  );
}
