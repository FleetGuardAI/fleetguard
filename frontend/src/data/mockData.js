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

export const mockTrips = [
  {
    id: 1,
    truck_id: 1,
    truck_plate: 'RJ14 XX 1234',
    driver_id: 1,
    driver_name: 'Rajesh Kumar',
    route_name: 'Jaipur - Mumbai Express',
    start_point: 'Jaipur, Rajasthan',
    end_point: 'Mumbai, Maharashtra',
    status: 'on-trip',
    start_date: new Date(Date.now() - 24 * 3600000).toISOString(),
    expected_delivery: new Date(Date.now() + 12 * 3600000).toISOString(),
    distance_km: 1150,
    progress: 65,
    current_lat: 22.5726,
    current_lng: 72.9777,
    timeline: [
      { status: 'Dispatched', time: new Date(Date.now() - 24 * 3600000).toISOString(), description: 'Trip started from Jaipur yard' },
      { status: 'Toll Crossed', time: new Date(Date.now() - 18 * 3600000).toISOString(), description: 'Kishangarh Toll Plaza' },
      { status: 'Fuel Stop', time: new Date(Date.now() - 12 * 3600000).toISOString(), description: 'Filled 200L at Jio-bp, Udaipur' },
      { status: 'Active', time: new Date(Date.now()).toISOString(), description: 'Currently near Vadodara' }
    ]
  },
  {
    id: 2,
    truck_id: 2,
    truck_plate: 'MH12 AB 5678',
    driver_id: 2,
    driver_name: 'Suresh Patel',
    route_name: 'Pune - Bangalore',
    start_point: 'Pune, Maharashtra',
    end_point: 'Bangalore, Karnataka',
    status: 'completed',
    start_date: new Date(Date.now() - 72 * 3600000).toISOString(),
    end_date: new Date(Date.now() - 24 * 3600000).toISOString(),
    distance_km: 840,
    progress: 100,
    timeline: [
      { status: 'Dispatched', time: new Date(Date.now() - 72 * 3600000).toISOString(), description: 'Trip started from Pune warehouse' },
      { status: 'Completed', time: new Date(Date.now() - 24 * 3600000).toISOString(), description: 'Delivered cargo safely at Bangalore terminal' }
    ]
  },
  {
    id: 3,
    truck_id: 3,
    truck_plate: 'GJ06 CD 9012',
    driver_id: 3,
    driver_name: 'Amit Singh',
    route_name: 'Ahmedabad - Delhi Industrial',
    start_point: 'Ahmedabad, Gujarat',
    end_point: 'Delhi NCR',
    status: 'scheduled',
    start_date: new Date(Date.now() + 18 * 3600000).toISOString(),
    distance_km: 950,
    progress: 0,
    timeline: [
      { status: 'Scheduled', time: new Date().toISOString(), description: 'Trip planning confirmed' }
    ]
  }
];

export const mockFuelLogs = [
  { id: 1, truck_id: 1, truck_plate: 'RJ14 XX 1234', date: new Date(Date.now() - 12 * 3600000).toISOString(), quantity_liters: 200, price_per_liter: 94.5, total_amount: 18900, odometer: 124500, station: 'Jio-bp, Udaipur', receipt_url: 'https://example.com/receipt1.jpg', status: 'approved' },
  { id: 2, truck_id: 2, truck_plate: 'MH12 AB 5678', date: new Date(Date.now() - 48 * 3600000).toISOString(), quantity_liters: 150, price_per_liter: 92.8, total_amount: 13920, odometer: 98600, station: 'Indian Oil, Pune', receipt_url: 'https://example.com/receipt2.jpg', status: 'approved' },
  { id: 3, truck_id: 3, truck_plate: 'GJ06 CD 9012', date: new Date(Date.now() - 72 * 3600000).toISOString(), quantity_liters: 180, price_per_liter: 93.1, total_amount: 16758, odometer: 45200, station: 'HP Petrol Pump, Ahmedabad', receipt_url: 'https://example.com/receipt3.jpg', status: 'pending' }
];

export const mockExpenses = [
  { id: 1001, truck_plate: 'RJ14 XX 1234', driver_name: 'Rajesh Kumar', category: 'repair', title: 'Tyre puncture Udaipur', amount: 850, date: new Date(Date.now() - 2 * 3600000).toISOString(), status: 'pending', receipt_url: 'https://images.unsplash.com/photo-1578894381163-e72c17f2d45f?q=80&w=600', ai_risk: 'High', ai_details: 'Amount exceeds benchmark price of INR 500 for tire repairs in this sector by 70%.' },
  { id: 1002, truck_plate: 'MH12 AB 5678', driver_name: 'Suresh Patel', category: 'toll', title: 'Khed Shivapur Toll', amount: 375, date: new Date(Date.now() - 12 * 3600000).toISOString(), status: 'approved', receipt_url: 'https://images.unsplash.com/photo-1559136555-9303baea8ebd?q=80&w=600', ai_risk: 'Low', ai_details: 'Toll amount matches NHAI transaction database exactly.' },
  { id: 1003, truck_plate: 'GJ06 CD 9012', driver_name: 'Amit Singh', category: 'fine', title: 'Over-speeding fine NH-8', amount: 2000, date: new Date(Date.now() - 24 * 3600000).toISOString(), status: 'rejected', receipt_url: '', ai_risk: 'Critical', ai_details: 'No supporting challan or receipt uploaded. Vehicle telematics shows speed did not exceed 65 km/h.' }
];

export const mockPayments = [
  { id: 'PAY-8921', recipient_name: 'Sharma Tyre Works', type: 'Vendor Payout', amount: 850, method: 'UPI', status: 'pending', date: new Date(Date.now() - 1 * 3600000).toISOString(), description: 'Tire repair payout' },
  { id: 'PAY-8920', recipient_name: 'Indian Oil Barmer', type: 'Fuel Card Recharge', amount: 15000, method: 'NetBanking', status: 'completed', date: new Date(Date.now() - 5 * 3600000).toISOString(), ref_num: 'TXN-9023481239', description: 'Monthly fuel quota' },
  { id: 'PAY-8919', recipient_name: 'Rajesh Kumar', type: 'Driver Advance', amount: 3000, method: 'IMPS', status: 'completed', date: new Date(Date.now() - 10 * 3600000).toISOString(), ref_num: 'TXN-9023471004', description: 'Food & toll allowance' }
];

export const mockMaintenance = [
  { id: 1, truck_plate: 'RJ14 XX 1234', type: 'Scheduled Service', description: 'Engine Oil and Air Filter replacement', cost: 12500, date: new Date(Date.now() - 10 * 86400000).toISOString(), status: 'completed', odometer: 121000, workshop: 'Tata Authorized Service, Jaipur' },
  { id: 2, truck_plate: 'MH12 AB 5678', type: 'Breakdown Repair', description: 'Clutch plate replacement on highway', cost: 22000, date: new Date(Date.now() - 2 * 86400000).toISOString(), status: 'completed', odometer: 97800, workshop: 'Highway Garage, Kolhapur' },
  { id: 3, truck_plate: 'GJ06 CD 9012', type: 'Inspection', description: 'Brake pad wear and air brake check', cost: 1500, date: new Date(Date.now() + 3 * 86400000).toISOString(), status: 'scheduled', odometer: 45500, workshop: 'BharatBenz Service, Surat' }
];

export const mockDocuments = [
  { id: 1, name: 'Registration Certificate (RC)', target_type: 'Vehicle', target_name: 'RJ14 XX 1234', category: 'Registration', status: 'active', expiry_date: '2029-10-15', file_url: 'https://example.com/rc_rj14.pdf' },
  { id: 2, name: 'National Goods Permit', target_type: 'Vehicle', target_name: 'MH12 AB 5678', category: 'Permit', status: 'warning', expiry_date: new Date(Date.now() + 15 * 86400000).toISOString().split('T')[0], file_url: 'https://example.com/permit_mh12.pdf' },
  { id: 3, name: 'Commercial Driving License', target_type: 'Driver', target_name: 'Rajesh Kumar', category: 'License', status: 'expired', expiry_date: new Date(Date.now() - 5 * 86400000).toISOString().split('T')[0], file_url: 'https://example.com/dl_rajesh.pdf' }
];

export const mockAlerts = [
  { id: 'ALT-101', type: 'Fuel Theft', level: 'critical', truck_plate: 'RJ14 XX 1234', message: 'Sudden fuel drop of 25.4L detected while stationary', date: new Date(Date.now() - 30 * 60000).toISOString(), resolved: false },
  { id: 'ALT-102', type: 'Over-speeding', level: 'warning', truck_plate: 'GJ06 CD 9012', message: 'Vehicle exceeded highway speed limit (88 km/h)', date: new Date(Date.now() - 120 * 60000).toISOString(), resolved: false },
  { id: 'ALT-103', type: 'Doc Expiration', level: 'warning', truck_plate: 'MH12 AB 5678', message: 'National Goods Permit is expiring in 15 days', date: new Date(Date.now() - 360 * 60000).toISOString(), resolved: true, resolved_by: 'Suryansh Chaudhary', resolved_at: new Date().toISOString() }
];

export const mockNotifications = [
  { id: 1, title: 'Critical Fuel Theft Alert', message: 'Truck RJ14 XX 1234 reported a stationary fuel drop of 25.4 Liters near Pali.', type: 'alert', read: false, time: new Date(Date.now() - 15 * 60000).toISOString() },
  { id: 2, title: 'New Claim Received', message: 'Driver Amit Singh uploaded a bill of INR 3,200 for Engine Oil via WhatsApp.', type: 'expense', read: false, time: new Date(Date.now() - 45 * 60000).toISOString() },
  { id: 3, title: 'License Renewal Warning', message: 'Driver Rajesh Kumar\'s Commercial License is marked as expired.', type: 'document', read: true, time: new Date(Date.now() - 24 * 3600000).toISOString() }
];

export const mockUsers = [
  { id: 1, name: 'Suryansh Chaudhary', email: 'suryansh@fleetguard.com', role: 'COO', status: 'active', phone: '+919999988888', department: 'Operations' },
  { id: 2, name: 'Deepak Rathore', email: 'deepak@fleetguard.com', role: 'Fleet Manager', status: 'active', phone: '+919999977777', department: 'Maintenance' },
  { id: 3, name: 'Vikash Yadav', email: 'vikash@fleetguard.com', role: 'Dispatcher', status: 'active', phone: '+919999966666', department: 'Logistics' },
  { id: 4, name: 'Neha Sharma', email: 'neha@fleetguard.com', role: 'Finance Admin', status: 'inactive', phone: '+919999955555', department: 'Finance' }
];

export const mockAuditLogs = [
  { id: 'AUD-991', user: 'Suryansh Chaudhary', action: 'Approved Expense Claim', details: 'Approved INR 850 puncture repair claim for RJ14 XX 1234', timestamp: new Date(Date.now() - 15 * 60000).toISOString(), ip: '192.168.1.102' },
  { id: 'AUD-990', user: 'Deepak Rathore', action: 'Added New Vehicle', details: 'Created vehicle profile GJ06 CD 9012 (BharatBenz)', timestamp: new Date(Date.now() - 4 * 3600000).toISOString(), ip: '192.168.1.105' },
  { id: 'AUD-989', user: 'Suryansh Chaudhary', action: 'Settings Updated', details: 'Modified fuel telemetry alert sensitivity from 15L to 18L', timestamp: new Date(Date.now() - 24 * 3600000).toISOString(), ip: '103.22.45.18' }
];

export const mockRoles = [
  {
    role: 'COO',
    description: 'Full administrative control and financial approval authority',
    permissions: {
      dashboard: ['view'],
      vehicles: ['view', 'create', 'edit', 'delete'],
      drivers: ['view', 'create', 'edit', 'delete'],
      trips: ['view', 'create', 'edit', 'delete'],
      fuel: ['view', 'create', 'edit', 'delete'],
      expenses: ['view', 'approve', 'reject'],
      payments: ['view', 'create', 'settle'],
      maintenance: ['view', 'create', 'edit'],
      documents: ['view', 'upload', 'verify'],
      system: ['manage_settings', 'view_logs', 'manage_users']
    }
  },
  {
    role: 'Fleet Manager',
    description: 'Manages drivers, vehicles, and maintenance logs',
    permissions: {
      dashboard: ['view'],
      vehicles: ['view', 'create', 'edit'],
      drivers: ['view', 'create', 'edit'],
      trips: ['view', 'create', 'edit'],
      fuel: ['view', 'create'],
      expenses: ['view'],
      payments: ['view'],
      maintenance: ['view', 'create', 'edit', 'delete'],
      documents: ['view', 'upload'],
      system: ['manage_settings']
    }
  },
  {
    role: 'Dispatcher',
    description: 'Monitors active vehicles, allocates routes, and handles daily trip updates',
    permissions: {
      dashboard: ['view'],
      vehicles: ['view'],
      drivers: ['view'],
      trips: ['view', 'create', 'edit'],
      fuel: ['view'],
      expenses: ['view', 'create'],
      payments: ['view'],
      maintenance: ['view'],
      documents: ['view'],
      system: []
    }
  }
];

