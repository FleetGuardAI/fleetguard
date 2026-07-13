import { mockFuelLogs, generateMockFuelData, mockFuelAlerts } from '@/data/mockData';

let localFuelLogs = [...mockFuelLogs];

export async function getFuelLogs(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localFuelLogs];
      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(l =>
          l.truck_plate.toLowerCase().includes(q) ||
          l.station.toLowerCase().includes(q)
        );
      }
      resolve(filtered);
    }, 500);
  });
}

export async function createFuelEntry(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newEntry = {
        id: localFuelLogs.length + 1,
        date: new Date().toISOString(),
        status: 'pending',
        ...data
      };
      localFuelLogs.unshift(newEntry);
      resolve(newEntry);
    }, 600);
  });
}

export async function getFuelTelemetry(truckId) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(generateMockFuelData());
    }, 400);
  });
}

export async function getFuelAlerts() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockFuelAlerts);
    }, 400);
  });
}
