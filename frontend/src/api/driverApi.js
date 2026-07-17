import { mockDrivers, mockTrucks } from '@/data/mockData';

let localDrivers = [...mockDrivers];

export async function getDrivers(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localDrivers];
      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(d =>
          d.name.toLowerCase().includes(q) ||
          d.phone_number.includes(q)
        );
      }
      if (params.status) {
        const active = params.status === 'active';
        filtered = filtered.filter(d => d.is_active === active);
      }
      resolve(filtered);
    }, 500);
  });
}

export async function getDriverById(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const driver = localDrivers.find(d => d.id === Number(id));
      if (driver) {
        // Find assigned truck
        const assignedTruck = mockTrucks[driver.id % mockTrucks.length]; // dummy relation
        resolve({ ...driver, assignedTruck });
      } else {
        reject(new Error('Driver not found'));
      }
    }, 400);
  });
}

export async function createDriver(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newDriver = {
        id: localDrivers.length + 1,
        risk_score: Math.floor(Math.random() * 50),
        rating: 4.0,
        total_trips: 0,
        total_expenses: 0,
        is_active: true,
        ...data
      };
      localDrivers.unshift(newDriver);
      resolve(newDriver);
    }, 600);
  });
}

export async function updateDriver(id, data) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const index = localDrivers.findIndex(d => d.id === Number(id));
      if (index !== -1) {
        localDrivers[index] = { ...localDrivers[index], ...data };
        resolve(localDrivers[index]);
      } else {
        reject(new Error('Driver not found'));
      }
    }, 500);
  });
}

export async function assignVehicle(driverId, vehicleId) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true, message: `Vehicle ID ${vehicleId} assigned to driver ID ${driverId}.` });
    }, 600);
  });
}
