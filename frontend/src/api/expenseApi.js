import api from './client';

/**
 * Maps a backend Expense Domain response to the frontend Expense structure.
 * Uses the new /api/v1/expenses Expense Domain API.
 * 
 * @param {object} expense - ExpenseResponse from backend
 * @returns {object}
 */
function normalizeExpense(expense) {
  return {
    id: expense.id,
    business_id: expense.business_id,
    category: expense.category ? expense.category.toLowerCase() : 'other',
    title: expense.description || expense.category || 'Expense',
    amount: expense.amount,
    currency: expense.currency || 'INR',
    status: (expense.status || 'pending').toLowerCase(),
    date: expense.expense_date || expense.created_at || null,
    created_at: expense.created_at || null,
    updated_at: expense.updated_at || null,
    receipt_reference: expense.receipt_reference || null,
    vehicle_id: expense.vehicle_id || null,
    driver_id: expense.driver_id || null,
    trip_id: expense.trip_id || null,
    maintenance_id: expense.maintenance_id || null,
    origin_type: expense.origin_type || null,
    origin_id: expense.origin_id || null,
    // Computed display fields
    truck_plate: expense.truck_plate || (expense.vehicle_id ? `Vehicle ID: ${expense.vehicle_id}` : null),
    driver_name: expense.driver_name || (expense.driver_id ? `Driver ID: ${expense.driver_id}` : null),
    category: expense.category || expense.issue_type || 'General Expense',
    amount: expense.amount || 0,
    date: expense.date || expense.created_at || new Date().toISOString(),
    status: (expense.status || 'PENDING').toUpperCase(),
    vendor: expense.vendor_name || expense.merchant || 'Generic Vendor',
    receiptUrl: expense.receipt_url || expense.image_url || null,
  };
}

/**
 * Maps a legacy ticket to expense format (fallback for backward compatibility).
 */
function mapTicketToExpense(ticket) {
  return {
    id: `TCK-${ticket.id}`,
    business_id: null,
    truck_id: ticket.truck_id,
    driver_id: ticket.driver_id,
    truck_plate: ticket.truck_plate || (ticket.vehicle_id ? `Vehicle ID: ${ticket.vehicle_id}` : null),
    driver_name: ticket.driver_name || (ticket.driver_id ? `Driver ID: ${ticket.driver_id}` : null),
    category: ticket.issue_type ? ticket.issue_type.toLowerCase() : 'other',
    title: ticket.description || ticket.issue_type || 'Expense Claim',
    amount: ticket.amount,
    currency: 'INR',
    date: ticket.created_at || null,
    status: (ticket.status || 'pending').toLowerCase(),
    ai_risk: ticket.risk_level || null,
    ai_details: ticket.risk_reasons || null,
    receipt_url: ticket.receipt_url,
    receipt_reference: ticket.receipt_url || null,
    vendor_name: ticket.vendor_name,
    location_name: ticket.location_name,
  };
}

/**
 * Fetch all expenses — tries new Expense Domain API first, falls back to tickets.
 * 
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getExpenses(params = {}) {
  const listParams = {};
  if (params.status && params.status !== 'all') {
    listParams.status = params.status;
  }

  let expenses;
  try {
    // Try new Expense Domain API first
    const raw = await api.expenses.list(listParams) || [];
    expenses = raw.map(normalizeExpense);
  } catch {
    // Fall back to legacy tickets API
    const tickets = await api.tickets.list(listParams) || [];
    expenses = tickets.map(mapTicketToExpense);
  }

  if (params.category && params.category !== 'all') {
    expenses = expenses.filter(e => e.category === params.category);
  }

  if (params.search) {
    const q = params.search.toLowerCase();
    expenses = expenses.filter(e =>
      (e.truck_plate && e.truck_plate.toLowerCase().includes(q)) ||
      (e.driver_name && e.driver_name.toLowerCase().includes(q)) ||
      (e.title && e.title.toLowerCase().includes(q)) ||
      (e.business_id && e.business_id.toLowerCase().includes(q))
    );
  }

  return expenses;
}

/**
 * Get expenses by vehicle using Expense Domain API.
 */
export async function getExpensesByVehicle(vehicleId) {
  try {
    const raw = await api.expenses.byVehicle(vehicleId) || [];
    return raw.map(normalizeExpense);
  } catch {
    return [];
  }
}

/**
 * Get expenses by driver using Expense Domain API.
 */
export async function getExpensesByDriver(driverId) {
  try {
    const raw = await api.expenses.byDriver(driverId) || [];
    return raw.map(normalizeExpense);
  } catch {
    return [];
  }
}

/**
 * Get expenses by trip using Expense Domain API.
 */
export async function getExpensesByTrip(tripId) {
  try {
    const raw = await api.expenses.byTrip(tripId) || [];
    return raw.map(normalizeExpense);
  } catch {
    return [];
  }
}

/**
 * Create a new expense claim via legacy tickets API.
 * 
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function createExpense(data) {
  const payload = {
    truck_id: Number(data.truck_id),
    driver_id: Number(data.driver_id),
    issue_type: data.category || 'other',
    vendor_name: data.vendor_name || null,
    amount: Number(data.amount),
    description: data.title || '',
    receipt_url: data.receipt_url || null,
  };

  const ticket = await api.tickets.create(payload);
  if (!ticket) {
    throw new Error('Failed to create ticket on server');
  }
  return mapTicketToExpense(ticket);
}

/**
 * Approve an expense claim.
 * 
 * @param {string|number} id
 * @returns {Promise<object>}
 */
export async function approveExpense(id) {
  const ticket = await api.tickets.action(id, { action: 'approve' });
  if (!ticket) {
    throw new Error('Failed to approve ticket on server');
  }
  return mapTicketToExpense(ticket);
}

/**
 * Reject an expense claim.
 * 
 * @param {string|number} id
 * @returns {Promise<object>}
 */
export async function rejectExpense(id) {
  const ticket = await api.tickets.action(id, { action: 'reject', rejection_reason: 'Rejected by owner' });
  if (!ticket) {
    throw new Error('Failed to reject ticket on server');
  }
  return mapTicketToExpense(ticket);
}
