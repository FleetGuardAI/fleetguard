import api from './client';

/**
 * Fetch recorded payments/payouts from backend expense tickets API.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getPayments(params = {}) {
  let tickets = [];
  try {
    tickets = await api.tickets.list() || [];
  } catch {
    tickets = [];
  }

  let payments = tickets.map(t => {
    let s = (t.status || 'pending').toLowerCase();
    if (s === 'approved' || s === 'resolved') s = 'completed';
    if (s === 'open') s = 'pending';

    return {
      id: `PAY-${t.id}`,
      recipient_name: t.driver_name || t.vendor_name || (t.driver_id ? `Driver ID: ${t.driver_id}` : 'Unknown'),
      truck_plate: t.truck_plate || (t.truck_id ? `Vehicle ID: ${t.truck_id}` : 'Unassigned'),
      category: t.issue_type || 'Expense Claim',
      amount: t.amount || 0,
      method: t.method || 'Unknown',
      date: t.updated_at || t.created_at || new Date().toISOString(),
      status: s,
      ref_num: s === 'completed' ? `TXN-${100000 + t.id}` : null,
    };
  });

  if (params.search) {
    const q = params.search.toLowerCase();
    payments = payments.filter(p =>
      p.recipient_name.toLowerCase().includes(q) ||
      p.id.toLowerCase().includes(q) ||
      p.truck_plate.toLowerCase().includes(q)
    );
  }

  return payments;
}

/**
 * Record a new payout via expense ticket creation.
 *
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function recordPayout(data) {
  const ticket = await api.tickets.create({
    truck_id: Number(data.truck_id || 1),
    driver_id: Number(data.driver_id || 1),
    issue_type: data.category || 'other',
    vendor_name: data.recipient_name || 'Generic Vendor',
    amount: Number(data.amount || 0),
    description: data.notes || 'Manual payout recorded',
  });

  return {
    id: `PAY-${ticket.id}`,
    date: new Date().toISOString(),
    status: 'completed',
    ref_num: `TXN-${Date.now()}`,
    ...data
  };
}

/**
 * Settle a payout by approving the underlying ticket.
 *
 * @param {string} payoutId - The payout ID (e.g. "PAY-123")
 * @returns {Promise<object>}
 */
export async function settlePayout(payoutId) {
  // Extract ticket ID from PAY-xxx format
  const ticketId = payoutId.startsWith('PAY-') ? payoutId.split('-')[1] : payoutId;
  
  const result = await api.tickets.action(ticketId, { 
    action: 'approve', 
    notes: 'Settled via Payout module' 
  });
  
  return result;
}
