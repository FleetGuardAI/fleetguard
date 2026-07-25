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
    tickets = await api.tickets.list({ status: 'APPROVED' }) || [];
  } catch {
    tickets = [];
  }

  let payments = tickets.map(t => ({
    id: `PAY-${t.id}`,
    recipient_name: t.driver_name || (t.driver_id ? `Driver ID: ${t.driver_id}` : 'Unassigned'),
    truck_plate: t.truck_plate || (t.truck_id ? `Vehicle ID: ${t.truck_id}` : 'Unassigned'),
    category: t.issue_type || 'Expense Claim',
    amount: t.amount,
    date: t.updated_at || t.created_at || new Date().toISOString(),
    status: 'completed',
    ref_num: `TXN-${100000 + t.id}`,
  }));

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
    ref_num: `TXN-${Math.floor(1000000000 + Math.random() * 9000000000)}`,
    ...data
  };
}
