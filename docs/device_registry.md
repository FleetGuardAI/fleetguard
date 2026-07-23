# Device Registry & Mapping Framework

## Architecture Overview
The Device Registry & Mapping Framework operates within the domain layer (`domain/device_registry/`). Its primary responsibility is managing external hardware inventory (GPS trackers, fuel sensors, dashcams) and assigning those devices to FleetGuard business entities (Vehicles, Trailers, Drivers).

It acts as the authoritative source for device identity, completely decoupled from the telemetry processing gateways. 

### Scope and Boundaries
**The Device Registry DOES:**
- Register hardware devices with provider-specific metadata.
- Prevent duplicate hardware registrations.
- Manage assignments to entities (e.g., Device `dev-uuid` is mapped to Vehicle `v-100`).
- Ensure assignment rules (e.g., A vehicle cannot have two active GPS trackers).

**The Device Registry DOES NOT:**
- Process incoming telemetry.
- Accept pings or heartbeat data.
- Run Fleet intelligence rules.

## Processing Lifecycle

### Registration
1. A new device record (`Device` model) is constructed.
2. The `DeviceRegistry` verifies no device exists with the same `provider` and `serial_number`.
3. The device is stored in the registry.

### Assignment
1. The `DeviceMappingService` receives a request to assign `dev-uuid` to `VEHICLE:v-100`.
2. `validate_mapping_conflict` checks if the device is already mapped somewhere else.
3. `validate_mapping_conflict` checks if `v-100` already has a device of that type (e.g., another `GPS_TRACKER`).
4. If valid, an immutable `DeviceMapping` is created with `status=ACTIVE`.

## Immutable Data Models
- **`Device`**: Identity record (`device_id`, `provider`, `serial_number`, `device_type`).
- **`DeviceMapping`**: Assignment record linking a `device_id` to an `entity_id` and `entity_type`.
- **`DeviceType` Enum**: Currently supports `GPS_TRACKER` and `FUEL_SENSOR`. Extensible for `DASHCAM` or `TEMP_SENSOR` without architectural rewrites.

## Anti-Patterns
- **Gateways Querying State**: A telemetry gateway (e.g. `infrastructure/fuel/`) should not query the Device Registry to figure out which vehicle a reading belongs to. The gateway should emit an Operational Event referencing the hardware `device_id` ONLY. The Intelligence Engine (or another mapping listener) will join the telemetry event with the Device Registry mapping offline.
