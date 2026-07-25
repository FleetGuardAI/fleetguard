/**
 * FleetGuard AI — Intelligence Data Configuration
 *
 * UI configuration constants for AI opportunity rendering.
 * CATEGORY_META and SEVERITY_CONFIG are used by card/panel components.
 */

/**
 * Opportunity categories and their subtle icon identifiers.
 * Maps to lucide-react icon names.
 */
export const CATEGORY_META = {
  fuel_waste:             { label: 'Fuel Waste',               icon: 'Fuel',           color: '#ef4444' },
  idle_time:              { label: 'Idle Time',                icon: 'PauseCircle',    color: '#f59e0b' },
  driver_behaviour:       { label: 'Driver Behaviour',         icon: 'UserX',          color: '#f97316' },
  route_optimization:     { label: 'Route Optimization',       icon: 'Route',          color: '#3b82f6' },
  delayed_payment:        { label: 'Delayed Payment',          icon: 'Clock',          color: '#8b5cf6' },
  high_maintenance:       { label: 'High Maintenance Cost',    icon: 'Wrench',         color: '#ec4899' },
  insurance_renewal:      { label: 'Insurance Renewal',        icon: 'Shield',         color: '#06b6d4' },
  permit_expiry:          { label: 'Permit Expiry',            icon: 'FileWarning',    color: '#d946ef' },
  unused_truck:           { label: 'Unused Truck',             icon: 'TruckIcon',      color: '#64748b' },
  customer_profitability: { label: 'Customer Profitability',   icon: 'TrendingDown',   color: '#0ea5e9' },
  invoice_delay:          { label: 'Invoice Delay',            icon: 'Receipt',        color: '#a855f7' },
  low_driver_rating:      { label: 'Low Driver Rating',        icon: 'Star',           color: '#eab308' },
  unexpected_expense:     { label: 'Unexpected Expense',       icon: 'AlertTriangle',  color: '#ef4444' },
  emergency_cash:         { label: 'Emergency Cash Request',   icon: 'Banknote',       color: '#f97316' },
  duplicate_fuel:         { label: 'Duplicate Fuel Bill',      icon: 'Copy',           color: '#dc2626' },
};

export const SEVERITY_CONFIG = {
  critical: { label: 'Critical', dot: 'bg-red-500',    text: 'text-red-600 dark:text-red-400',    bg: 'bg-red-50 dark:bg-red-950/30' },
  high:     { label: 'High',     dot: 'bg-orange-500', text: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-50 dark:bg-orange-950/30' },
  medium:   { label: 'Medium',   dot: 'bg-amber-500',  text: 'text-amber-600 dark:text-amber-400',  bg: 'bg-amber-50 dark:bg-amber-950/30' },
  low:      { label: 'Low',      dot: 'bg-emerald-500',text: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-950/30' },
};
