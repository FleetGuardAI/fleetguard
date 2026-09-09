BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 000_legacy_base

CREATE TYPE ticketstatus AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REJECTED');;

CREATE TYPE risklevel AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');;

CREATE TYPE fuel_source AS ENUM ('TELEMATICS', 'MANUAL_ENTRY', 'CALCULATED');;

CREATE TYPE fuel_state_reliability AS ENUM ('HIGH', 'MEDIUM', 'LOW');;

CREATE TYPE fuel_transaction_type AS ENUM ('REFILL', 'THEFT', 'CONSUMPTION');;

CREATE TABLE companies (
    id SERIAL NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE users (
    id SERIAL NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    hashed_password VARCHAR(255) NOT NULL, 
    role VARCHAR(50) NOT NULL, 
    is_active BOOLEAN, 
    company_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id), 
    UNIQUE (email)
);

CREATE TABLE trucks (
    id SERIAL NOT NULL, 
    license_plate VARCHAR(50) NOT NULL, 
    company_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id), 
    UNIQUE (license_plate)
);

CREATE TABLE drivers (
    id SERIAL NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    phone VARCHAR(50), 
    company_id INTEGER NOT NULL, 
    risk_score FLOAT DEFAULT '0.0' NOT NULL, 
    rating FLOAT DEFAULT '5.0' NOT NULL, 
    total_trips INTEGER DEFAULT '0' NOT NULL, 
    total_expenses FLOAT DEFAULT '0.0' NOT NULL, 
    is_active BOOLEAN DEFAULT '1' NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id)
);

CREATE TABLE fuel_logs (
    id SERIAL NOT NULL, 
    truck_id INTEGER NOT NULL, 
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL, 
    raw_level FLOAT NOT NULL, 
    filtered_level FLOAT NOT NULL, 
    expected_level FLOAT NOT NULL, 
    speed FLOAT NOT NULL, 
    latitude FLOAT NOT NULL, 
    longitude FLOAT NOT NULL, 
    is_theft_alert BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(truck_id) REFERENCES trucks (id)
);

CREATE TABLE fuel_states (
    id SERIAL NOT NULL, 
    truck_id INTEGER NOT NULL, 
    current_level FLOAT NOT NULL, 
    source fuel_source NOT NULL, 
    reliability fuel_state_reliability NOT NULL, 
    last_operational_event_id VARCHAR(255), 
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(truck_id) REFERENCES trucks (id)
);

CREATE TABLE fuel_transactions (
    id SERIAL NOT NULL, 
    truck_id INTEGER NOT NULL, 
    transaction_type fuel_transaction_type NOT NULL, 
    amount_liters FLOAT NOT NULL, 
    origin_type VARCHAR(50), 
    origin_id VARCHAR(255), 
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL, 
    description VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(truck_id) REFERENCES trucks (id)
);

CREATE TABLE tickets (
    id SERIAL NOT NULL, 
    truck_id INTEGER, 
    driver_id INTEGER NOT NULL, 
    issue_type VARCHAR(100) NOT NULL, 
    vendor_name VARCHAR(200), 
    amount FLOAT NOT NULL, 
    fair_price FLOAT, 
    description TEXT, 
    location_lat FLOAT, 
    location_lng FLOAT, 
    location_name VARCHAR(300), 
    receipt_url VARCHAR(500), 
    ocr_raw_response TEXT, 
    status ticketstatus NOT NULL, 
    risk_level risklevel NOT NULL, 
    risk_reasons TEXT, 
    is_duplicate BOOLEAN NOT NULL, 
    expense_date TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    payout_reference VARCHAR(100), 
    PRIMARY KEY (id), 
    FOREIGN KEY(driver_id) REFERENCES drivers (id), 
    FOREIGN KEY(truck_id) REFERENCES trucks (id)
);

INSERT INTO alembic_version (version_num) VALUES ('000_legacy_base') RETURNING alembic_version.version_num;

-- Running upgrade 000_legacy_base -> 001_operational_event

CREATE TYPE event_type AS ENUM (
            'FUEL_FILLED',
            'FUEL_ALERT_TRIGGERED',
            'TRIP_STARTED',
            'TRIP_ENDED',
            'TRIP_PAUSED',
            'TRIP_RESUMED',
            'VEHICLE_ASSIGNED',
            'VEHICLE_UNASSIGNED',
            'VEHICLE_STATUS_CHANGED',
            'DRIVER_ASSIGNED',
            'DRIVER_UNASSIGNED',
            'DRIVER_STATUS_CHANGED',
            'MAINTENANCE_COMPLETED',
            'MAINTENANCE_SCHEDULED',
            'MAINTENANCE_OVERDUE',
            'TYRE_REPLACED',
            'TYRE_PRESSURE_ALERT',
            'EXPENSE_ADDED',
            'EXPENSE_APPROVED',
            'EXPENSE_REJECTED',
            'INSURANCE_EXPIRY_ALERT',
            'PERMIT_EXPIRY_ALERT',
            'DOCUMENT_UPLOADED',
            'SYSTEM_SYNC'
        );

CREATE TYPE entity_type AS ENUM (
            'VEHICLE',
            'DRIVER',
            'TRIP',
            'ROUTE',
            'EXPENSE',
            'MAINTENANCE',
            'TYRE',
            'DOCUMENT',
            'SYSTEM'
        );

CREATE TYPE capture_method AS ENUM (
            'WHATSAPP_BOT',
            'TELEMATICS',
            'MANUAL_ENTRY',
            'API_INTEGRATION',
            'SYSTEM_GENERATED'
        );

CREATE TYPE verification_status AS ENUM (
            'PENDING',
            'VERIFIED',
            'DISPUTED',
            'REJECTED'
        );

CREATE TABLE operational_events (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    event_type event_type NOT NULL, 
    entity_type entity_type NOT NULL, 
    entity_id VARCHAR(255) NOT NULL, 
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    capture_method capture_method NOT NULL, 
    verification_status verification_status DEFAULT 'PENDING' NOT NULL, 
    created_by VARCHAR(255), 
    payload JSONB, 
    event_metadata JSONB, 
    notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    PRIMARY KEY (id)
);

COMMENT ON COLUMN operational_events.id IS 'Globally unique event identifier (UUID v4).';

COMMENT ON COLUMN operational_events.event_type IS 'What happened ù drives processing logic in downstream consumers.';

COMMENT ON COLUMN operational_events.entity_type IS 'The primary fleet entity domain this event concerns.';

COMMENT ON COLUMN operational_events.entity_id IS 'Identifier of the specific entity (vehicle plate, driver UUID, etc.). String type to accommodate heterogeneous entity key formats.';

COMMENT ON COLUMN operational_events.occurred_at IS 'Wall-clock time when the event occurred in the physical world. For offline-captured events this precedes recorded_at.';

COMMENT ON COLUMN operational_events.recorded_at IS 'UTC timestamp when this event was received and stored by the platform.';

COMMENT ON COLUMN operational_events.capture_method IS 'Channel through which this event entered the system.';

COMMENT ON COLUMN operational_events.verification_status IS 'Validation lifecycle state ù updated by the Validation & Enrichment Engine.';

COMMENT ON COLUMN operational_events.created_by IS 'ID of the user or system service that submitted this event. NULL for fully automated / system-generated events.';

COMMENT ON COLUMN operational_events.payload IS 'Event-specific data bag. Schema is owned by the producing service and documented in the Event Catalogue.';

COMMENT ON COLUMN operational_events.event_metadata IS 'Operational metadata: source IP, device ID, app version, correlation IDs, retry counts. Not business data.';

COMMENT ON COLUMN operational_events.notes IS 'Free-text annotation added by a fleet manager during review.';

COMMENT ON COLUMN operational_events.created_at IS 'Row insert timestamp ù managed by the database.';

COMMENT ON COLUMN operational_events.updated_at IS 'Row last-modified timestamp ù managed by the database.';

CREATE INDEX ix_operational_events_event_type ON operational_events (event_type);

CREATE INDEX ix_operational_events_entity_type ON operational_events (entity_type);

CREATE INDEX ix_operational_events_entity_id ON operational_events (entity_id);

CREATE INDEX ix_operational_events_occurred_at ON operational_events (occurred_at);

CREATE INDEX ix_operational_events_verification_status ON operational_events (verification_status);

CREATE INDEX ix_operational_events_created_at ON operational_events (created_at);

CREATE INDEX ix_operational_events_entity ON operational_events (entity_type, entity_id);

UPDATE alembic_version SET version_num='001_operational_event' WHERE alembic_version.version_num = '000_legacy_base';

-- Running upgrade 001_operational_event -> 1a05c613820c

ALTER TABLE trucks RENAME TO vehicles;

ALTER TABLE vehicles RENAME license_plate TO registration_number;

ALTER TABLE vehicles ADD COLUMN vin VARCHAR(50);

ALTER TABLE vehicles ADD COLUMN engine_number VARCHAR(50);

ALTER TABLE vehicles ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL;

ALTER TABLE vehicles ADD COLUMN ownership_info VARCHAR(255);

ALTER TABLE vehicles ADD COLUMN origin_type VARCHAR(50);

ALTER TABLE vehicles ADD COLUMN origin_id VARCHAR(255);

CREATE UNIQUE INDEX ix_vehicles_vin ON vehicles (vin);

CREATE INDEX ix_vehicles_status ON vehicles (status);

ALTER TABLE tickets RENAME truck_id TO vehicle_id;

ALTER TABLE fuel_logs RENAME truck_id TO vehicle_id;

ALTER TABLE fuel_states RENAME truck_id TO vehicle_id;

ALTER TABLE fuel_transactions RENAME truck_id TO vehicle_id;

UPDATE alembic_version SET version_num='1a05c613820c' WHERE alembic_version.version_num = '001_operational_event';

-- Running upgrade 1a05c613820c -> 26b5d244efc9

ALTER TABLE drivers ADD COLUMN employee_id VARCHAR(50);

ALTER TABLE drivers ADD COLUMN license_number VARCHAR(100);

ALTER TABLE drivers ADD COLUMN license_valid_until DATE;

ALTER TABLE drivers ADD COLUMN employment_status VARCHAR(20);

ALTER TABLE drivers ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL;

ALTER TABLE drivers ADD COLUMN origin_type VARCHAR(50);

ALTER TABLE drivers ADD COLUMN origin_id VARCHAR(255);

CREATE UNIQUE INDEX ix_drivers_employee_id ON drivers (employee_id);

CREATE UNIQUE INDEX ix_drivers_license_number ON drivers (license_number);

CREATE INDEX ix_drivers_status ON drivers (status);

ALTER TABLE drivers DROP COLUMN risk_score;

ALTER TABLE drivers DROP COLUMN rating;

ALTER TABLE drivers DROP COLUMN total_trips;

ALTER TABLE drivers DROP COLUMN total_expenses;

ALTER TABLE drivers DROP COLUMN is_active;

UPDATE alembic_version SET version_num='26b5d244efc9' WHERE alembic_version.version_num = '1a05c613820c';

-- Running upgrade 26b5d244efc9 -> a34e738eba91

CREATE TABLE trips (
    id SERIAL NOT NULL, 
    trip_id VARCHAR(255) NOT NULL, 
    status VARCHAR(20) DEFAULT 'CREATED' NOT NULL, 
    origin_location VARCHAR(255), 
    destination_location VARCHAR(255), 
    planned_distance FLOAT, 
    actual_distance FLOAT, 
    planned_start_time TIMESTAMP WITH TIME ZONE, 
    actual_start_time TIMESTAMP WITH TIME ZONE, 
    planned_end_time TIMESTAMP WITH TIME ZONE, 
    actual_end_time TIMESTAMP WITH TIME ZONE, 
    vehicle_id INTEGER, 
    driver_id INTEGER, 
    origin_type VARCHAR(50), 
    origin_id VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(driver_id) REFERENCES drivers (id), 
    FOREIGN KEY(vehicle_id) REFERENCES vehicles (id)
);

CREATE INDEX ix_trips_driver_id ON trips (driver_id);

CREATE INDEX ix_trips_status ON trips (status);

CREATE UNIQUE INDEX ix_trips_trip_id ON trips (trip_id);

CREATE INDEX ix_trips_vehicle_id ON trips (vehicle_id);

UPDATE alembic_version SET version_num='a34e738eba91' WHERE alembic_version.version_num = '26b5d244efc9';

-- Running upgrade a34e738eba91 -> fc992deff131

CREATE TABLE maintenance_records (
    id SERIAL NOT NULL, 
    business_id VARCHAR(255) NOT NULL, 
    status VARCHAR(20) DEFAULT 'CREATED' NOT NULL, 
    category VARCHAR(20) DEFAULT 'PREVENTIVE' NOT NULL, 
    vehicle_id INTEGER, 
    workshop VARCHAR(255), 
    service_provider VARCHAR(255), 
    scheduled_date TIMESTAMP WITH TIME ZONE, 
    completed_date TIMESTAMP WITH TIME ZONE, 
    origin_type VARCHAR(50), 
    origin_id VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(vehicle_id) REFERENCES vehicles (id)
);

CREATE UNIQUE INDEX ix_maintenance_records_business_id ON maintenance_records (business_id);

CREATE INDEX ix_maintenance_records_category ON maintenance_records (category);

CREATE INDEX ix_maintenance_records_status ON maintenance_records (status);

CREATE INDEX ix_maintenance_records_vehicle_id ON maintenance_records (vehicle_id);

CREATE TABLE maintenance_tasks (
    id SERIAL NOT NULL, 
    maintenance_record_id INTEGER NOT NULL, 
    task_type VARCHAR(50) DEFAULT 'OTHER' NOT NULL, 
    description VARCHAR(500) NOT NULL, 
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL, 
    notes TEXT, 
    performed_at TIMESTAMP WITH TIME ZONE, 
    origin_type VARCHAR(50), 
    origin_id VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(maintenance_record_id) REFERENCES maintenance_records (id)
);

CREATE INDEX ix_maintenance_tasks_maintenance_record_id ON maintenance_tasks (maintenance_record_id);

UPDATE alembic_version SET version_num='fc992deff131' WHERE alembic_version.version_num = 'a34e738eba91';

-- Running upgrade fc992deff131 -> 42a8922a1403

CREATE TABLE tyres (
    id SERIAL NOT NULL, 
    serial_number VARCHAR(255) NOT NULL, 
    manufacturer VARCHAR(255), 
    brand VARCHAR(255), 
    model VARCHAR(255), 
    size VARCHAR(50), 
    purchase_information JSON, 
    current_vehicle_id INTEGER, 
    current_position VARCHAR(50), 
    current_status VARCHAR(20) DEFAULT 'REGISTERED' NOT NULL, 
    origin_type VARCHAR(50), 
    origin_id VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(current_vehicle_id) REFERENCES vehicles (id)
);

CREATE UNIQUE INDEX ix_tyres_serial_number ON tyres (serial_number);

CREATE INDEX ix_tyres_current_vehicle_id ON tyres (current_vehicle_id);

CREATE INDEX ix_tyres_current_status ON tyres (current_status);

CREATE TABLE tyre_lifecycle_records (
    id SERIAL NOT NULL, 
    tyre_id INTEGER NOT NULL, 
    event_category VARCHAR(50) NOT NULL, 
    performed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    details JSON, 
    origin_type VARCHAR(50), 
    origin_id VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(tyre_id) REFERENCES tyres (id)
);

CREATE INDEX ix_tyre_lifecycle_records_tyre_id ON tyre_lifecycle_records (tyre_id);

UPDATE alembic_version SET version_num='42a8922a1403' WHERE alembic_version.version_num = 'fc992deff131';

-- Running upgrade 42a8922a1403 -> d27912fc65ad

CREATE TABLE assets (
    id SERIAL NOT NULL, 
    business_id VARCHAR(255) NOT NULL, 
    asset_type VARCHAR(50) NOT NULL, 
    manufacturer VARCHAR(255), 
    model VARCHAR(255), 
    serial_number VARCHAR(255), 
    firmware_version VARCHAR(255), 
    purchase_information JSON, 
    warranty_information JSON, 
    current_vehicle_id INTEGER, 
    installation_status VARCHAR(20) DEFAULT 'REGISTERED' NOT NULL, 
    operational_status VARCHAR(20) DEFAULT 'OK' NOT NULL, 
    origin_type VARCHAR(50), 
    origin_id VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(current_vehicle_id) REFERENCES vehicles (id)
);

CREATE UNIQUE INDEX ix_assets_business_id ON assets (business_id);

CREATE INDEX ix_assets_asset_type ON assets (asset_type);

CREATE INDEX ix_assets_serial_number ON assets (serial_number);

CREATE INDEX ix_assets_current_vehicle_id ON assets (current_vehicle_id);

CREATE INDEX ix_assets_installation_status ON assets (installation_status);

CREATE INDEX ix_assets_operational_status ON assets (operational_status);

CREATE TABLE asset_history_records (
    id SERIAL NOT NULL, 
    asset_id INTEGER NOT NULL, 
    event_category VARCHAR(50) NOT NULL, 
    performed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    details JSON, 
    origin_type VARCHAR(50), 
    origin_id VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(asset_id) REFERENCES assets (id)
);

CREATE INDEX ix_asset_history_records_asset_id ON asset_history_records (asset_id);

UPDATE alembic_version SET version_num='d27912fc65ad' WHERE alembic_version.version_num = '42a8922a1403';

-- Running upgrade d27912fc65ad -> e5653c63763b

CREATE TABLE processing_records (
    id SERIAL NOT NULL, 
    event_id VARCHAR(36) NOT NULL, 
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL, 
    domains_invoked JSON, 
    domains_failed JSON, 
    started_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    execution_ms INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_processing_records_event_id ON processing_records (event_id);

CREATE INDEX ix_processing_records_status ON processing_records (status);

UPDATE alembic_version SET version_num='e5653c63763b' WHERE alembic_version.version_num = 'd27912fc65ad';

-- Running upgrade e5653c63763b -> 8569eb5c85cd

CREATE TABLE expenses (
    id SERIAL NOT NULL, 
    category VARCHAR(50) NOT NULL, 
    amount FLOAT NOT NULL, 
    currency VARCHAR(3) DEFAULT 'INR' NOT NULL, 
    status VARCHAR(50) DEFAULT 'RECORDED' NOT NULL, 
    expense_date TIMESTAMP WITH TIME ZONE NOT NULL, 
    description TEXT, 
    receipt_reference VARCHAR(255), 
    business_id VARCHAR(255) NOT NULL, 
    vehicle_id INTEGER, 
    driver_id INTEGER, 
    trip_id INTEGER, 
    maintenance_id INTEGER, 
    origin_type VARCHAR(100) DEFAULT 'verified_event' NOT NULL, 
    origin_id VARCHAR(255) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_expenses_category ON expenses (category);

CREATE INDEX ix_expenses_status ON expenses (status);

CREATE UNIQUE INDEX ix_expenses_business_id ON expenses (business_id);

CREATE INDEX ix_expenses_vehicle_id ON expenses (vehicle_id);

CREATE INDEX ix_expenses_driver_id ON expenses (driver_id);

CREATE INDEX ix_expenses_trip_id ON expenses (trip_id);

CREATE INDEX ix_expenses_maintenance_id ON expenses (maintenance_id);

UPDATE alembic_version SET version_num='8569eb5c85cd' WHERE alembic_version.version_num = 'e5653c63763b';

-- Running upgrade 8569eb5c85cd -> d1c8e33c06eb

CREATE TYPE metric_entity_type AS ENUM ('TRUCK', 'TRIP', 'DRIVER', 'FLEET');

CREATE TYPE fuel_metric_type AS ENUM ('FUEL_EFFICIENCY', 'FUEL_CONSUMPTION');

CREATE TYPE fuel_source_type AS ENUM ('FUEL_SENSOR', 'FUEL_TRANSACTION', 'ODOMETER_FUEL', 'MANUAL_ENTRY', 'EXTERNAL_TELEMATICS', 'ESTIMATED');

CREATE TYPE fuel_data_quality AS ENUM ('HIGH', 'MEDIUM', 'LOW', 'INSUFFICIENT');

CREATE TYPE fuel_measurement_type AS ENUM ('MEASURED', 'DERIVED', 'ESTIMATED');

CREATE TABLE derived_fuel_metrics (
    id SERIAL NOT NULL, 
    entity_id VARCHAR(50) NOT NULL, 
    entity_type metric_entity_type NOT NULL, 
    metric_type fuel_metric_type NOT NULL, 
    value FLOAT NOT NULL, 
    unit VARCHAR(20) NOT NULL, 
    source fuel_source_type NOT NULL, 
    quality fuel_data_quality NOT NULL, 
    measurement_type fuel_measurement_type NOT NULL, 
    period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
    period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
    sample_size INTEGER NOT NULL, 
    source_reference VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

COMMENT ON COLUMN derived_fuel_metrics.source_reference IS 'Traceability to operational data';

CREATE INDEX ix_derived_fuel_metrics_entity_id ON derived_fuel_metrics (entity_id);

CREATE INDEX ix_derived_fuel_metrics_entity_period ON derived_fuel_metrics (entity_type, entity_id, period_start, period_end);

CREATE INDEX ix_derived_fuel_metrics_entity_type ON derived_fuel_metrics (entity_type);

CREATE INDEX ix_derived_fuel_metrics_metric_type ON derived_fuel_metrics (metric_type);

CREATE INDEX ix_derived_fuel_metrics_period_end ON derived_fuel_metrics (period_end);

CREATE INDEX ix_derived_fuel_metrics_period_start ON derived_fuel_metrics (period_start);

UPDATE alembic_version SET version_num='d1c8e33c06eb' WHERE alembic_version.version_num = '8569eb5c85cd';

-- Running upgrade d1c8e33c06eb -> 8a0da79d278c

CREATE TYPE baseline_entity_type AS ENUM ('TRUCK', 'TRIP', 'DRIVER', 'FLEET');

CREATE TYPE baseline_fuel_metric_type AS ENUM ('FUEL_EFFICIENCY', 'FUEL_CONSUMPTION');

CREATE TYPE baseline_data_quality AS ENUM ('HIGH', 'MEDIUM', 'LOW', 'INSUFFICIENT');

CREATE TYPE baseline_status AS ENUM ('VALID', 'INSUFFICIENT_DATA');

CREATE TABLE entity_baselines (
    id SERIAL NOT NULL, 
    entity_id VARCHAR(50) NOT NULL, 
    entity_type baseline_entity_type NOT NULL, 
    metric_type baseline_fuel_metric_type NOT NULL, 
    baseline_value FLOAT NOT NULL, 
    unit VARCHAR(20) NOT NULL, 
    sample_size INTEGER NOT NULL, 
    calculation_method VARCHAR(50) NOT NULL, 
    data_quality baseline_data_quality NOT NULL, 
    status baseline_status NOT NULL, 
    period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
    period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uix_entity_baseline_period UNIQUE (entity_id, entity_type, metric_type, period_start, period_end)
);

CREATE INDEX ix_entity_baselines_entity_id ON entity_baselines (entity_id);

CREATE INDEX ix_entity_baselines_entity_type ON entity_baselines (entity_type);

CREATE INDEX ix_entity_baselines_lookup ON entity_baselines (entity_id, entity_type, metric_type);

CREATE INDEX ix_entity_baselines_metric_type ON entity_baselines (metric_type);

UPDATE alembic_version SET version_num='8a0da79d278c' WHERE alembic_version.version_num = 'd1c8e33c06eb';

-- Running upgrade 8a0da79d278c -> 2332f04ea585

CREATE TYPE anomaly_entity_type AS ENUM ('TRUCK', 'TRIP', 'DRIVER', 'FLEET');

CREATE TYPE anomaly_fuel_metric_type AS ENUM ('FUEL_EFFICIENCY', 'FUEL_CONSUMPTION');

CREATE TYPE anomaly_direction AS ENUM ('DEGRADATION', 'IMPROVEMENT', 'NORMAL');

CREATE TYPE anomaly_severity AS ENUM ('CRITICAL', 'WARNING', 'NORMAL');

CREATE TYPE anomaly_status AS ENUM ('ANOMALY', 'NORMAL', 'INSUFFICIENT_DATA');

CREATE TABLE fuel_anomalies (
    id SERIAL NOT NULL, 
    entity_id VARCHAR(50) NOT NULL, 
    entity_type anomaly_entity_type NOT NULL, 
    metric_type anomaly_fuel_metric_type NOT NULL, 
    baseline_value FLOAT NOT NULL, 
    observed_value FLOAT NOT NULL, 
    deviation_percent FLOAT NOT NULL, 
    direction anomaly_direction NOT NULL, 
    severity anomaly_severity NOT NULL, 
    status anomaly_status NOT NULL, 
    baseline_reference VARCHAR(255) NOT NULL, 
    observation_reference VARCHAR(255) NOT NULL, 
    period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
    period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uix_fuel_anomaly_observation UNIQUE (observation_reference)
);

CREATE INDEX ix_fuel_anomalies_entity_id ON fuel_anomalies (entity_id);

CREATE INDEX ix_fuel_anomalies_entity_type ON fuel_anomalies (entity_type);

CREATE INDEX ix_fuel_anomalies_lookup ON fuel_anomalies (entity_id, entity_type, metric_type);

CREATE INDEX ix_fuel_anomalies_metric_type ON fuel_anomalies (metric_type);

CREATE INDEX ix_fuel_anomalies_observation_reference ON fuel_anomalies (observation_reference);

UPDATE alembic_version SET version_num='2332f04ea585' WHERE alembic_version.version_num = '8a0da79d278c';

-- Running upgrade 2332f04ea585 -> 086c2d1e25f7

CREATE TYPE impact_entity_type AS ENUM ('TRUCK', 'TRIP', 'DRIVER', 'FLEET');

CREATE TYPE impact_metric_type AS ENUM ('FUEL_EFFICIENCY', 'FUEL_CONSUMPTION');

CREATE TYPE fuel_price_source AS ENUM ('ACTUAL_PURCHASE_PRICE', 'VOLUME_WEIGHTED_PURCHASE_PRICE', 'VERIFIED_HISTORICAL_REFERENCE');

CREATE TABLE fuel_financial_impacts (
    id SERIAL NOT NULL, 
    entity_id VARCHAR(50) NOT NULL, 
    entity_type impact_entity_type NOT NULL, 
    metric_type impact_metric_type NOT NULL, 
    baseline_efficiency FLOAT NOT NULL, 
    observed_efficiency FLOAT NOT NULL, 
    distance FLOAT NOT NULL, 
    expected_fuel_liters FLOAT NOT NULL, 
    implied_fuel_liters FLOAT NOT NULL, 
    excess_fuel_liters FLOAT NOT NULL, 
    fuel_price_per_liter FLOAT NOT NULL, 
    fuel_price_source fuel_price_source NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    estimated_financial_exposure FLOAT NOT NULL, 
    anomaly_reference VARCHAR(255) NOT NULL, 
    baseline_reference VARCHAR(255) NOT NULL, 
    observation_reference VARCHAR(255) NOT NULL, 
    period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
    period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
    calculation_method VARCHAR(100) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_fuel_financial_impacts_anomaly_reference ON fuel_financial_impacts (anomaly_reference);

CREATE INDEX ix_fuel_financial_impacts_entity_id ON fuel_financial_impacts (entity_id);

CREATE INDEX ix_fuel_financial_impacts_entity_type ON fuel_financial_impacts (entity_type);

CREATE INDEX ix_fuel_financial_impacts_metric_type ON fuel_financial_impacts (metric_type);

UPDATE alembic_version SET version_num='086c2d1e25f7' WHERE alembic_version.version_num = '2332f04ea585';

-- Running upgrade 086c2d1e25f7 -> 9dae99ddd519

CREATE TYPE rc_entity_type AS ENUM ('TRUCK', 'TRIP', 'DRIVER', 'FLEET');

CREATE TABLE fuel_root_cause_analyses (
    id SERIAL NOT NULL, 
    anomaly_reference VARCHAR(255) NOT NULL, 
    financial_impact_reference VARCHAR(255), 
    entity_id VARCHAR(50) NOT NULL, 
    entity_type rc_entity_type NOT NULL, 
    period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
    period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
    status VARCHAR(50) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_fuel_root_cause_analyses_anomaly_reference ON fuel_root_cause_analyses (anomaly_reference);

CREATE INDEX ix_fuel_root_cause_analyses_entity_id ON fuel_root_cause_analyses (entity_id);

CREATE TYPE root_cause_type AS ENUM ('EXCESSIVE_IDLE', 'HIGH_SPEED', 'EXCESS_DISTANCE', 'FUEL_EVENT_ANOMALY', 'VEHICLE_MAINTENANCE', 'DRIVER_BEHAVIOUR', 'UNKNOWN');

CREATE TYPE evidence_status AS ENUM ('SUPPORTING', 'NEUTRAL', 'CONTRADICTING', 'UNAVAILABLE');

CREATE TYPE evidence_strength AS ENUM ('NO_EVIDENCE', 'WEAK_SUPPORT', 'MODERATE_SUPPORT', 'STRONG_SUPPORT');

CREATE TABLE fuel_root_cause_evidence (
    id SERIAL NOT NULL, 
    analysis_id INTEGER NOT NULL, 
    cause_type root_cause_type NOT NULL, 
    evidence_status evidence_status NOT NULL, 
    evidence_strength evidence_strength NOT NULL, 
    evidence_value FLOAT, 
    baseline_value FLOAT, 
    deviation_percent FLOAT, 
    unit VARCHAR(50), 
    explanation TEXT NOT NULL, 
    source_references TEXT, 
    rank INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(analysis_id) REFERENCES fuel_root_cause_analyses (id)
);

COMMENT ON COLUMN fuel_root_cause_evidence.source_references IS 'Comma-separated IDs';

CREATE INDEX ix_fuel_root_cause_evidence_analysis_id ON fuel_root_cause_evidence (analysis_id);

UPDATE alembic_version SET version_num='9dae99ddd519' WHERE alembic_version.version_num = '086c2d1e25f7';

-- Running upgrade 9dae99ddd519 -> 123abc456def

ALTER TABLE fuel_financial_impacts ADD COLUMN baseline_value FLOAT;

ALTER TABLE fuel_financial_impacts ADD COLUMN observed_value FLOAT;

ALTER TABLE fuel_financial_impacts ADD COLUMN domain_context JSONB;

UPDATE alembic_version SET version_num='123abc456def' WHERE alembic_version.version_num = '9dae99ddd519';

-- Running upgrade 123abc456def -> 005a340d1e3d

CREATE TABLE owner_pairing_tokens (
    id SERIAL NOT NULL, 
    company_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    pairing_token VARCHAR(255) NOT NULL, 
    is_used BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_owner_pairing_tokens_company_id ON owner_pairing_tokens (company_id);

CREATE UNIQUE INDEX ix_owner_pairing_tokens_pairing_token ON owner_pairing_tokens (pairing_token);

CREATE INDEX ix_owner_pairing_tokens_user_id ON owner_pairing_tokens (user_id);

UPDATE alembic_version SET version_num='005a340d1e3d' WHERE alembic_version.version_num = '123abc456def';

-- Running upgrade 005a340d1e3d -> dcff6780ab29

ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

ALTER TABLE users ADD COLUMN mobile_number VARCHAR(20);

ALTER TABLE users ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT now();

ALTER TABLE users ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();

ALTER TABLE users RENAME hashed_password TO password_hash;

CREATE UNIQUE INDEX ix_users_mobile_number ON users (mobile_number);

CREATE UNIQUE INDEX ix_users_email ON users (email);

UPDATE alembic_version SET version_num='dcff6780ab29' WHERE alembic_version.version_num = '005a340d1e3d';

-- Running upgrade dcff6780ab29 -> 5b6ce0e2b9a8

ALTER TABLE companies RENAME name TO company_name;

ALTER TABLE companies ADD COLUMN owner_name VARCHAR(255);

ALTER TABLE companies ADD COLUMN mobile_number VARCHAR(20);

ALTER TABLE companies ADD COLUMN email VARCHAR(255);

ALTER TABLE companies ADD COLUMN status VARCHAR(50) DEFAULT 'ACTIVE';

ALTER TABLE companies ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT now();

ALTER TABLE companies ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();

UPDATE alembic_version SET version_num='5b6ce0e2b9a8' WHERE alembic_version.version_num = 'dcff6780ab29';

-- Running upgrade 5b6ce0e2b9a8 -> c4683c6b38c6

CREATE TABLE auth_sessions (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    company_id INTEGER NOT NULL, 
    session_jti VARCHAR(128) NOT NULL, 
    remember_me BOOLEAN NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    revoked_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_auth_sessions_company_id ON auth_sessions (company_id);

CREATE INDEX ix_auth_sessions_expires_at ON auth_sessions (expires_at);

CREATE UNIQUE INDEX ix_auth_sessions_session_jti ON auth_sessions (session_jti);

CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id);

CREATE TABLE password_reset_tokens (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    company_id INTEGER NOT NULL, 
    token_hash VARCHAR(128) NOT NULL, 
    requested_identifier VARCHAR(255) NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    used_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_password_reset_tokens_company_id ON password_reset_tokens (company_id);

CREATE INDEX ix_password_reset_tokens_expires_at ON password_reset_tokens (expires_at);

CREATE UNIQUE INDEX ix_password_reset_tokens_token_hash ON password_reset_tokens (token_hash);

CREATE INDEX ix_password_reset_tokens_user_id ON password_reset_tokens (user_id);

UPDATE alembic_version SET version_num='c4683c6b38c6' WHERE alembic_version.version_num = '5b6ce0e2b9a8';

-- Running upgrade c4683c6b38c6 -> a1b2c3d4e5f6

ALTER TABLE vehicles ADD COLUMN make VARCHAR(100);

ALTER TABLE vehicles ADD COLUMN model VARCHAR(100);

ALTER TABLE vehicles ADD COLUMN year INTEGER;

ALTER TABLE vehicles ADD COLUMN tank_capacity FLOAT DEFAULT '400.0' NOT NULL;

ALTER TABLE vehicles ADD COLUMN assigned_driver_id INTEGER;

ALTER TABLE vehicles ADD CONSTRAINT fk_vehicles_assigned_driver_id FOREIGN KEY(assigned_driver_id) REFERENCES drivers (id) ON DELETE SET NULL;

CREATE INDEX ix_vehicles_assigned_driver_id ON vehicles (assigned_driver_id);

UPDATE alembic_version SET version_num='a1b2c3d4e5f6' WHERE alembic_version.version_num = 'c4683c6b38c6';

-- Running upgrade a1b2c3d4e5f6 -> b2c3d4e5f6g7

UPDATE alembic_version SET version_num='b2c3d4e5f6g7' WHERE alembic_version.version_num = 'a1b2c3d4e5f6';

-- Running upgrade b2c3d4e5f6g7 -> c3d4e5f6g7h8

ALTER TABLE drivers RENAME phone TO phone_number;

CREATE UNIQUE INDEX ix_drivers_phone_number ON drivers (phone_number);

ALTER TABLE drivers ADD COLUMN avatar_url VARCHAR(500);

ALTER TABLE drivers ADD COLUMN user_id INTEGER;

ALTER TABLE drivers ADD CONSTRAINT fk_drivers_users_id FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL;

ALTER TABLE drivers ADD CONSTRAINT uq_drivers_user_id UNIQUE (user_id);

ALTER TABLE drivers ADD COLUMN license_front_url VARCHAR(500);

ALTER TABLE drivers ADD COLUMN license_back_url VARCHAR(500);

ALTER TABLE drivers ADD COLUMN aadhaar_front_url VARCHAR(500);

ALTER TABLE drivers ADD COLUMN aadhaar_back_url VARCHAR(500);

ALTER TABLE drivers ADD COLUMN selfie_url VARCHAR(500);

ALTER TABLE drivers ADD COLUMN aadhaar_number VARCHAR(20);

ALTER TABLE drivers ADD COLUMN verification_status VARCHAR(50);

CREATE INDEX ix_drivers_verification_status ON drivers (verification_status);

ALTER TABLE drivers ADD COLUMN face_verified BOOLEAN;

ALTER TABLE drivers ADD COLUMN duty_status VARCHAR(50);

ALTER TABLE drivers ADD COLUMN last_known_lat FLOAT;

ALTER TABLE drivers ADD COLUMN last_known_lng FLOAT;

ALTER TABLE drivers ADD COLUMN last_location_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE drivers ADD COLUMN fcm_token VARCHAR(500);

ALTER TABLE drivers ADD COLUMN driver_score FLOAT DEFAULT '85.0';

UPDATE alembic_version SET version_num='c3d4e5f6g7h8' WHERE alembic_version.version_num = 'b2c3d4e5f6g7';

-- Running upgrade c3d4e5f6g7h8 -> d4e5f6g7h8i9

ALTER TABLE trips ADD COLUMN company_id INTEGER;

ALTER TABLE trips ADD COLUMN revenue FLOAT;

ALTER TABLE trips ADD COLUMN planned_cost FLOAT;

ALTER TABLE trips ADD COLUMN planned_fuel_liters FLOAT;

ALTER TABLE trips ADD COLUMN cargo_weight FLOAT;

UPDATE trips SET company_id = 1 WHERE company_id IS NULL;

ALTER TABLE trips ALTER COLUMN company_id SET NOT NULL;

ALTER TABLE trips ADD CONSTRAINT fk_trips_companies_id FOREIGN KEY(company_id) REFERENCES companies (id);

CREATE INDEX ix_trips_company_id ON trips (company_id);

UPDATE alembic_version SET version_num='d4e5f6g7h8i9' WHERE alembic_version.version_num = 'c3d4e5f6g7h8';

-- Running upgrade d4e5f6g7h8i9 -> c2557519ddca

ALTER TYPE ticketstatus RENAME TO old_ticketstatus;

ALTER TYPE risklevel RENAME TO old_risklevel;

CREATE TYPE ticketstatus AS ENUM('pending', 'approved', 'rejected');

CREATE TYPE risklevel AS ENUM('Low', 'Medium', 'High', 'Critical');

ALTER TABLE tickets 
        ALTER COLUMN status TYPE ticketstatus 
        USING CASE status::text 
            WHEN 'OPEN' THEN 'pending'::ticketstatus 
            WHEN 'IN_PROGRESS' THEN 'pending'::ticketstatus
            WHEN 'RESOLVED' THEN 'approved'::ticketstatus
            WHEN 'CLOSED' THEN 'approved'::ticketstatus
            WHEN 'REJECTED' THEN 'rejected'::ticketstatus
            ELSE 'pending'::ticketstatus 
        END;

ALTER TABLE tickets 
        ALTER COLUMN risk_level TYPE risklevel 
        USING CASE risk_level::text 
            WHEN 'LOW' THEN 'Low'::risklevel 
            WHEN 'MEDIUM' THEN 'Medium'::risklevel
            WHEN 'HIGH' THEN 'High'::risklevel
            WHEN 'CRITICAL' THEN 'Critical'::risklevel
            ELSE 'Low'::risklevel 
        END;

DROP TYPE old_ticketstatus;

DROP TYPE old_risklevel;

UPDATE alembic_version SET version_num='c2557519ddca' WHERE alembic_version.version_num = 'd4e5f6g7h8i9';

COMMIT;

