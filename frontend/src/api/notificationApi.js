import api from './client';

/**
 * Fetch system notifications from real backend operational events.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getNotifications(params = {}) {
  let events = [];
  try {
    events = await api.events.list({ limit: 50 }) || [];
  } catch {
    events = [];
  }

  let notifications = events.map(e => {
    let fallbackMsg = `Event ${e.event_type} registered for ${e.entity_type} ${e.entity_id}`;
    if (e.event_type === 'DOCUMENT_UPLOADED') {
      const docType = e.payload?.document_type ? e.payload.document_type.replace(/_/g, ' ') : 'Document';
      fallbackMsg = `Document Uploaded: ${docType}`;
      if (e.payload?.filename) fallbackMsg += ` (${e.payload.filename})`;
    }

    return {
      id: e.id,
      title: e.event_type ? e.event_type.replace(/_/g, ' ').toUpperCase() : 'SYSTEM NOTICE',
      message: e.payload?.description || e.payload?.notes || fallbackMsg,
      type: e.verification_status === 'VERIFIED' ? 'info' : 'warning',
      date: e.occurred_at || e.timestamp || e.created_at || null,
      read: false,
      payload: e.payload,
    };
  });

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

export async function markNotificationRead(id) {
  return { id, read: true };
}

export async function markAllNotificationsRead() {
  return { success: true };
}

export async function deleteNotification(id) {
  return { id, deleted: true };
}
