import { mockMaintenance } from '@/data/mockData';

let localMaintenance = [...mockMaintenance];

export async function getMaintenanceLogs(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localMaintenance];
      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(m =>
          m.truck_plate.toLowerCase().includes(q) ||
          m.type.toLowerCase().includes(q)
        );
      }
      resolve(filtered);
    }, 500);
  });
}

export async function scheduleMaintenance(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newMaint = {
        id: localMaintenance.length + 1,
        status: 'scheduled',
        ...data
      };
      localMaintenance.unshift(newMaint);
      resolve(newMaint);
    }, 600);
  });
}
