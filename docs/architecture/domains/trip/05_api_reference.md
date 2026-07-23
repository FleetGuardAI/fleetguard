# Trip Management Domain: API Reference

The Trip API exclusively exposes **read models** and **projections**. In accordance with FleetGuard's Event-Driven Architecture, there are no lifecycle mutators (e.g., no `POST /trips/start`).

---

## `GET /trips`
Returns a paginated, filterable list of summarized trips.

### Query Parameters
- `page` (int, default: 1): Pagination offset.
- `size` (int, default: 50): Number of records per page.
- `status` (TripStatus, optional): Filter by `IN_PROGRESS`, `COMPLETED`, etc.
- `vehicle_id` (str, optional): Filter by specific vehicle.
- `driver_id` (UUID, optional): Filter by driver assignment.

### Response
```json
{
  "data": [
    {
      "trip_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "vehicle_id": "veh-123",
      "status": "COMPLETED",
      "started_at": "2026-07-21T08:00:00Z",
      "total_distance_km": 150.5
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "size": 50
  }
}
```

---

## `GET /trips/active`
Optimized projection specifically for operational dashboards to view vehicles currently in motion.

### Query Parameters
- `region` (str, optional): Filter by operational region.

### Response
```json
[
  {
    "trip_id": "b2c3d4e5-...",
    "vehicle_id": "veh-456",
    "status": "IN_PROGRESS",
    "started_at": "2026-07-21T10:00:00Z",
    "total_distance_km": 12.0
  }
]
```

---

## `GET /trips/{trip_id}`
Returns the full detail aggregate payload for a single trip.

### Response
```json
{
  "trip_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "organization_id": "org-uuid",
  "vehicle_id": "veh-123",
  "driver_assignment_id": "driver-assign-uuid",
  "status": "COMPLETED",
  "started_at": "2026-07-21T08:00:00Z",
  "ended_at": "2026-07-21T10:30:00Z",
  "origin": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "address": "New York, NY"
  },
  "destination": {
    "latitude": 42.3601,
    "longitude": -71.0589,
    "address": "Boston, MA"
  },
  "total_distance_km": 340.5,
  "driving_duration_seconds": 9000,
  "idle_duration_seconds": 1800,
  "stop_count": 1,
  "metadata": {}
}
```
