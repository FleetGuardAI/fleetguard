export const APP_NAME = 'FleetGuard';

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  VEHICLES: '/vehicles',
  VEHICLE_NEW: '/vehicles/new',
  VEHICLE_DETAIL: '/vehicles/:id',
  VEHICLE_EDIT: '/vehicles/:id/edit',
  DRIVERS: '/drivers',
  DRIVER_NEW: '/drivers/new',
  DRIVER_DETAIL: '/drivers/:id',
  DRIVER_EDIT: '/drivers/:id/edit',
  TRIPS: '/trips',
  TRIP_NEW: '/trips/new',
  TRIP_DETAIL: '/trips/:id',
  FUEL: '/fuel',
  FUEL_NEW: '/fuel/new',
  EXPENSES: '/expenses',
  EXPENSE_NEW: '/expenses/new',
  NOTIFICATIONS: '/notifications',
  PROFILE: '/profile',
  SETTINGS: '/settings',
};

export const SIDEBAR_NAV = [
  {
    section: 'Overview',
    items: [
      { label: 'Dashboard', path: ROUTES.DASHBOARD, icon: 'LayoutDashboard' },
    ],
  },
  {
    section: 'Fleet',
    items: [
      { label: 'Vehicles', path: ROUTES.VEHICLES, icon: 'Truck' },
      { label: 'Drivers', path: ROUTES.DRIVERS, icon: 'Users' },
    ],
  },
  {
    section: 'Operations',
    items: [
      { label: 'Trips', path: ROUTES.TRIPS, icon: 'Route' },
      { label: 'Fuel', path: ROUTES.FUEL, icon: 'Fuel' },
      { label: 'Expenses', path: ROUTES.EXPENSES, icon: 'Receipt' },
    ],
  },
  {
    section: 'System',
    items: [
      { label: 'Notifications', path: ROUTES.NOTIFICATIONS, icon: 'Bell' },
      { label: 'Settings', path: ROUTES.SETTINGS, icon: 'Settings' },
    ],
  },
];

export const VEHICLE_TYPES = [
  { value: 'truck', label: 'Truck' },
  { value: 'trailer', label: 'Trailer' },
  { value: 'tanker', label: 'Tanker' },
  { value: 'container', label: 'Container' },
];

export const FUEL_TYPES = [
  { value: 'diesel', label: 'Diesel' },
  { value: 'petrol', label: 'Petrol' },
  { value: 'cng', label: 'CNG' },
  { value: 'electric', label: 'Electric' },
];

export const EXPENSE_CATEGORIES = [
  { value: 'repair', label: 'Repair' },
  { value: 'fuel', label: 'Fuel' },
  { value: 'toll', label: 'Toll' },
  { value: 'parking', label: 'Parking' },
  { value: 'fine', label: 'Fine' },
  { value: 'other', label: 'Other' },
];

export const STATUS_COLORS = {
  active: 'bg-green-100 text-green-700',
  inactive: 'bg-gray-100 text-gray-700',
  maintenance: 'bg-amber-100 text-amber-700',
  'on-trip': 'bg-blue-100 text-blue-700',
  'off-duty': 'bg-gray-100 text-gray-700',
  scheduled: 'bg-purple-100 text-purple-700',
  'in-progress': 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
  pending: 'bg-amber-100 text-amber-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
};

export const ITEMS_PER_PAGE_OPTIONS = [10, 25, 50, 100];
export const DEFAULT_PAGE_SIZE = 10;
