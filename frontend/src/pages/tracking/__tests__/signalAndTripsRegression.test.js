import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import api, { resolveAbortSignal } from '../../../api/client';
import {
  getDriverTrips,
  getDriverLocations,
  getDriverAnalytics,
  getTrackingDrivers,
  getTripRoute,
} from '../../../api/telematicsApi';

describe('AbortSignal Resolution & RequestInit Sanitization', () => {
  it('handles null, undefined, and non-object values safely', () => {
    expect(resolveAbortSignal(undefined)).toBeUndefined();
    expect(resolveAbortSignal(null)).toBeUndefined();
    expect(resolveAbortSignal('invalid-string')).toBeUndefined();
    expect(resolveAbortSignal(123)).toBeUndefined();
    expect(resolveAbortSignal(true)).toBeUndefined();
    expect(resolveAbortSignal({})).toBeUndefined();
    expect(resolveAbortSignal({ signal: 'not-a-signal' })).toBeUndefined();
  });

  it('resolves native AbortSignal directly', () => {
    const controller = new AbortController();
    const resolved = resolveAbortSignal(controller.signal);
    expect(resolved).toBe(controller.signal);
    expect(resolved instanceof AbortSignal).toBe(true);
  });

  it('unwraps nested { signal: AbortSignal } objects', () => {
    const controller = new AbortController();
    const resolved = resolveAbortSignal({ signal: controller.signal });
    expect(resolved).toBe(controller.signal);
    expect(resolved instanceof AbortSignal).toBe(true);
  });

  it('unwraps multiply-nested { signal: { signal: AbortSignal } } objects', () => {
    const controller = new AbortController();
    const nested = { signal: { signal: controller.signal } };
    const resolved = resolveAbortSignal(nested);
    expect(resolved).toBe(controller.signal);
    expect(resolved instanceof AbortSignal).toBe(true);
  });
});

describe('10 Core Regression Scenarios (User Prompt Verification)', () => {
  let originalFetch;

  beforeEach(() => {
    originalFetch = global.fetch;
    localStorage.setItem('fleetguard_token', 'test-token');
    localStorage.setItem('fleetguard_token_type', 'Bearer');
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  // 1. Fetch without a signal
  it('Scenario 1: Fetch without a signal omits signal from RequestInit and executes successfully', async () => {
    let capturedConfig = null;
    global.fetch = vi.fn().mockImplementation((url, config) => {
      capturedConfig = config;
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: { get: () => 'application/json' },
        json: async () => [{ id: 41, trip_id: 'TRP-112543B4' }],
      });
    });

    const trips = await getDriverTrips(74);
    expect(trips).toEqual([{ id: 41, trip_id: 'TRP-112543B4' }]);
    expect(capturedConfig.signal).toBeUndefined();
    expect(capturedConfig.headers.Authorization).toBe('Bearer test-token');
  });

  // 2. Fetch with a valid AbortController.signal
  it('Scenario 2: Fetch with a valid AbortController.signal passes native signal', async () => {
    const controller = new AbortController();
    let capturedConfig = null;

    global.fetch = vi.fn().mockImplementation((url, config) => {
      capturedConfig = config;
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: { get: () => 'application/json' },
        json: async () => [{ id: 41 }],
      });
    });

    // Pass as positional signal or options object
    await getDriverTrips(74, {}, controller.signal);
    expect(capturedConfig.signal).toBe(controller.signal);
    expect(capturedConfig.signal instanceof AbortSignal).toBe(true);

    // Pass as options object { signal }
    await getDriverTrips(74, {}, { signal: controller.signal });
    expect(capturedConfig.signal).toBe(controller.signal);
  });

  // 3. Fetch after the controller has been aborted
  it('Scenario 3: Fetch after the controller has been aborted propagates AbortError cleanly', async () => {
    const controller = new AbortController();
    controller.abort();

    global.fetch = vi.fn().mockImplementation((url, config) => {
      if (config?.signal?.aborted) {
        const error = new Error('The operation was aborted');
        error.name = 'AbortError';
        return Promise.reject(error);
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => [] });
    });

    await expect(getDriverTrips(74, {}, controller.signal)).rejects.toMatchObject({
      name: 'AbortError',
    });
  });

  // 4. Rapid driver switching
  it('Scenario 4: Rapid driver switching aborts older in-flight requests and resolves latest', async () => {
    const executionOrder = [];

    global.fetch = vi.fn().mockImplementation((url, config) => {
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          executionOrder.push(url);
          resolve({
            ok: true,
            status: 200,
            headers: { get: () => 'application/json' },
            json: async () => [{ driverUrl: url }],
          });
        }, url.includes('74') ? 50 : 10);

        if (config?.signal) {
          config.signal.addEventListener('abort', () => {
            clearTimeout(timer);
            const err = new Error('Request aborted');
            err.name = 'AbortError';
            reject(err);
          });
        }
      });
    });

    // Simulate selecting Driver 74 then immediately selecting Driver 75
    const ctrl1 = new AbortController();
    const p1 = getDriverTrips(74, {}, ctrl1.signal);

    // Rapid switch to 75
    ctrl1.abort();
    const ctrl2 = new AbortController();
    const p2 = getDriverTrips(75, {}, ctrl2.signal);

    await expect(p1).rejects.toMatchObject({ name: 'AbortError' });
    const res2 = await p2;
    expect(res2).toEqual([{ driverUrl: expect.stringContaining('/v1/tracking/driver/75/trips') }]);
  });

  // 5. Rapid date-range changes
  it('Scenario 5: Rapid date-range changes cancel obsolete in-flight requests', async () => {
    let activeController = null;

    global.fetch = vi.fn().mockImplementation((url, config) => {
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          resolve({
            ok: true,
            status: 200,
            headers: { get: () => 'application/json' },
            json: async () => ({ range: url }),
          });
        }, 30);

        if (config?.signal) {
          config.signal.addEventListener('abort', () => {
            clearTimeout(timer);
            const err = new Error('Aborted');
            err.name = 'AbortError';
            reject(err);
          });
        }
      });
    });

    // User rapidly adjusts date range 3 times
    const results = [];
    for (let i = 1; i <= 3; i++) {
      if (activeController) activeController.abort();
      activeController = new AbortController();
      const p = getDriverTrips(74, { start_time: `2026-10-0${i}T00:00:00Z` }, activeController.signal);
      results.push(p);
    }

    await expect(results[0]).rejects.toMatchObject({ name: 'AbortError' });
    await expect(results[1]).rejects.toMatchObject({ name: 'AbortError' });
    const finalResult = await results[2];
    expect(finalResult.range).toContain('2026-10-03');
  });

  // 6. Trip request success
  it('Scenario 6: Trip request success returns structured trip list and verifies URL format', async () => {
    const mockTrips = [
      {
        id: 41,
        trip_id: 'TRP-112543B4',
        status: 'IN_PROGRESS',
        driver_id: 74,
        start_time: '2026-10-23T10:00:00Z',
        end_time: null,
        distance_km: 154.2,
        points_count: 428,
      },
    ];

    let requestedUrl = null;
    global.fetch = vi.fn().mockImplementation((url) => {
      requestedUrl = url;
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: { get: () => 'application/json' },
        json: async () => mockTrips,
      });
    });

    const res = await getDriverTrips(74, {
      start_time: '2026-10-01T00:00:00Z',
      end_time: '2026-10-23T23:59:59Z',
    });

    expect(requestedUrl).toContain('/v1/tracking/driver/74/trips?');
    expect(requestedUrl).toContain('start_time=2026-10-01T00%3A00%3A00Z');
    expect(requestedUrl).toContain('end_time=2026-10-23T23%3A59%3A59Z');
    expect(res).toEqual(mockTrips);
    expect(res[0].trip_id).toBe('TRP-112543B4');
    expect(res[0].points_count).toBe(428);
  });

  // 7. Trip request returning HTTP 404 or 500
  it('Scenario 7: Trip request returning HTTP 404 or 500 throws descriptive API error', async () => {
    global.fetch = vi.fn().mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: { get: () => 'application/json' },
        json: async () => ({ detail: 'Driver 999 not found' }),
      });
    });

    await expect(getDriverTrips(999)).rejects.toThrow('Driver 999 not found');

    global.fetch = vi.fn().mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: { get: () => 'application/json' },
        json: async () => ({ detail: 'Database connection failed' }),
      });
    });

    await expect(getDriverTrips(74)).rejects.toThrow('Database connection failed');
  });

  // 8. Malformed API responses
  it('Scenario 8: Malformed API responses (non-JSON or text) are caught and handled gracefully', async () => {
    global.fetch = vi.fn().mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        status: 502,
        statusText: 'Bad Gateway',
        headers: { get: () => 'text/html' },
        json: async () => {
          throw new SyntaxError('Unexpected token < in JSON at position 0');
        },
      });
    });

    await expect(getDriverTrips(74)).rejects.toThrow();
  });

  // 9. Telemetry failure while trips succeed
  it('Scenario 9: Telemetry failure while trips succeed does not break trip retrieval', async () => {
    const mockTrips = [{ id: 41, trip_id: 'TRP-112543B4' }];

    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.includes('/trips')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: { get: () => 'application/json' },
          json: async () => mockTrips,
        });
      }
      if (url.includes('/locations') || url.includes('/analytics')) {
        return Promise.resolve({
          ok: false,
          status: 503,
          statusText: 'Service Unavailable',
          headers: { get: () => 'application/json' },
          json: async () => ({ detail: 'Telemetry engine warming up' }),
        });
      }
      return Promise.reject(new Error('Unknown url'));
    });

    // In FleetMap, trips and telemetry are independently loaded
    const tripsResult = await getDriverTrips(74);
    expect(tripsResult).toEqual(mockTrips);

    // Telemetry errors are isolated and do not prevent trip display
    await expect(getDriverLocations(74)).rejects.toThrow('Telemetry engine warming up');
  });

  // 10. Component unmount during an in-flight request
  it('Scenario 10: Component unmount aborts in-flight requests cleanly', async () => {
    const controller = new AbortController();
    let abortedInFetch = false;

    global.fetch = vi.fn().mockImplementation((url, config) => {
      return new Promise((resolve, reject) => {
        if (config?.signal) {
          config.signal.addEventListener('abort', () => {
            abortedInFetch = true;
            const err = new Error('Component unmounted');
            err.name = 'AbortError';
            reject(err);
          });
        }
      });
    });

    const inFlightPromise = getDriverTrips(74, {}, controller.signal);

    // Simulate React cleanup function on unmount:
    controller.abort();

    await expect(inFlightPromise).rejects.toMatchObject({
      name: 'AbortError',
    });
    expect(abortedInFetch).toBe(true);
  });
});
