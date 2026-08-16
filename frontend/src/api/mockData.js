// Mock Data Generator for FleetGuard
export function getMockData(endpoint) {
  if (endpoint.includes('/v1/vehicles') || endpoint.includes('/trucks')) {
    return [
      { id: 1, license_plate: 'MH-12-AB-1234', make: 'Tata', model: 'Prima 5530.S', year: 2022, type: 'Heavy Duty', status: 'ACTIVE', current_fuel_level: 65, tank_capacity: 400, location: 'Mumbai' },
      { id: 2, license_plate: 'MH-14-CD-5678', make: 'Ashok Leyland', model: 'U-3518', year: 2021, type: 'Medium Duty', status: 'MAINTENANCE', current_fuel_level: 20, tank_capacity: 350, location: 'Pune' },
      { id: 3, license_plate: 'KA-01-EF-9012', make: 'BharatBenz', model: '3528C', year: 2023, type: 'Heavy Duty', status: 'ACTIVE', current_fuel_level: 80, tank_capacity: 380, location: 'Bangalore' },
    ];
  }
  if (endpoint.includes('/v1/drivers')) {
    return [
      { id: 101, name: 'Ramesh Kumar', phone_number: '+91 9876543210', status: 'ACTIVE', risk_score: 25, rating: 4.8 },
      { id: 102, name: 'Suresh Singh', phone_number: '+91 9876543211', status: 'INACTIVE', risk_score: 45, rating: 4.2 },
      { id: 103, name: 'Amit Patel', phone_number: '+91 9876543212', status: 'ACTIVE', risk_score: 15, rating: 4.9 },
    ];
  }
  if (endpoint.includes('/v1/trips')) {
    return [
      { id: 1001, trip_id: 'TRP-1001', origin: 'Mumbai', destination: 'Delhi', status: 'IN_PROGRESS', progress: 45, vehicle_id: 1, driver_name: 'Ramesh Kumar', planned_distance: 1400, revenue: 45000 },
      { id: 1002, trip_id: 'TRP-1002', origin: 'Pune', destination: 'Bangalore', status: 'COMPLETED', progress: 100, vehicle_id: 2, driver_name: 'Suresh Singh', planned_distance: 850, revenue: 28000 },
      { id: 1003, trip_id: 'TRP-1003', origin: 'Chennai', destination: 'Hyderabad', status: 'CREATED', progress: 0, vehicle_id: 3, driver_name: 'Amit Patel', planned_distance: 620, revenue: 21000 },
    ];
  }
  if (endpoint.includes('/v1/maintenance')) {
    return [
      { id: 501, vehicle_id: 1, type: 'Preventive', status: 'COMPLETED', cost: 15000, date: '2025-10-15', description: 'Oil change and brake inspection' },
      { id: 502, vehicle_id: 2, type: 'Repair', status: 'IN_PROGRESS', cost: 45000, date: '2025-11-20', description: 'Engine overheating issue' },
      { id: 503, vehicle_id: 3, type: 'Tire Replacement', status: 'SCHEDULED', cost: 32000, date: '2025-12-05', description: 'Replace all rear tires' },
    ];
  }
  if (endpoint.includes('/v1/expenses')) {
    return [
      { id: 701, category: 'Toll', amount: 4500, date: '2025-11-18', vehicle_id: 1, trip_id: 1001, description: 'NH48 Toll Plaza' },
      { id: 702, category: 'Food', amount: 850, date: '2025-11-19', vehicle_id: 1, trip_id: 1001, description: 'Driver allowance' },
      { id: 703, category: 'Maintenance', amount: 15000, date: '2025-10-15', vehicle_id: 2, trip_id: null, description: 'Oil change' },
    ];
  }
  if (endpoint.includes('/v1/payments')) {
    return [
      { id: 801, amount: 45000, status: 'COMPLETED', date: '2025-11-10', method: 'Bank Transfer', reference: 'TRX987654321', type: 'Income' },
      { id: 802, amount: 12500, status: 'PENDING', date: '2025-11-20', method: 'UPI', reference: 'UPI123456789', type: 'Expense' },
      { id: 803, amount: 28000, status: 'COMPLETED', date: '2025-11-15', method: 'Card', reference: 'CRD555666777', type: 'Income' },
    ];
  }
  if (endpoint.includes('/v1/fuel')) {
    return [
      { id: 901, vehicle_id: 1, liters: 150, cost: 13500, location: 'Reliance Pump, Surat', date: '2025-11-18' },
      { id: 902, vehicle_id: 2, liters: 80, cost: 7200, location: 'Indian Oil, Pune', date: '2025-11-15' },
      { id: 903, vehicle_id: 3, liters: 200, cost: 18000, location: 'HP Petrol Pump, Hubli', date: '2025-11-19' },
    ];
  }
  if (endpoint.includes('/v1/assets')) {
    return [
      { id: 201, name: 'GPS Tracker v2', type: 'Telematics', status: 'ACTIVE', assigned_to: 'MH-12-AB-1234' },
      { id: 202, name: 'Dashcam Pro', type: 'Camera', status: 'MAINTENANCE', assigned_to: 'MH-14-CD-5678' },
      { id: 203, name: 'Fuel Sensor', type: 'Sensor', status: 'ACTIVE', assigned_to: 'KA-01-EF-9012' },
    ];
  }
  if (endpoint.includes('/v1/documents')) {
    return [
      { id: 301, name: 'Vehicle Registration', type: 'RC', expiry: '2028-05-10', status: 'VALID', related_entity: 'MH-12-AB-1234' },
      { id: 302, name: 'National Permit', type: 'Permit', expiry: '2026-01-15', status: 'EXPIRING_SOON', related_entity: 'MH-14-CD-5678' },
      { id: 303, name: 'Driver License', type: 'License', expiry: '2030-08-22', status: 'VALID', related_entity: 'Ramesh Kumar' },
    ];
  }
  if (endpoint.includes('/v1/alerts') || endpoint.includes('/v1/notifications')) {
    return [
      { id: 401, type: 'Fuel Theft', severity: 'HIGH', message: 'Sudden fuel drop detected on MH-12-AB-1234', timestamp: new Date().toISOString(), read: false },
      { id: 402, type: 'Maintenance Due', severity: 'MEDIUM', message: 'MH-14-CD-5678 is due for oil change', timestamp: new Date(Date.now() - 86400000).toISOString(), read: true },
      { id: 403, type: 'Overspeeding', severity: 'LOW', message: 'KA-01-EF-9012 exceeded 80km/h', timestamp: new Date(Date.now() - 3600000).toISOString(), read: false },
    ];
  }
  if (endpoint.includes('/tickets')) {
    return [
      { id: 1, title: 'App crashing on map view', issue_type: 'Technical Issue', status: 'open', created_at: new Date().toISOString() },
      { id: 2, title: 'Billing discrepancy for last month', issue_type: 'Billing & Payments', status: 'resolved', created_at: new Date(Date.now() - 86400000*3).toISOString() },
      { id: 101, title: 'Advance for Trip TRP-404', issue_type: 'Driver Advance', status: 'open', driver_name: 'Amit Patel', driver_id: 103, amount: 2500, method: 'UPI', created_at: new Date().toISOString() },
      { id: 102, title: 'Repair costs for flat tire', issue_type: 'Repair Claim', status: 'open', driver_name: 'Suresh Singh', driver_id: 102, amount: 1200, method: 'Bank Transfer', created_at: new Date(Date.now() - 8640000).toISOString() },
      { id: 103, title: 'Fuel Card Recharge Request', issue_type: 'Fuel Advance', status: 'resolved', driver_name: 'Ramesh Kumar', driver_id: 101, amount: 15000, method: 'Card', created_at: new Date(Date.now() - 86400000*2).toISOString() },
    ];
  }
  if (endpoint.includes('/v1/events') || endpoint.includes('/events')) {
    return [
      { id: 2001, actor_id: 'Ramesh Kumar', event_type: 'trip.started', payload: { description: 'Trip TRP-1001 started from Mumbai' }, timestamp: new Date().toISOString() },
      { id: 2002, actor_id: 'System Admin', event_type: 'payment.settled', payload: { description: 'Settled vendor payment TXN-987654321' }, timestamp: new Date(Date.now() - 3600000).toISOString() },
      { id: 2003, actor_id: 'Amit Patel', event_type: 'document.uploaded', payload: { description: 'Uploaded new Driver License scan' }, timestamp: new Date(Date.now() - 86400000).toISOString() },
      { id: 2004, actor_id: 'System Admin', event_type: 'vehicle.maintenance_scheduled', payload: { description: 'Scheduled Preventive maintenance for MH-12-AB-1234' }, timestamp: new Date(Date.now() - 86400000 * 2).toISOString() },
    ];
  }
  
  return []; // Default empty fallback
}
