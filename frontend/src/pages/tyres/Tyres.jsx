import React from 'react';
import { Routes, Route } from 'react-router-dom';
import TyreList from './TyreList';

export default function Tyres() {
  return (
    <Routes>
      <Route index element={<TyreList />} />
    </Routes>
  );
}
