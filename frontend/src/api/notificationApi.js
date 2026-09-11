import api from './client';

/**
 * Notification field mapping:
 *
 * Backend returns:  is_read, category, description, created_at
 * Frontend uses:    read,    type,     message,     date
 *
 * Normalization is done here so the UI can use its preferred field names
 * without coupling to the backend schema.
 */

/**
 * Map backend category values to frontend type keys used for icons/styles.
 */
const CATEGORY_TO_TYPE = {
  ALERT: 'ALERT',
  TRIP: 'TRIP',
  VEHICLE: 'VEHICLE',
  FINANCE: 'FINANCE',
  SYSTEM: 'SYSTEM',
};

function normalizeNotification(n) {
  return {
    id: n.id,
    title: n.title,
    message: n.description,
    type: CATEGORY_TO_TYPE[n.category] || n.category || 'SYSTEM',
    date: n.created_at || null,
    read: n.is_read ?? false,
  };
}

/**
 * Fetch notifications from the real backend notification endpoint.
 *
 * @param {object} params - Optional filters: search, type, read
 * @returns {Promise<Array>}
 */
export async function getNotifications(params = {}) {
  let notifications = [];
  try {
    const raw = await api.get('/api/v1/notifications') || [];
    notifications = raw.map(normalizeNotification);
  } catch {
    notifications = [];
  }

  if (params.search) {
    const q = params.search.toLowerCase();
    notifications = notifications.filter(n =>
      n.title.toLowerCase().includes(q) ||
      n.message.toLowerCase().includes(q)
    );
  }

  if (params.type && params.type !== 'all') {
    notifications = notifications.filter(n => n.type === params.type);
  }

  if (params.read !== undefined) {
    notifications = notifications.filter(n => n.read === params.read);
  }

  return notifications;
}

/**
 * Mark a single notification as read.
 * @param {number} id
 */
export async function markNotificationRead(id) {
  return await api.put(`/api/v1/notifications/${id}/read`);
}

/**
 * Mark all notifications as read.
 */
export async function markAllNotificationsRead() {
  return await api.put('/api/v1/notifications/read-all');
}

/**
 * Delete a single notification.
 * @param {number} id
 */
export async function deleteNotification(id) {
  return await api.delete(`/api/v1/notifications/${id}`);
}
