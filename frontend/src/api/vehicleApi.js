import { mockTrucks, mockTrips } from '@/data/mockData';

let localTrucks = [...mockTrucks];

export async function getVehicles(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localTrucks];
      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(v =>
          v.license_plate.toLowerCase().includes(q) ||
          v.make.toLowerCase().includes(q) ||
          v.model.toLowerCase().includes(q)
        );
      }
      if (params.status) {
        const active = params.status === 'active';
        filtered = filtered.filter(v => v.is_active === active);
      }
      resolve(filtered);
    }, 500);
  });
}

export async function getVehicleById(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const truck = localTrucks.find(t => t.id === Number(id));
      if (truck) {
        // Find associated active trip if any
        const activeTrip = mockTrips.find(tr => tr.truck_id === truck.id && tr.status === 'on-trip');
        resolve({ ...truck, activeTrip });
      } else {
        reject(new Error('Vehicle not found'));
      }
    }, 400);
  });
}

export async function createVehicle(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newTruck = {
        id: localTrucks.length + 1,
        is_active: true,
        ...data
      };
      localTrucks.unshift(newTruck);
      resolve(newTruck);
    }, 600);
  });
}

export async function updateVehicle(id, data) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const index = localTrucks.findIndex(t => t.id === Number(id));
      if (index !== -1) {
        localTrucks[index] = { ...localTrucks[index], ...data };
        resolve(localTrucks[index]);
      } else {
        reject(new Error('Vehicle not found'));
      }
    }, 500);
  });
}

export async function getVehicleHistory(id) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { id: 1, date: new Date(Date.now() - 3600000).toISOString(), status: 'moving', speed: 65, location: 'Near Udaipur, NH-48', fuelLevel: 280 },
        { id: 2, date: new Date(Date.now() - 7200000).toISOString(), status: 'moving', speed: 70, location: 'Near Pali, NH-48', fuelLevel: 295 },
        { id: 3, date: new Date(Date.now() - 10800000).toISOString(), status: 'stopped', speed: 0, location: 'Dhaba Midway, Ajmer', fuelLevel: 300 }
      ]);
    }, 400);
  });
}
