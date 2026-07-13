import React from 'react';
import { Routes, Route } from 'react-router-dom';
import FuelDashboard from './FuelDashboard';
import FuelForm from './FuelForm';

export default function Fuel() {
  return (
    <Routes>
      <Route index element={<FuelDashboard />} />
      <Route path="new" element={<FuelForm />} />
    </Routes>
  );
}
