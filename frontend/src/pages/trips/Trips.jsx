import React from 'react';
import { Routes, Route } from 'react-router-dom';
import TripList from './TripList';
import TripDetail from './TripDetail';
import TripForm from './TripForm';
import TripHistoryWorkspace from '../tracking/TripHistoryWorkspace';

export default function Trips() {
  return (
    <Routes>
      <Route index element={<TripList />} />
      <Route path="new" element={<TripForm />} />
      <Route path="history" element={<TripHistoryWorkspace />} />
      <Route path=":id" element={<TripDetail />} />
    </Routes>
  );
}
