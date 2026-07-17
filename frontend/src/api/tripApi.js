import { mockTrips } from '@/data/mockData';

let localTrips = [...mockTrips];

export async function getTrips(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localTrips];
      if (params.status) {
        filtered = filtered.filter(t => t.status === params.status);
      }
      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(t =>
          t.truck_plate.toLowerCase().includes(q) ||
          t.driver_name.toLowerCase().includes(q) ||
          t.route_name.toLowerCase().includes(q)
        );
      }
      resolve(filtered);
    }, 500);
  });
}

export async function getTripById(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const trip = localTrips.find(t => t.id === Number(id));
      if (trip) {
        resolve(trip);
      } else {
        reject(new Error('Trip not found'));
      }
    }, 400);
  });
}

export async function createTrip(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newTrip = {
        id: localTrips.length + 1,
        progress: 0,
        status: 'scheduled',
        timeline: [
          { status: 'Scheduled', time: new Date().toISOString(), description: 'Trip planning confirmed' }
        ],
        ...data
      };
      localTrips.unshift(newTrip);
      resolve(newTrip);
    }, 600);
  });
}

export async function updateTripStatus(id, status, description) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const trip = localTrips.find(t => t.id === Number(id));
      if (trip) {
        trip.status = status;
        trip.timeline.push({
          status: status.toUpperCase(),
          time: new Date().toISOString(),
          description: description || `Status updated to ${status}`
        });
        resolve(trip);
      } else {
        reject(new Error('Trip not found'));
      }
    }, 400);
  });
}
