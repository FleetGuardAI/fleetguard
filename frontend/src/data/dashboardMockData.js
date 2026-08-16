/**
 * FleetGuard Dashboard — Mock Data
 * 
 * Isolated mock data for the dashboard overview.
 * Replace with API responses when backend endpoints are ready.
 */

export const MOCK_KPIS = [
  {
    id: 'active',
    label: 'Active Trucks',
    value: 24,
    icon: 'Truck',
    trend: '+3 today',
    color: '#19B86A',
  },
  {
    id: 'on-load',
    label: 'On a Load',
    value: 12,
    icon: 'Package',
    trend: '50% utilized',
    color: '#3b82f6', // blue
  },
  {
    id: 'available',
    label: 'Available',
    value: 8,
    icon: 'CheckCircle2',
    trend: 'Ready to deploy',
    color: '#8b5cf6', // purple
  },
  {
    id: 'maintenance',
    label: 'Maintenance',
    value: 4,
    icon: 'Wrench',
    trend: '2 due this week',
    color: '#f97316', // orange
  },
];

export const MOCK_FLEET_STATUS = [
  { label: 'Active Signals', value: '1', color: '#19B86A' },
  { label: 'Fuel Economy', value: '3.9 km/L', color: '#19B86A' },
  { label: 'Vehicle Lifespan', value: '67%', progress: 67, color: '#19B86A' },
  { label: 'Safety Index', value: '92%', progress: 92, color: '#19B86A' },
  { label: 'Schedules', value: '3 Due', color: '#f59e0b' },
];

export const MOCK_FLEET_HEALTH = [
  { label: 'Fuel Efficiency', value: '3.9 km/L', status: 'normal' },
  { label: 'Engine Health', value: 'Good', status: 'good' },
  { label: 'Tyre Health', value: 'Good', status: 'good' },
  { label: 'Next Service', value: '2 Days', status: 'warning' },
];

export const MOCK_RECENT_ACTIVITY = [
  {
    id: 1,
    icon: 'Route',
    text: 'KA-01-HH-1234 started a trip',
    time: '10 min ago',
    color: '#19B86A',
  },
  {
    id: 2,
    icon: 'Fuel',
    text: 'Fuel added to KA-01-HH-1234',
    time: '45 min ago',
    color: '#36D98A',
  },
  {
    id: 3,
    icon: 'Package',
    text: 'New load assigned to KA-01-HH-1234',
    time: '1 hr ago',
    color: '#0D6B46',
  },
  {
    id: 4,
    icon: 'CreditCard',
    text: 'Payment received from ABC Logistics',
    time: '2 hr ago',
    color: '#19B86A',
  },
];

export const MOCK_FLEET_SUMMARY = {
  totalDistance: '12,450 km',
  fuelConsumed: '4,250 L',
  avgFuelEfficiency: '3.9 km/L',
  totalEarnings: '₹ 8,45,000',
  chartData: [
    { day: 'Mon', value: 1800 },
    { day: 'Tue', value: 2200 },
    { day: 'Wed', value: 1950 },
    { day: 'Thu', value: 2400 },
    { day: 'Fri', value: 2100 },
    { day: 'Sat', value: 1600 },
    { day: 'Sun', value: 1400 },
  ],
};

export const MOCK_ALERTS = [
  {
    id: 1,
    icon: 'AlertTriangle',
    text: 'KA-01-HH-1234 requires maintenance',
    detail: 'Due in 2 days',
    severity: 'warning',
  },
  {
    id: 2,
    icon: 'ShieldAlert',
    text: 'Insurance expired for KA-02-AB-5678',
    detail: 'Expired on 10 May',
    severity: 'critical',
  },
];

export const MOCK_PREDICTIVE_SIGNAL = {
  id: 'fuel-001',
  severity: 'medium',
  category: 'fuel_waste',
  title: 'Fuel drop of 5.0L detected on KA-01-HH-1234',
  narrative: 'Fuel efficiency dropped significantly on truck KA-01-HH-1234. Average fuel economy fell from 4.8 km/L to 3.9 km/L over the last 26 days. This drop is costing you roughly ₹475 per month.',
  time: '06:44 am',
  savings: 475,
  confidence: 90,
  impact: 'Financial Risk',
  truck: { plate: 'KA-01-HH-1234' },
  driver: { name: 'Ramesh Kumar' },
  rootCause: 'Potential fuel leak or unauthorized siphoning detected based on GPS-correlated fuel sensor data.',
  recommendation: 'Schedule immediate inspection of fuel tank and sensor calibration. Review driver fueling logs for discrepancies.',
  evidence: [
    'Fuel economy dropped from 4.8 to 3.9 km/L',
    '5.0L unexplained fuel loss in 24hrs',
    'No refueling event logged for the period',
    'GPS shows vehicle was stationary during drop',
  ],
  createdAt: new Date().toISOString(),
  status: 'new',
  potentialSaving: 475,
};
