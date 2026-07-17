import React from 'react';
import { Routes, Route } from 'react-router-dom';
import ExpenseDashboard from './ExpenseDashboard';
import ExpenseForm from './ExpenseForm';

export default function Expenses() {
  return (
    <Routes>
      <Route index element={<ExpenseDashboard />} />
      <Route path="new" element={<ExpenseForm />} />
    </Routes>
  );
}
