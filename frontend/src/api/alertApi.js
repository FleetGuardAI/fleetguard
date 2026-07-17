import { mockAlerts } from '@/data/mockData';

let localAlerts = [...mockAlerts];

export async function getAlerts(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localAlerts];

      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(a =>
          a.truck_plate.toLowerCase().includes(q) ||
          a.type.toLowerCase().includes(q) ||
          a.message.toLowerCase().includes(q)
        );
      }

      if (params.severity) {
        filtered = filtered.filter(a => a.level === params.severity);
      }

      if (params.resolved !== undefined) {
        filtered = filtered.filter(a => a.resolved === params.resolved);
      }

      // Map level -> severity in view if needed, or unify
      const normalized = filtered.map(a => ({
        ...a,
        severity: a.level // map level field to severity for consistent naming
      }));

      resolve(normalized);
    }, 400);
  });
}

export async function resolveAlert(id, comment) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const idx = localAlerts.findIndex(a => String(a.id) === String(id));
      if (idx !== -1) {
        localAlerts[idx] = {
          ...localAlerts[idx],
          resolved: true,
          resolutionComment: comment,
          resolved_by: 'Suryansh Chaudhary',
          resolved_at: new Date().toISOString()
        };
        resolve({
          ...localAlerts[idx],
          severity: localAlerts[idx].level
        });
      } else {
        reject(new Error('Alert not found'));
      }
    }, 400);
  });
}
