import React from 'react';
import { Routes, Route } from 'react-router-dom';
import VehicleList from './VehicleList';
import VehicleDetail from './VehicleDetail';
import VehicleForm from './VehicleForm';

export default function Vehicles() {
  return (
    <Routes>
      <Route index element={<VehicleList />} />
      <Route path="new" element={<VehicleForm />} />
      <Route path=":id" element={<VehicleDetail />} />
      <Route path=":id/edit" element={<VehicleForm />} />
    </Routes>
  );
}
