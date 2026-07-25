/**
 * FleetGuard — Opportunity Filter Constants
 * Configuration constants for the Opportunity Feed filters.
 * Extracted from opportunity mock data.
 */

/** Vehicle type options for filters */
export const VEHICLE_TYPES = [
  'Open Trailer',
  'Closed Container',
  'Flatbed Trailer',
  'Container 20ft',
  'Container 40ft',
  'Eicher 14ft',
  'Eicher 19ft',
  'Taurus 16T',
  'Tipper Truck',
  'Car Carrier',
  'Refrigerated Van',
];

/** Source options for filters */
export const SOURCE_OPTIONS = [
  { value: 'broker', label: 'Broker' },
  { value: 'marketplace', label: 'Marketplace' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'direct', label: 'Direct Customer' },
];

/** Status options for filters */
export const STATUS_OPTIONS = [
  { value: 'available', label: 'Available' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'expired', label: 'Expired' },
  { value: 'negotiating', label: 'Negotiating' },
];

/** Priority options */
export const PRIORITY_OPTIONS = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];
