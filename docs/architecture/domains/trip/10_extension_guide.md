# Trip Management Domain: Extension Guide

This guide details how future developers should add features to the Trip Domain while strictly maintaining Domain-Driven Design boundaries.

## Adding Multi-Stop Trips
Trips often have multiple delivery stops. 
- **Do NOT** create a `DispatchStop` array inside the Trip. The Trip is a physical reality.
- **DO** create a `Waypoint` value object. When `POSITION_RECORDED` events indicate the vehicle has idled inside a geofence, append a `Waypoint` to the Trip's `stops` array. The Trip tracks that the vehicle stopped; it does *not* know if the stop was scheduled.

## Implementing Route Optimization & Geofencing
- **Do NOT** put routing API calls inside the `TripAggregate` or `TripService`.
- **DO** create a separate Geofence or Routing context that listens to `TripStarted` Domain Events. That external domain can calculate ETA or alert on route deviations.

## Incorporating Driver Behavior (Harsh Braking, Speeding)
- **Do NOT** add `harsh_braking_count` to the core `Trip` entity.
- **DO** let the Fleet Intelligence Engine calculate driver behavior. The Intelligence engine consumes the exact same `OperationalEvents` (e.g. `SPEED_ALERT`) and correlates them to the `Trip` via timestamp and `vehicle_id`. 

## Extending the Event Handler
To handle new physical triggers (e.g., a BLE beacon detecting cargo loading):
1. Ensure the Gateway defines `CARGO_LOADED` as an Operational Event.
2. Add a `_handle_cargo_loaded(event)` method in `TripEventHandler`.
3. Dispatch a command to `TripService`, which invokes logic on the `TripAggregate` (e.g., `trip.add_cargo_weight()`).
