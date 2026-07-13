import { mockNotifications } from '@/data/mockData';

let localNotifications = [...mockNotifications];

export async function getNotifications(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localNotifications];

      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(n =>
          n.title.toLowerCase().includes(q) ||
          n.message.toLowerCase().includes(q)
        );
      }

      if (params.type && params.type !== 'all') {
        filtered = filtered.filter(n => n.type === params.type);
      }

      if (params.read !== undefined) {
        filtered = filtered.filter(n => n.read === params.read);
      }

      resolve(filtered);
    }, 300);
  });
}

export async function markNotificationRead(id) {
  return new Promise((resolve) => {
    setTimeout(() => {
      localNotifications = localNotifications.map(n =>
        n.id === Number(id) ? { ...n, read: true } : n
      );
      resolve(true);
    }, 200);
  });
}

export async function markAllNotificationsRead() {
  return new Promise((resolve) => {
    setTimeout(() => {
      localNotifications = localNotifications.map(n => ({ ...n, read: true }));
      resolve(true);
    }, 300);
  });
}

export async function deleteNotification(id) {
  return new Promise((resolve) => {
    setTimeout(() => {
      localNotifications = localNotifications.filter(n => n.id !== Number(id));
      resolve(true);
    }, 200);
  });
}
