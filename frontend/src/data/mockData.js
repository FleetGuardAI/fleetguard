/**
 * FleetGuard — Mock Data for Dashboard Demo
 * Realistic Indian trucking fleet data used as fallback when the API is empty.
 * @module data/mockData
 */

/** @typedef {{ active_trucks: number, pending_approvals: number, theft_alerts: number, flagged_drivers: number, total_expenses_today: number, total_expenses_month: number }} DashboardKPIs */

/** @type {DashboardKPIs} */
export const mockKPIs = {
  active_trucks: 24,
  pending_approvals: 7,
  theft_alerts: 3,
  flagged_drivers: 2,
  total_expenses_today: 14750,
  total_expenses_month: 287500,
};

/** @type {Array<{ id: number, issue_type: string, amount: number, status: string, risk_level: string, driver_name: string, truck_plate: string, created_at: string, vendor_name?: string, location_name?: string, receipt_url?: string }>} */
export const mockTickets = [
  {
    id: 1,
    truck_id: 1,
    driver_id: 1,
    issue_type: 'Tire Puncture',
    vendor_name: 'Sharma Tyre Works',
    amount: 850,
    fair_price: 500,
    status: 'pending',
    risk_level: 'High',
    driver_name: 'Rajesh Kumar',
    truck_plate: 'RJ14 XX 1234',
    location_name: 'NH-48, near Udaipur',
    location_lat: 24.5854,
    location_lng: 73.7125,
    created_at: new Date(Date.now() - 25 * 60000).toISOString(),
    is_duplicate: false,
    risk_reasons: 'Amount exceeds fair price by 70%',
  },
  {
    id: 2,
    truck_id: 2,
    driver_id: 2,
    issue_type: 'Fuel',
    vendor_name: 'Indian Oil, Barmer',
    amount: 4200,
    fair_price: 4100,
    status: 'pending',
    risk_level: 'Low',
    driver_name: 'Suresh Patel',
    truck_plate: 'MH12 AB 5678',
    location_name: 'NH-15, Barmer',
    location_lat: 25.7521,
    location_lng: 71.3967,
    created_at: new Date(Date.now() - 45 * 60000).toISOString(),
    is_duplicate: false,
  },
  {
    id: 3,
    truck_id: 3,
    driver_id: 3,
    issue_type: 'Engine Oil',
    vendor_name: 'Gupta Auto Parts',
    amount: 3200,
    fair_price: 2500,
    status: 'pending',
    risk_level: 'Medium',
    driver_name: 'Amit Singh',
    truck_plate: 'GJ06 CD 9012',
    location_name: 'Ahmedabad Ring Road',
    location_lat: 23.0225,
    location_lng: 72.5714,
    created_at: new Date(Date.now() - 90 * 60000).toISOString(),
    is_duplicate: false,
    risk_reasons: 'Amount exceeds fair price by 28%',
  },
  {
    id: 4,
    truck_id: 1,
    driver_id: 4,
    issue_type: 'Tire Puncture',
    vendor_name: 'Highway Tyre Service',
    amount: 500,
    fair_price: 500,
    status: 'pending',
    risk_level: 'Low',
    driver_name: 'Vikram Yadav',
    truck_plate: 'RJ14 XX 1234',
    location_name: 'NH-48, Pali',
    location_lat: 25.7711,
    location_lng: 73.3234,
    created_at: new Date(Date.now() - 120 * 60000).toISOString(),
    is_duplicate: false,
  },
  {
    id: 5,
    truck_id: 4,
    driver_id: 5,
    issue_type: 'Toll',
    vendor_name: 'NHAI Toll Plaza',
    amount: 375,
    fair_price: 375,
    status: 'approved',
    risk_level: 'Low',
    driver_name: 'Mohammad Iqbal',
    truck_plate: 'MP09 EF 3456',
    location_name: 'Kota-Bundi Highway',
    location_lat: 25.2138,
    location_lng: 75.8648,
    created_at: new Date(Date.now() - 180 * 60000).toISOString(),
    is_duplicate: false,
    payout_reference: 'UPI-A3F7B9C2E1D0',
  },
  {
    id: 6,
    truck_id: 5,
    driver_id: 1,
    issue_type: 'Tire Puncture',
    vendor_name: 'Unknown Workshop',
    amount: 1200,
    fair_price: 500,
    status: 'rejected',
    risk_level: 'Critical',
    driver_name: 'Rajesh Kumar',
    truck_plate: 'DL01 GH 7890',
    location_name: 'NH-8, Jaipur',
    location_lat: 26.9124,
    location_lng: 75.7873,
    created_at: new Date(Date.now() - 360 * 60000).toISOString(),
    is_duplicate: true,
    risk_reasons: 'Duplicate claim; Amount exceeds fair price by 140%',
  },
  {
    id: 7,
    truck_id: 2,
    driver_id: 6,
    issue_type: 'Food / Refreshment',
    vendor_name: 'Highway Dhaba',
    amount: 250,
    fair_price: 300,
    status: 'pending',
    risk_level: 'Low',
    driver_name: 'Ramesh Sharma',
    truck_plate: 'MH12 AB 5678',
    location_name: 'NH-48, Sirohi',
    location_lat: 24.8846,
    location_lng: 72.8625,
    created_at: new Date(Date.now() - 15 * 60000).toISOString(),
    is_duplicate: false,
  },
];

/** @type {Array<{ id: number, name: string, phone_number: string, risk_score: number, rating: number, total_trips: number, total_expenses: number, is_active: boolean }>} */
export const mockDrivers = [
  {
    id: 1,
    name: 'Rajesh Kumar',
    phone_number: '+919876543210',
    risk_score: 72,
    rating: 2.8,
    total_trips: 148,
    total_expenses: 125600,
    is_active: true,
  },
  {
    id: 2,
    name: 'Suresh Patel',
    phone_number: '+919876543211',
    risk_score: 15,
    rating: 4.6,
    total_trips: 203,
    total_expenses: 98400,
    is_active: true,
  },
  {
    id: 3,
    name: 'Amit Singh',
    phone_number: '+919876543212',
    risk_score: 38,
    rating: 3.9,
    total_trips: 167,
    total_expenses: 112000,
    is_active: true,
  },
  {
    id: 4,
    name: 'Vikram Yadav',
    phone_number: '+919876543213',
    risk_score: 8,
    rating: 4.8,
    total_trips: 312,
    total_expenses: 156700,
    is_active: true,
  },
  {
    id: 5,
    name: 'Mohammad Iqbal',
    phone_number: '+919876543214',
    risk_score: 22,
    rating: 4.2,
    total_trips: 189,
    total_expenses: 87200,
    is_active: true,
  },
  {
    id: 6,
    name: 'Ramesh Sharma',
    phone_number: '+919876543215',
    risk_score: 55,
    rating: 3.2,
    total_trips: 95,
    total_expenses: 67800,
    is_active: true,
  },
  {
    id: 7,
    name: 'Deepak Meena',
    phone_number: '+919876543216',
    risk_score: 5,
    rating: 4.9,
    total_trips: 276,
    total_expenses: 134500,
    is_active: true,
  },
  {
    id: 8,
    name: 'Karan Thakur',
    phone_number: '+919876543217',
    risk_score: 45,
    rating: 3.5,
    total_trips: 121,
    total_expenses: 78900,
    is_active: false,
  },
];

/**
 * Generate mock fuel chart data (24 hours of readings)
 * @returns {Array<{ timestamp: string, expected_level: number, actual_filtered_level: number, raw_level: number, is_theft_alert: boolean }>}
 */
export function generateMockFuelData() {
  const data = [];
  const now = Date.now();
  let expectedLevel = 380;
  let actualLevel = 375;
  const consumptionRate = 2.5; // liters per 15 min when driving

  for (let i = 96; i >= 0; i--) {
    const timestamp = new Date(now - i * 15 * 60000).toISOString();
    const isNight = new Date(timestamp).getHours() >= 22 || new Date(timestamp).getHours() < 5;
    const driving = !isNight && Math.random() > 0.15;

    if (driving) {
      expectedLevel -= consumptionRate;
      actualLevel -= consumptionRate + (Math.random() - 0.5) * 1.2;
    }

    // Simulate a theft event around reading 60
    const isTheft = i === 60;
    if (isTheft) {
      actualLevel -= 25; // sudden 25L drop
    }

    // Simulate a refuel around reading 35
    if (i === 35) {
      expectedLevel = 380;
      actualLevel = 372;
    }

    const noise = (Math.random() - 0.5) * 4;

    data.push({
      timestamp,
      expected_level: Math.max(0, Math.round(expectedLevel * 10) / 10),
      actual_filtered_level: Math.max(0, Math.round(actualLevel * 10) / 10),
      raw_level: Math.max(0, Math.round((actualLevel + noise) * 10) / 10),
      is_theft_alert: isTheft,
    });
  }

  return data;
}

/** @type {Array<{ id: number, license_plate: string, make: string, model: string, tank_capacity: number, is_active: boolean }>} */
export const mockTrucks = [
  { id: 1, license_plate: 'RJ14 XX 1234', make: 'Tata Motors', model: 'Prima 4928.S', year: 2023, tank_capacity: 400, is_active: true },
  { id: 2, license_plate: 'MH12 AB 5678', make: 'Ashok Leyland', model: 'Captain 2523', year: 2022, tank_capacity: 350, is_active: true },
  { id: 3, license_plate: 'GJ06 CD 9012', make: 'BharatBenz', model: '1617R', year: 2024, tank_capacity: 300, is_active: true },
  { id: 4, license_plate: 'MP09 EF 3456', make: 'Eicher', model: 'Pro 6049', year: 2023, tank_capacity: 400, is_active: true },
  { id: 5, license_plate: 'DL01 GH 7890', make: 'Tata Motors', model: 'Signa 4825.TK', year: 2021, tank_capacity: 450, is_active: true },
];

/** @type {Array<{ id: number, truck_id: number, truck_plate: string, timestamp: string, fuel_drop_liters: number, speed: number, latitude: number, longitude: number }>} */
export const mockFuelAlerts = [
  {
    id: 101,
    truck_id: 1,
    truck_plate: 'RJ14 XX 1234',
    timestamp: new Date(Date.now() - 3 * 3600000).toISOString(),
    fuel_drop_liters: 25.4,
    filtered_level_before: 285.0,
    filtered_level_after: 259.6,
    speed: 0,
    latitude: 24.9854,
    longitude: 73.3125,
  },
  {
    id: 102,
    truck_id: 3,
    truck_plate: 'GJ06 CD 9012',
    timestamp: new Date(Date.now() - 18 * 3600000).toISOString(),
    fuel_drop_liters: 18.2,
    filtered_level_before: 190.0,
    filtered_level_after: 171.8,
    speed: 0,
    latitude: 23.2225,
    longitude: 72.1714,
  },
  {
    id: 103,
    truck_id: 5,
    truck_plate: 'DL01 GH 7890',
    timestamp: new Date(Date.now() - 48 * 3600000).toISOString(),
    fuel_drop_liters: 30.1,
    filtered_level_before: 320.0,
    filtered_level_after: 289.9,
    speed: 0,
    latitude: 28.6139,
    longitude: 77.209,
  },
];
