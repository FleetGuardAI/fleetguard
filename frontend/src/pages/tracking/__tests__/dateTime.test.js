import { describe, it, expect } from 'vitest';
import { 
  FLEET_TIMEZONE, 
  FLEET_TIMEZONE_LABEL, 
  formatFleetDateTime, 
  formatDurationMinutes, 
  formatDateTime, 
  calculatePresetRange, 
  getTimeFilterRange 
} from '@/utils/dateTime';

describe('dateTime utility in Fleet IST timezone', () => {
  it('has Asia/Kolkata timezone configured', () => {
    expect(FLEET_TIMEZONE).toBe('Asia/Kolkata');
    expect(FLEET_TIMEZONE_LABEL).toContain('IST');
  });

  it('formats duration in minutes accurately', () => {
    expect(formatDurationMinutes(0)).toBe('0s');
    expect(formatDurationMinutes(15)).toBe('15m 0s');
    expect(formatDurationMinutes(90)).toBe('1h 30m');
    expect(formatDurationMinutes(null)).toBe('Not available');
  });

  it('formats dates in Indian Standard Time (UTC+05:30)', () => {
    const utcDate = new Date('2026-10-23T10:00:00Z');
    // 10:00 UTC is 15:30 IST
    const formattedTime = formatDateTime(utcDate, 'HH:mm');
    expect(formattedTime).toBe('15:30');

    const formattedSecs = formatDateTime(utcDate, 'HH:mm:ss');
    expect(formattedSecs).toBe('15:30:00');
  });

  it('calculates preset ranges correctly', () => {
    const anchor = new Date('2026-10-23T12:00:00Z');
    
    const range1h = calculatePresetRange('1h', anchor);
    const start1h = new Date(range1h.startTime);
    const end1h = new Date(range1h.endTime);
    expect(end1h.getTime() - start1h.getTime()).toBe(3600000);

    const range24h = calculatePresetRange('24h', anchor);
    const start24h = new Date(range24h.startTime);
    const end24h = new Date(range24h.endTime);
    expect(end24h.getTime() - start24h.getTime()).toBe(86400000);

    const range7d = calculatePresetRange('7d', anchor);
    const start7d = new Date(range7d.startTime);
    const end7d = new Date(range7d.endTime);
    expect(end7d.getTime() - start7d.getTime()).toBe(7 * 86400000);
  });

  it('returns valid Date objects in getTimeFilterRange', () => {
    const range = getTimeFilterRange('7d');
    expect(range.startTime instanceof Date).toBe(true);
    expect(range.endTime instanceof Date).toBe(true);
    expect(range.startTime.getTime()).toBeLessThan(range.endTime.getTime());
  });
});
