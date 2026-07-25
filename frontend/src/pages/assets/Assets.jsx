import React from 'react';
import { Routes, Route } from 'react-router-dom';
import AssetList from './AssetList';

export default function Assets() {
  return (
    <Routes>
      <Route index element={<AssetList />} />
    </Routes>
  );
}
