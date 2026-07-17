import { mockExpenses } from '@/data/mockData';

let localExpenses = [...mockExpenses];

export async function getExpenses(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localExpenses];
      if (params.category && params.category !== 'all') {
        filtered = filtered.filter(e => e.category === params.category);
      }
      if (params.status && params.status !== 'all') {
        filtered = filtered.filter(e => e.status === params.status);
      }
      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(e =>
          e.truck_plate.toLowerCase().includes(q) ||
          e.driver_name.toLowerCase().includes(q) ||
          e.title.toLowerCase().includes(q)
        );
      }
      resolve(filtered);
    }, 500);
  });
}

export async function createExpense(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newExpense = {
        id: localExpenses.length + 1001,
        date: new Date().toISOString(),
        status: 'pending',
        ai_risk: 'Low',
        ai_details: 'Mock AI check: No anomalies detected on receipt or GPS matching.',
        ...data
      };
      localExpenses.unshift(newExpense);
      resolve(newExpense);
    }, 600);
  });
}

export async function approveExpense(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const expense = localExpenses.find(e => e.id === Number(id));
      if (expense) {
        expense.status = 'approved';
        resolve(expense);
      } else {
        reject(new Error('Expense not found'));
      }
    }, 400);
  });
}

export async function rejectExpense(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const expense = localExpenses.find(e => e.id === Number(id));
      if (expense) {
        expense.status = 'rejected';
        resolve(expense);
      } else {
        reject(new Error('Expense not found'));
      }
    }, 400);
  });
}
