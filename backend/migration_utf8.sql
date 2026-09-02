BEGIN;

-- Running upgrade d54845acfb95 -> b6b360db6af8

CREATE TABLE documents (
    id UUID NOT NULL, 
    original_filename VARCHAR(255) NOT NULL, 
    mime_type VARCHAR(100) NOT NULL, 
    storage_path VARCHAR(1024) NOT NULL, 
    status VARCHAR(50) NOT NULL, 
    uploaded_by VARCHAR(255), 
    company_id INTEGER, 
    name VARCHAR(255), 
    category VARCHAR(100), 
    expiry_date VARCHAR(50), 
    target_id VARCHAR(100), 
    target_type VARCHAR(50), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_documents_company_id ON documents (company_id);

CREATE INDEX ix_documents_id ON documents (id);

CREATE INDEX ix_documents_status ON documents (status);

CREATE INDEX ix_documents_target_id ON documents (target_id);

CREATE INDEX ix_documents_target_type ON documents (target_type);

CREATE TYPE outboxstatus AS ENUM ('PENDING', 'PUBLISHING', 'PUBLISHED');

CREATE TABLE outbox_events (
    id SERIAL NOT NULL, 
    event_id VARCHAR(36), 
    topic VARCHAR(255) NOT NULL, 
    payload JSON NOT NULL, 
    headers JSON, 
    status outboxstatus NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    published_at TIMESTAMP WITH TIME ZONE, 
    retry_count INTEGER NOT NULL, 
    last_error VARCHAR, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_outbox_events_event_id ON outbox_events (event_id);

CREATE INDEX ix_outbox_events_status ON outbox_events (status);

CREATE TABLE processed_events (
    id SERIAL NOT NULL, 
    operational_event_id VARCHAR(36) NOT NULL, 
    domain_name VARCHAR(255) NOT NULL, 
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    processing_result VARCHAR(50) NOT NULL, 
    metadata_payload JSON, 
    PRIMARY KEY (id), 
    UNIQUE (operational_event_id, domain_name)
);

CREATE INDEX ix_processed_events_domain_name ON processed_events (domain_name);

CREATE INDEX ix_processed_events_operational_event_id ON processed_events (operational_event_id);

CREATE TABLE evidence (
    id UUID NOT NULL, 
    event_id UUID NOT NULL, 
    evidence_type VARCHAR(50) NOT NULL, 
    source VARCHAR(255) NOT NULL, 
    status VARCHAR(50) NOT NULL, 
    summary VARCHAR(500) NOT NULL, 
    details TEXT, 
    raw_data JSON, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(event_id) REFERENCES operational_events (id) ON DELETE CASCADE
);

CREATE INDEX ix_evidence_event_id ON evidence (event_id);

CREATE INDEX ix_evidence_evidence_type ON evidence (evidence_type);

CREATE INDEX ix_evidence_id ON evidence (id);

CREATE INDEX ix_evidence_status ON evidence (status);

CREATE TABLE driver_locations (
    id SERIAL NOT NULL, 
    driver_id INTEGER NOT NULL, 
    company_id INTEGER NOT NULL, 
    latitude FLOAT NOT NULL, 
    longitude FLOAT NOT NULL, 
    speed FLOAT, 
    heading FLOAT, 
    accuracy FLOAT, 
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL, 
    battery_percent INTEGER, 
    activity_state VARCHAR(50), 
    source VARCHAR(50) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
    FOREIGN KEY(driver_id) REFERENCES drivers (id) ON DELETE CASCADE
);

COMMENT ON COLUMN driver_locations.speed IS 'Speed in m/s';

COMMENT ON COLUMN driver_locations.heading IS 'Heading in degrees';

COMMENT ON COLUMN driver_locations.accuracy IS 'GPS accuracy in meters';

COMMENT ON COLUMN driver_locations.timestamp IS 'When this position was recorded on the device';

COMMENT ON COLUMN driver_locations.activity_state IS 'Device activity: DRIVING, WALKING, STATIONARY, etc.';

CREATE INDEX ix_driver_locations_company_id ON driver_locations (company_id);

CREATE INDEX ix_driver_locations_driver_id ON driver_locations (driver_id);

CREATE INDEX ix_driver_locations_timestamp ON driver_locations (timestamp);

CREATE TABLE location_alerts (
    id SERIAL NOT NULL, 
    driver_id INTEGER NOT NULL, 
    company_id INTEGER NOT NULL, 
    alert_type VARCHAR(50) NOT NULL, 
    details VARCHAR(500), 
    latitude FLOAT, 
    longitude FLOAT, 
    is_resolved BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
    FOREIGN KEY(driver_id) REFERENCES drivers (id) ON DELETE CASCADE
);

CREATE INDEX ix_location_alerts_alert_type ON location_alerts (alert_type);

CREATE INDEX ix_location_alerts_company_id ON location_alerts (company_id);

CREATE INDEX ix_location_alerts_driver_id ON location_alerts (driver_id);

CREATE TABLE wallet_transactions (
    id SERIAL NOT NULL, 
    driver_id INTEGER NOT NULL, 
    company_id INTEGER NOT NULL, 
    transaction_type VARCHAR(50) NOT NULL, 
    amount FLOAT NOT NULL, 
    status VARCHAR(50) NOT NULL, 
    description TEXT, 
    reference_id VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    processed_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
    FOREIGN KEY(driver_id) REFERENCES drivers (id) ON DELETE CASCADE
);

CREATE INDEX ix_wallet_transactions_company_id ON wallet_transactions (company_id);

CREATE INDEX ix_wallet_transactions_driver_id ON wallet_transactions (driver_id);

CREATE INDEX ix_wallet_transactions_transaction_type ON wallet_transactions (transaction_type);

CREATE TABLE vehicle_inspections (
    id SERIAL NOT NULL, 
    driver_id INTEGER NOT NULL, 
    vehicle_id INTEGER NOT NULL, 
    company_id INTEGER NOT NULL, 
    inspection_type VARCHAR(50) NOT NULL, 
    overall_status VARCHAR(50) NOT NULL, 
    items JSON NOT NULL, 
    notes VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
    FOREIGN KEY(driver_id) REFERENCES drivers (id) ON DELETE CASCADE, 
    FOREIGN KEY(vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
);

COMMENT ON COLUMN vehicle_inspections.items IS 'Checklist items: {item_name: {status, notes, photo_url}}';

CREATE INDEX ix_vehicle_inspections_company_id ON vehicle_inspections (company_id);

CREATE INDEX ix_vehicle_inspections_driver_id ON vehicle_inspections (driver_id);

CREATE INDEX ix_vehicle_inspections_inspection_type ON vehicle_inspections (inspection_type);

CREATE INDEX ix_vehicle_inspections_vehicle_id ON vehicle_inspections (vehicle_id);

CREATE TABLE emergency_alerts (
    id SERIAL NOT NULL, 
    driver_id INTEGER NOT NULL, 
    company_id INTEGER NOT NULL, 
    vehicle_id INTEGER, 
    trip_id INTEGER, 
    latitude FLOAT, 
    longitude FLOAT, 
    status VARCHAR(50) NOT NULL, 
    message VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    resolved_at TIMESTAMP WITH TIME ZONE, 
    resolved_by VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
    FOREIGN KEY(driver_id) REFERENCES drivers (id) ON DELETE CASCADE, 
    FOREIGN KEY(trip_id) REFERENCES trips (id), 
    FOREIGN KEY(vehicle_id) REFERENCES vehicles (id)
);

CREATE INDEX ix_emergency_alerts_company_id ON emergency_alerts (company_id);

CREATE INDEX ix_emergency_alerts_driver_id ON emergency_alerts (driver_id);

CREATE INDEX ix_emergency_alerts_status ON emergency_alerts (status);

CREATE TABLE proof_of_delivery (
    id SERIAL NOT NULL, 
    trip_id INTEGER NOT NULL, 
    driver_id INTEGER NOT NULL, 
    company_id INTEGER NOT NULL, 
    signature_url VARCHAR(500), 
    photos JSON, 
    invoice_url VARCHAR(500), 
    remarks TEXT, 
    receiver_name VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE, 
    FOREIGN KEY(driver_id) REFERENCES drivers (id) ON DELETE CASCADE, 
    FOREIGN KEY(trip_id) REFERENCES trips (id) ON DELETE CASCADE
);

COMMENT ON COLUMN proof_of_delivery.signature_url IS 'URL to customer signature image';

COMMENT ON COLUMN proof_of_delivery.photos IS 'List of delivery photo URLs';

COMMENT ON COLUMN proof_of_delivery.invoice_url IS 'URL to invoice/delivery receipt';

COMMENT ON COLUMN proof_of_delivery.remarks IS 'Delivery remarks or notes';

CREATE INDEX ix_proof_of_delivery_company_id ON proof_of_delivery (company_id);

CREATE INDEX ix_proof_of_delivery_driver_id ON proof_of_delivery (driver_id);

CREATE INDEX ix_proof_of_delivery_trip_id ON proof_of_delivery (trip_id);

COMMENT ON COLUMN asset_history_records.details IS 'Event-specific metadata';

COMMENT ON COLUMN assets.business_id IS 'Authoritative business ID for the asset (e.g. internal tracking ID)';

ALTER TABLE assets ALTER COLUMN installation_status TYPE VARCHAR(50);

ALTER TABLE assets ALTER COLUMN installation_status DROP DEFAULT;

ALTER TABLE assets ALTER COLUMN operational_status TYPE VARCHAR(50);

ALTER TABLE assets ALTER COLUMN operational_status DROP DEFAULT;

COMMENT ON COLUMN companies.company_name IS 'Legal or trading name of the company';

UPDATE companies SET owner_name = (SELECT full_name FROM users WHERE users.company_id = companies.id AND users.role = 'COMPANY_ADMIN' ORDER BY id ASC LIMIT 1) WHERE owner_name IS NULL;

UPDATE companies SET owner_name = company_name WHERE owner_name IS NULL;

ALTER TABLE companies ALTER COLUMN owner_name SET NOT NULL;

COMMENT ON COLUMN companies.owner_name IS 'Full name of the primary company owner';

UPDATE companies SET mobile_number = '+00000000' || id::text WHERE mobile_number IS NULL;

ALTER TABLE companies ALTER COLUMN mobile_number SET NOT NULL;

COMMENT ON COLUMN companies.mobile_number IS 'Primary contact mobile number; must be globally unique';

COMMENT ON COLUMN companies.email IS 'Optional company contact email; must be globally unique if provided';

ALTER TABLE companies ALTER COLUMN status TYPE VARCHAR(20);

ALTER TABLE companies ALTER COLUMN status SET NOT NULL;

COMMENT ON COLUMN companies.status IS 'Account lifecycle status';

ALTER TABLE companies ALTER COLUMN created_at SET NOT NULL;

ALTER TABLE companies ALTER COLUMN updated_at SET NOT NULL;

CREATE INDEX ix_companies_company_name ON companies (company_name);

CREATE UNIQUE INDEX ix_companies_email ON companies (email);

CREATE UNIQUE INDEX ix_companies_mobile_number ON companies (mobile_number);

ALTER TABLE derived_fuel_metrics ALTER COLUMN entity_type TYPE VARCHAR(50);

ALTER TABLE derived_fuel_metrics ALTER COLUMN metric_type TYPE VARCHAR(50);

ALTER TABLE derived_fuel_metrics ALTER COLUMN source TYPE VARCHAR(50);

ALTER TABLE derived_fuel_metrics ALTER COLUMN quality TYPE VARCHAR(50);

ALTER TABLE derived_fuel_metrics ALTER COLUMN measurement_type TYPE VARCHAR(50);

ALTER TABLE drivers ALTER COLUMN name TYPE VARCHAR(150);

ALTER TABLE drivers ALTER COLUMN phone_number TYPE VARCHAR(20);

ALTER TABLE drivers ALTER COLUMN phone_number SET NOT NULL;

COMMENT ON COLUMN drivers.phone_number IS 'WhatsApp phone number in E.164 format (e.g. +919876543210)';

ALTER TABLE drivers ALTER COLUMN company_id DROP NOT NULL;

COMMENT ON COLUMN drivers.company_id IS 'The fleet company this driver belongs to';

COMMENT ON COLUMN drivers.user_id IS 'Linked user account for authentication';

COMMENT ON COLUMN drivers.verification_status IS 'Mobile app onboarding verification status';

ALTER TABLE drivers ALTER COLUMN employment_status TYPE VARCHAR(50);

ALTER TABLE drivers ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE drivers ALTER COLUMN status DROP DEFAULT;

COMMENT ON COLUMN drivers.duty_status IS 'Current duty status from the mobile app';

ALTER TABLE drivers ALTER COLUMN driver_score DROP DEFAULT;

COMMENT ON COLUMN drivers.origin_type IS 'Origin of this state (e.g., ''verified_event'', ''system'')';

COMMENT ON COLUMN drivers.origin_id IS 'Reference ID from the origin (e.g., OperationalEvent ID)';

CREATE INDEX ix_drivers_company_id ON drivers (company_id);

ALTER TABLE drivers DROP CONSTRAINT drivers_company_id_fkey;

ALTER TABLE drivers ADD FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE;

ALTER TABLE entity_baselines ALTER COLUMN entity_type TYPE VARCHAR(50);

ALTER TABLE entity_baselines ALTER COLUMN metric_type TYPE VARCHAR(50);

ALTER TABLE entity_baselines ALTER COLUMN data_quality TYPE VARCHAR(50);

ALTER TABLE entity_baselines ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE expenses ADD COLUMN company_id INTEGER;

ALTER TABLE expenses ALTER COLUMN currency DROP DEFAULT;

ALTER TABLE expenses ALTER COLUMN status DROP DEFAULT;

ALTER TABLE expenses ALTER COLUMN origin_type DROP DEFAULT;

CREATE INDEX ix_expenses_company_id ON expenses (company_id);

ALTER TABLE fuel_anomalies ALTER COLUMN entity_type TYPE VARCHAR(50);

ALTER TABLE fuel_anomalies ALTER COLUMN metric_type TYPE VARCHAR(50);

ALTER TABLE fuel_anomalies ALTER COLUMN direction TYPE VARCHAR(50);

ALTER TABLE fuel_anomalies ALTER COLUMN severity TYPE VARCHAR(50);

ALTER TABLE fuel_anomalies ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE fuel_financial_impacts ALTER COLUMN entity_type TYPE VARCHAR(50);

ALTER TABLE fuel_financial_impacts ALTER COLUMN metric_type TYPE VARCHAR(50);

ALTER TABLE fuel_financial_impacts ALTER COLUMN fuel_price_source TYPE VARCHAR(50);

COMMENT ON COLUMN fuel_logs.timestamp IS 'Timestamp of the sensor reading';

COMMENT ON COLUMN fuel_logs.raw_level IS 'Raw fuel level reading in liters (noisy)';

COMMENT ON COLUMN fuel_logs.filtered_level IS 'EMA-smoothed fuel level in liters';

COMMENT ON COLUMN fuel_logs.expected_level IS 'Expected fuel level based on distance and consumption rate';

COMMENT ON COLUMN fuel_logs.speed IS 'Vehicle speed in km/h at time of reading';

COMMENT ON COLUMN fuel_logs.is_theft_alert IS 'True if this reading triggered a CRITICAL_THEFT alert';

CREATE INDEX ix_fuel_logs_is_theft_alert ON fuel_logs (is_theft_alert);

CREATE INDEX ix_fuel_logs_timestamp ON fuel_logs (timestamp);

CREATE INDEX ix_fuel_logs_vehicle_id ON fuel_logs (vehicle_id);

ALTER TABLE fuel_root_cause_analyses ALTER COLUMN entity_type TYPE VARCHAR(50);

ALTER TABLE fuel_root_cause_evidence ALTER COLUMN cause_type TYPE VARCHAR(50);

ALTER TABLE fuel_root_cause_evidence ALTER COLUMN evidence_status TYPE VARCHAR(50);

ALTER TABLE fuel_root_cause_evidence ALTER COLUMN evidence_strength TYPE VARCHAR(50);

COMMENT ON COLUMN fuel_states.current_level IS 'Current known fuel level in liters';

ALTER TABLE fuel_states ALTER COLUMN source TYPE VARCHAR(50);

COMMENT ON COLUMN fuel_states.source IS 'Origin of this state';

ALTER TABLE fuel_states ALTER COLUMN reliability TYPE VARCHAR(50);

COMMENT ON COLUMN fuel_states.reliability IS 'Business-oriented reliability of the measurement';

COMMENT ON COLUMN fuel_states.last_operational_event_id IS 'Reference ID from the origin (e.g., OperationalEvent ID)';

CREATE UNIQUE INDEX ix_fuel_states_vehicle_id ON fuel_states (vehicle_id);

ALTER TABLE fuel_transactions ALTER COLUMN transaction_type TYPE VARCHAR(50);

COMMENT ON COLUMN fuel_transactions.amount_liters IS 'Amount of fuel changed in liters (can be positive or negative for adjustments)';

COMMENT ON COLUMN fuel_transactions.timestamp IS 'When the transaction occurred';

CREATE INDEX ix_fuel_transactions_timestamp ON fuel_transactions (timestamp);

CREATE INDEX ix_fuel_transactions_transaction_type ON fuel_transactions (transaction_type);

CREATE INDEX ix_fuel_transactions_vehicle_id ON fuel_transactions (vehicle_id);

COMMENT ON COLUMN maintenance_records.business_id IS 'Business identifier for the maintenance event';

ALTER TABLE maintenance_records ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE maintenance_records ALTER COLUMN status DROP DEFAULT;

ALTER TABLE maintenance_records ALTER COLUMN category TYPE VARCHAR(50);

ALTER TABLE maintenance_records ALTER COLUMN category DROP DEFAULT;

ALTER TABLE maintenance_tasks ALTER COLUMN task_type DROP DEFAULT;

ALTER TABLE maintenance_tasks ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE maintenance_tasks ALTER COLUMN status DROP DEFAULT;

ALTER TABLE operational_events ALTER COLUMN id DROP DEFAULT;

ALTER TABLE operational_events ALTER COLUMN event_type TYPE VARCHAR(50);

ALTER TABLE operational_events ALTER COLUMN entity_type TYPE VARCHAR(50);

ALTER TABLE operational_events ALTER COLUMN capture_method TYPE VARCHAR(50);

ALTER TABLE operational_events ALTER COLUMN verification_status TYPE VARCHAR(50);

ALTER TABLE operational_events ALTER COLUMN verification_status DROP DEFAULT;

COMMENT ON COLUMN operational_events.created_by IS 'ID of the user or system service that submitted this event. Null for fully automated / system-generated events.';

ALTER TABLE operational_events ALTER COLUMN payload TYPE JSON;

COMMENT ON COLUMN operational_events.payload IS 'Event-specific data bag.  Schema is owned by the service producing this event_type and documented in the Event Catalogue. Maps to JSONB on PostgreSQL for indexing support.';

ALTER TABLE operational_events ALTER COLUMN event_metadata TYPE JSON;

COMMENT ON COLUMN operational_events.event_metadata IS 'Operational metadata: source IP, device ID, app version, correlation IDs, retry counts, etc.  Not business data. Named event_metadata to avoid SQLAlchemy''s reserved ''metadata''.';

DROP INDEX ix_operational_events_created_at;

DROP INDEX ix_operational_events_entity;

ALTER TABLE processing_records ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE processing_records ALTER COLUMN status DROP DEFAULT;

COMMENT ON COLUMN tickets.issue_type IS 'Category: Tire Puncture, Fuel, Engine Repair, Food, Toll, etc.';

COMMENT ON COLUMN tickets.amount IS 'Claimed amount in INR';

COMMENT ON COLUMN tickets.fair_price IS 'Regional average price for this issue_type';

COMMENT ON COLUMN tickets.receipt_url IS 'URL to the uploaded receipt image';

COMMENT ON COLUMN tickets.ocr_raw_response IS 'Raw JSON response from OpenAI Vision OCR';

ALTER TABLE tickets ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE tickets ALTER COLUMN risk_level TYPE VARCHAR(50);

COMMENT ON COLUMN tickets.risk_reasons IS 'JSON array of reasons for the risk flag';

COMMENT ON COLUMN tickets.expense_date IS 'Date extracted from receipt or reported by driver';

COMMENT ON COLUMN tickets.payout_reference IS 'UPI transaction ID after approval payout';

CREATE INDEX ix_tickets_driver_id ON tickets (driver_id);

CREATE INDEX ix_tickets_status ON tickets (status);

CREATE INDEX ix_tickets_vehicle_id ON tickets (vehicle_id);

COMMENT ON COLUMN trips.trip_id IS 'Business identifier for the trip';

ALTER TABLE trips ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE trips ALTER COLUMN status DROP DEFAULT;

COMMENT ON COLUMN trips.revenue IS 'Trip freight/revenue amount in base currency';

COMMENT ON COLUMN trips.planned_cost IS 'Estimated/budgeted total cost for this trip';

COMMENT ON COLUMN trips.planned_fuel_liters IS 'Planned fuel consumption in liters';

COMMENT ON COLUMN trips.cargo_weight IS 'Cargo weight in tonnes';

COMMENT ON COLUMN trips.origin_type IS 'Origin of this state (e.g., ''verified_event'')';

COMMENT ON COLUMN trips.origin_id IS 'Reference ID from the origin (e.g., OperationalEvent ID)';

COMMENT ON COLUMN tyre_lifecycle_records.details IS 'Event-specific metadata (e.g. tread_depth, repair_cost, workshop_name)';

COMMENT ON COLUMN tyres.serial_number IS 'Authoritative business ID (physical serial number) for the tyre';

ALTER TABLE tyres ALTER COLUMN current_status TYPE VARCHAR(50);

ALTER TABLE tyres ALTER COLUMN current_status DROP DEFAULT;

COMMENT ON COLUMN users.company_id IS 'The company (tenant) this user belongs to';

ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;

COMMENT ON COLUMN users.full_name IS 'User''s full display name';

ALTER TABLE users ALTER COLUMN mobile_number SET NOT NULL;

COMMENT ON COLUMN users.mobile_number IS 'Mobile number used for login; globally unique across all tenants';

ALTER TABLE users ALTER COLUMN email DROP NOT NULL;

COMMENT ON COLUMN users.email IS 'Optional email for login; globally unique if provided';

COMMENT ON COLUMN users.password_hash IS 'bcrypt hash of the user''s password ù NEVER expose in API responses';

ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20);

COMMENT ON COLUMN users.role IS 'Access level / permission role';

ALTER TABLE users ALTER COLUMN is_active SET NOT NULL;

COMMENT ON COLUMN users.is_active IS 'Soft-disable a user without deleting them';

ALTER TABLE users ALTER COLUMN created_at SET NOT NULL;

ALTER TABLE users ALTER COLUMN updated_at SET NOT NULL;

ALTER TABLE users DROP CONSTRAINT users_email_key;

CREATE INDEX ix_users_company_id ON users (company_id);

ALTER TABLE users DROP CONSTRAINT users_company_id_fkey;

ALTER TABLE users ADD FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE;

ALTER TABLE vehicles ALTER COLUMN registration_number TYPE VARCHAR(20);

COMMENT ON COLUMN vehicles.registration_number IS 'Vehicle license plate / registration';

COMMENT ON COLUMN vehicles.vin IS 'Vehicle Identification Number / Chassis Number';

COMMENT ON COLUMN vehicles.engine_number IS 'Engine Number';

ALTER TABLE vehicles ALTER COLUMN tank_capacity DROP DEFAULT;

COMMENT ON COLUMN vehicles.tank_capacity IS 'Fuel tank capacity in liters';

ALTER TABLE vehicles ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE vehicles ALTER COLUMN status DROP DEFAULT;

COMMENT ON COLUMN vehicles.ownership_info IS 'Details about ownership (Leased, Owned, etc.)';

COMMENT ON COLUMN vehicles.origin_type IS 'Origin of this state (e.g., ''verified_event'', ''system'')';

COMMENT ON COLUMN vehicles.origin_id IS 'Reference ID from the origin (e.g., OperationalEvent ID)';

COMMENT ON COLUMN vehicles.assigned_driver_id IS 'Currently assigned driver';

ALTER TABLE vehicles DROP CONSTRAINT trucks_license_plate_key;

CREATE INDEX ix_vehicles_company_id ON vehicles (company_id);

CREATE UNIQUE INDEX ix_vehicles_registration_number ON vehicles (registration_number);

UPDATE alembic_version SET version_num='b6b360db6af8' WHERE alembic_version.version_num = 'd54845acfb95';

COMMIT;

