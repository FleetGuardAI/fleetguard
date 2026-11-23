# FleetGuard TMS — Disaster Recovery Runbook & Business Continuity Plan (FG-SEC-022)

## 1. Executive Summary & Recovery Objectives

FleetGuard TMS maintains strict business continuity and disaster recovery metrics to ensure data integrity and high availability for fleet management, telemetry ingestion, and regulatory compliance.

* **Recovery Point Objective (RPO)**: $\le 15$ minutes (maximum acceptable data loss window)
* **Recovery Time Objective (RTO)**: $\le 30$ minutes (maximum acceptable downtime until system restoration)
* **Primary Database**: PostgreSQL 16+ with Row-Level Security (RLS) enabled
* **Storage Provider**: Supabase Storage / AWS S3 with server-side encryption (SSE-KMS)

---

## 2. Backup Architecture & Automation

### 2.1 Backup Automation Script
Backups are orchestrated via `backend/scripts/backup_database.py`, which performs:
1. Connection parameter normalization and credential isolation.
2. Compressed binary dump (`pg_dump ... | gzip`).
3. Automated archive integrity validation (`\x1f\x8b` magic byte check and non-empty stream validation).
4. Rolling retention pruning (default 7 days local retention, 30 days off-site).

### 2.2 Scheduled Execution (Cron / Systemd Timer)
Run daily at 02:00 UTC and every 6 hours for point-in-time snapshots:
```bash
# Add to crontab
0 2 * * * cd /opt/fleetguard && python backend/scripts/backup_database.py --output-dir /var/backups/fleetguard --retention-days 7
```

### 2.3 Off-Site Replication
Generated archives (`fleetguard_backup_<dbname>_<timestamp>.sql.gz`) are synced immediately to secondary geographic object storage:
```bash
aws s3 sync /var/backups/fleetguard s3://fleetguard-dr-backups-ap-south-1/database/ --sse aws:kms
```

---

## 3. Disaster Recovery Restoration Runbook

In the event of database corruption, regional cloud outage, or ransomware incident, follow these step-by-step restoration procedures:

### Step 1: Incident Assessment & Traffic Isolation
1. Declare Severity 1 Incident in the incident response channel.
2. Put API gateways (FastAPI / Nginx / Cloudflare) into Maintenance Mode to prevent split-brain writes:
   ```bash
   # Route ingress to maintenance page
   systemctl stop fleetguard-backend
   ```

### Step 2: Retrieve & Verify Target Backup Archive
1. Identify the latest valid backup archive:
   ```bash
   ls -la /var/backups/fleetguard/
   ```
2. Verify archive integrity before applying:
   ```bash
   python backend/scripts/backup_database.py --verify-only /var/backups/fleetguard/fleetguard_backup_fleetguard_latest.sql.gz
   ```

### Step 3: Database Restoration
1. If the database instance is reachable, recreate clean target database:
   ```bash
   dropdb -h $DB_HOST -U postgres fleetguard
   createdb -h $DB_HOST -U postgres -O fleetguard_user fleetguard
   ```
2. Restore schema, tables, functions, and data:
   ```bash
   gunzip -c /var/backups/fleetguard/fleetguard_backup_fleetguard_latest.sql.gz | psql -h $DB_HOST -U postgres -d fleetguard
   ```

### Step 4: Alembic Migration Head Verification
1. Verify Alembic migration state and apply any intermediate schema deltas:
   ```bash
   cd /opt/fleetguard/backend
   alembic current
   alembic upgrade head
   ```
2. Confirm unified single head:
   ```bash
   alembic heads
   ```

### Step 5: Post-Restoration Integrity Verification
1. Run database sanity queries:
   ```sql
   SELECT count(*) FROM companies;
   SELECT count(*) FROM users;
   SELECT count(*) FROM vehicles;
   SELECT count(*) FROM drivers;
   ```
2. Verify RLS policies and encryption keys:
   ```bash
   pytest tests/security/test_rls_tenant_isolation.py -v
   pytest tests/security/test_pii_encryption_at_rest.py -v
   ```

### Step 6: Traffic Resumption & Post-Mortem
1. Restart application services:
   ```bash
   systemctl start fleetguard-backend
   ```
2. Verify API health check:
   ```bash
   curl -f http://localhost:8000/
   ```
3. Disable maintenance mode and notify stakeholders.
4. Schedule post-incident review within 48 hours.

---

## 4. Quarterly DR Verification Drills
Every 90 days, the DevOps and Security team must execute a dry-run restoration drill into an isolated staging environment to validate that RTO $\le 30$ minutes and RPO $\le 15$ minutes remain achievable.
