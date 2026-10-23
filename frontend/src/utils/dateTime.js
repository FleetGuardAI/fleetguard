/**
 * the vahan — Geospatial Date, Time, and Timezone Utilities
 * 
 * Configured fleet timezone: Asia/Kolkata (IST, UTC+05:30).
 * Handles robust date range presets, formatting, validation, and conversions.
 */

export const FLEET_TIMEZONE = 'Asia/Kolkata';
export const FLEET_TIMEZONE_LABEL = 'IST (UTC+05:30)';

/**
 * Format a Date or ISO string in the Fleet timezone.
 */
export function formatFleetDateTime(dateInput, options = {}) {
  if (!dateInput) return 'Not available';
  try {
    const d = dateInput instanceof Date ? dateInput : new Date(dateInput);
    if (isNaN(d.getTime())) return 'Invalid date';

    const defaultOptions = {
      timeZone: FLEET_TIMEZONE,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
      ...options,
    };

    return new Intl.DateTimeFormat('en-IN', defaultOptions).format(d);
  } catch (err) {
    return String(dateInput);
  }
}

/**
 * Format date only (e.g. "22 Sep 2026").
 */
export function formatFleetDateOnly(dateInput) {
  return formatFleetDateTime(dateInput, {
    hour: undefined,
    minute: undefined,
    second: undefined,
    hour12: undefined,
  });
}

/**
 * Format time only (e.g. "06:14 PM IST").
 */
export function formatFleetTimeOnly(dateInput, includeSeconds = false) {
  if (!dateInput) return 'Not available';
  try {
    const d = dateInput instanceof Date ? dateInput : new Date(dateInput);
    if (isNaN(d.getTime())) return 'Invalid date';

    const str = new Intl.DateTimeFormat('en-IN', {
      timeZone: FLEET_TIMEZONE,
      hour: '2-digit',
      minute: '2-digit',
      second: includeSeconds ? '2-digit' : undefined,
      hour12: true,
    }).format(d);

    return `${str} IST`;
  } catch (err) {
    return '';
  }
}

/**
 * Human relative time description (e.g. "5 mins ago", "2 hours ago").
 */
export function formatRelativeTime(dateInput) {
  if (!dateInput) return 'Never';
  try {
    const d = dateInput instanceof Date ? dateInput : new Date(dateInput);
    if (isNaN(d.getTime())) return 'Invalid date';

    const now = new Date();
    const diffSeconds = Math.round((now.getTime() - d.getTime()) / 1000);

    if (diffSeconds < 60) return 'Just now';
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`;
    if (diffSeconds < 604800) return `${Math.floor(diffSeconds / 86400)}d ago`;

    return formatFleetDateOnly(d);
  } catch {
    return 'Unknown';
  }
}

/**
 * Convert seconds into clean duration string (e.g. "2h 45m", "35m 12s").
 */
export function formatDuration(seconds) {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return 'Not available';
  const sec = Math.max(0, Math.round(seconds));
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;

  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

/**
 * Convert input date & time string into ISO-8601 UTC string.
 * Uses local fleet timezone context.
 */
export function toUtcIsoString(dateStr, timeStr = '00:00') {
  if (!dateStr) return null;
  // Parse YYYY-MM-DD and HH:mm in IST context (+05:30)
  const combined = `${dateStr}T${timeStr || '00:00'}:00+05:30`;
  const d = new Date(combined);
  if (isNaN(d.getTime())) return null;
  return d.toISOString();
}

/**
 * Given a preset key, calculate the corresponding { startTime, endTime } as ISO strings.
 */
export function calculatePresetRange(presetKey, anchorDate = null) {
  const now = anchorDate ? new Date(anchorDate) : new Date();
  const end = new Date(now);
  const start = new Date(now);

  switch (presetKey) {
    case '1h':
      start.setHours(start.getHours() - 1);
      break;
    case '6h':
      start.setHours(start.getHours() - 6);
      break;
    case '12h':
      start.setHours(start.getHours() - 12);
      break;
    case '24h':
      start.setHours(start.getHours() - 24);
      break;
    case 'today': {
      // Start of day in IST (+05:30)
      const formatter = new Intl.DateTimeFormat('en-CA', { timeZone: FLEET_TIMEZONE });
      const istDateStr = formatter.format(now); // YYYY-MM-DD
      const istStart = new Date(`${istDateStr}T00:00:00+05:30`);
      return { startTime: istStart.toISOString(), endTime: now.toISOString() };
    }
    case 'yesterday': {
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      const formatter = new Intl.DateTimeFormat('en-CA', { timeZone: FLEET_TIMEZONE });
      const istDateStr = formatter.format(yesterday);
      const istStart = new Date(`${istDateStr}T00:00:00+05:30`);
      const istEnd = new Date(`${istDateStr}T23:59:59+05:30`);
      return { startTime: istStart.toISOString(), endTime: istEnd.toISOString() };
    }
    case '7d':
      start.setDate(start.getDate() - 7);
      break;
    case '30d':
      start.setDate(start.getDate() - 30);
      break;
    default:
      return { startTime: null, endTime: null };
  }

  return { startTime: start.toISOString(), endTime: end.toISOString() };
}

/**
 * Format duration in minutes.
 */
export function formatDurationMinutes(minutes) {
  if (minutes === null || minutes === undefined || isNaN(minutes)) return 'Not available';
  return formatDuration(minutes * 60);
}

/**
 * Format datetime with common patterns in fleet timezone.
 */
export function formatDateTime(dateInput, formatPattern = null) {
  if (!dateInput) return 'Not available';
  try {
    const d = dateInput instanceof Date ? dateInput : new Date(dateInput);
    if (isNaN(d.getTime())) return 'Invalid date';

    if (formatPattern === 'HH:mm') {
      return new Intl.DateTimeFormat('en-IN', {
        timeZone: FLEET_TIMEZONE,
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }).format(d);
    }
    if (formatPattern === 'HH:mm:ss') {
      return new Intl.DateTimeFormat('en-IN', {
        timeZone: FLEET_TIMEZONE,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      }).format(d);
    }
    if (formatPattern === 'dd MMM yyyy') {
      return new Intl.DateTimeFormat('en-IN', {
        timeZone: FLEET_TIMEZONE,
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      }).format(d);
    }
    if (formatPattern === 'dd MMM, HH:mm') {
      return new Intl.DateTimeFormat('en-IN', {
        timeZone: FLEET_TIMEZONE,
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }).format(d);
    }
    if (formatPattern === 'dd MMM yyyy, HH:mm:ss') {
      return new Intl.DateTimeFormat('en-IN', {
        timeZone: FLEET_TIMEZONE,
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      }).format(d);
    }

    return formatFleetDateTime(d);
  } catch {
    return String(dateInput);
  }
}

/**
 * Convenience helper returning { startTime: Date, endTime: Date } for state initialization.
 */
export function getTimeFilterRange(presetKey) {
  const { startTime, endTime } = calculatePresetRange(presetKey);
  return {
    startTime: startTime ? new Date(startTime) : new Date(Date.now() - 7 * 86400000),
    endTime: endTime ? new Date(endTime) : new Date(),
  };
}
