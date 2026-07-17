import api from './client';

/**
 * Maps a backend TicketResponse object to the frontend Expense structure.
 * 
 * @param {object} ticket
 * @returns {object}
 */
function mapTicketToExpense(ticket) {
  return {
    id: ticket.id,
    truck_id: ticket.truck_id,
    driver_id: ticket.driver_id,
    truck_plate: ticket.truck_plate || `Truck #${ticket.truck_id}`,
    driver_name: ticket.driver_name || `Driver #${ticket.driver_id}`,
    category: ticket.issue_type ? ticket.issue_type.toLowerCase() : 'other',
    title: ticket.description || ticket.issue_type || 'Expense Claim',
    amount: ticket.amount,
    date: ticket.created_at || new Date().toISOString(),
    status: ticket.status || 'pending',
    ai_risk: ticket.risk_level || 'Low',
    ai_details: ticket.risk_reasons || 'No anomalies detected.',
    receipt_url: ticket.receipt_url,
    vendor_name: ticket.vendor_name,
    location_name: ticket.location_name,
  };
}

/**
 * Fetch all expense claims (tickets) from the backend.
 * 
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getExpenses(params = {}) {
  const listParams = {};
  if (params.status && params.status !== 'all') {
    listParams.status = params.status;
  }
  if (params.driver_id) {
    listParams.driver_id = params.driver_id;
  }
  if (params.truck_id) {
    listParams.truck_id = params.truck_id;
  }

  const tickets = await api.tickets.list(listParams) || [];
  let filtered = tickets.map(mapTicketToExpense);

  if (params.category && params.category !== 'all') {
    filtered = filtered.filter(e => e.category === params.category);
  }

  if (params.search) {
    const q = params.search.toLowerCase();
    filtered = filtered.filter(e =>
      (e.truck_plate && e.truck_plate.toLowerCase().includes(q)) ||
      (e.driver_name && e.driver_name.toLowerCase().includes(q)) ||
      (e.title && e.title.toLowerCase().includes(q))
    );
  }

  return filtered;
}

/**
 * Create a new expense claim.
 * 
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function createExpense(data) {
  const payload = {
    truck_id: Number(data.truck_id),
    driver_id: Number(data.driver_id),
    issue_type: data.category || 'other',
    vendor_name: data.vendor_name || 'Generic Vendor',
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
