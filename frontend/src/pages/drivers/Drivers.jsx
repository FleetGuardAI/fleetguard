import React from 'react';
import { Routes, Route } from 'react-router-dom';
import DriverList from './DriverList';
import DriverProfile from './DriverProfile';
import DriverForm from './DriverForm';

export default function Drivers() {
  return (
    <Routes>
      <Route index element={<DriverList />} />
      <Route path="new" element={<DriverForm />} />
      <Route path=":id" element={<DriverProfile />} />
      <Route path=":id/edit" element={<DriverForm />} />
    </Routes>
  );
}
