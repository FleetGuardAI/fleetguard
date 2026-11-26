# Vahan Hardware Assets & Telematics — Staging Deployment Runbook

> **Target Environment**: Staging VPS (Ubuntu 22.04 / 24.04 LTS)  
> **Prerequisites**: Docker Engine 24+, Docker Compose v2, Python 3.12/3.13, PostgreSQL 15+ (or Supabase)

---

## 1. VPS Host Setup & Prerequisites

### 1.1 Operating System Packages
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl ufw fail2ban certbot python3-certbot-nginx libpq-dev
```

### 1.2 Docker Engine & Docker Compose
```bash
# Install official Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Verify
docker --version
docker compose version
```

---

## 2. Firewall Configuration (UFW)

The Traccar telematics gateway accepts raw hardware packets across designated cellular tracker ports. The Vahan backend (`:8000`) must **never** be exposed directly to the public internet; it must only be accessible via the Docker bridge network and reverse proxy.

```bash
# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 1. SSH Management
sudo ufw allow 22/tcp comment "SSH administration"

# 2. Reverse Proxy (HTTPS / Web UI)
sudo ufw allow 80/tcp comment "Certbot HTTP verification"
sudo ufw allow 443/tcp comment "Vahan Web App & Traccar Web UI"

# 3. Hardware GPS Device Ports (Traccar Gateway)
sudo ufw allow 5023/tcp comment "Concox / Jimi GT06 TCP"
sudo ufw allow 5023/udp comment "Concox / Jimi GT06 UDP"
sudo ufw allow 5027/tcp comment "Teltonika Codec 8/8E/16 TCP"
sudo ufw allow 5027/udp comment "Teltonika Codec 8 UDP"
sudo ufw allow 5001/tcp comment "Coban TK103 TCP"
sudo ufw allow 5001/udp comment "Coban TK103 UDP"
sudo ufw allow 5004/tcp comment "Queclink TCP"
sudo ufw allow 5013/tcp comment "Sinotrack H02 TCP"
sudo ufw allow 5008/tcp comment "JT/T 808 TCP"
sudo ufw allow 5140/tcp comment "AIS-140 Indian Government IRNSS TCP"
sudo ufw allow 5140/udp comment "AIS-140 Indian Government IRNSS UDP"
sudo ufw allow 5055/tcp comment "OsmAnd Mobile Tracking HTTP"

# Enable UFW
sudo ufw enable
sudo ufw status verbose
```

---

## 3. Environment Variable Checklist

Create `/opt/vahan/.env` (permissions: `chmod 600 /opt/vahan/.env`):

```bash
# --- Core Application ---
ENVIRONMENT=staging
DEBUG=false
SECRET_KEY=generate_with_openssl_rand_hex_32
ADMIN_JWT_SECRET=generate_with_openssl_rand_hex_32

# --- Database ---
DATABASE_URL=postgresql+asyncpg://postgres:YourSecurePassword@db.staging.thevahan.com:5432/vahan_staging
DATABASE_DIRECT_URL=postgresql://postgres:YourSecurePassword@db.staging.thevahan.com:5432/vahan_staging

# --- Telematics Ingestion Security ---
TELEMATICS_WEBHOOK_SECRET=generate_with_openssl_rand_hex_32
ALLOW_REGISTRATION_ONLY_TELEMATICS=false

# --- Traccar Integration ---
TRACCAR_SERVER_URL=http://vahan-traccar-engine:8082
TRACCAR_ADMIN_USER=admin
TRACCAR_ADMIN_PASSWORD=SetSecureTraccarPassword
```

---

## 4. Database Pre-Deployment & Migration Procedure

### 4.1 Pre-Migration Backup
Before running migrations on staging:
```bash
# Create immediate snapshot
pg_dump -h db.staging.thevahan.com -U postgres -d vahan_staging -Fc -f "/opt/vahan/backups/pre_hardware_migration_$(date +%Y%m%d_%H%M%S).dump"
```

### 4.2 Run Migration
```bash
cd /opt/vahan/backend
source .venv/bin/activate
alembic current
alembic upgrade head
alembic current
```
*Expected Head*: `a2b3c4d5e6f7` (reconciliation, quarantine backfill, foreign key constraint).

### 4.3 Verify Safe Quarantine Records
```sql
-- Verify no orphaned assets or deleted records exist:
SELECT id, company_name, email, status FROM companies WHERE email = 'quarantine@vahan.system';
SELECT count(*) FROM assets WHERE company_id = (SELECT id FROM companies WHERE email = 'quarantine@vahan.system');
SELECT count(*) FROM asset_history_records WHERE details->>'action' = 'QUARANTINE_BACKFILL';
```

---

## 5. Docker Compose Deployment

Use `docker-compose.traccar.yml`:

```bash
cd /opt/vahan
docker compose -f docker-compose.traccar.yml up -d
```

Check running containers:
```bash
docker compose -f docker-compose.traccar.yml ps
```

---

## 6. Health Checks & Verification Procedures

### 6.1 Traccar Gateway Health Check
```bash
# 1. Container status
docker inspect --format='{{.State.Status}}' vahan-traccar-engine

# 2. REST API reachability
curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/api/server
# Expected: 200

# 3. Log inspection
docker logs --tail 50 vahan-traccar-engine
```

### 6.2 Vahan Telematics Webhook Health & Security Check
```bash
# 1. Missing Secret (Must return 401)
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/tracking/telematics/traccar
# Expected: 401

# 2. Invalid Secret (Must return 401)
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/tracking/telematics/traccar \
  -H "X-Telematics-Secret: wrong_key"
# Expected: 401

# 3. Valid Secret (Must return 200 with JSON)
curl -s -X POST http://localhost:8000/api/v1/tracking/telematics/traccar \
  -H "Content-Type: application/json" \
  -H "X-Telematics-Secret: $TELEMATICS_WEBHOOK_SECRET" \
  -d '{"device": {"uniqueId": "860123456789012"}, "position": {"latitude": 28.6139, "longitude": 77.2090, "deviceTime": "2026-11-24T10:30:00Z", "attributes": {"ignition": true}}}'
# Expected: {"accepted":1,"duplicates":0,"rejected":0,"items":[{"timestamp":"...","status":"accepted","reason":null}]}
```

---

## 7. Rollback & Disaster Recovery Procedure

If migration or deployment encounters an issue:

### 7.1 Revert Migration Safely
```bash
cd /opt/vahan/backend
# Downgrade 1 revision back to clean merge point
alembic downgrade -1
```

### 7.2 Full Database Restore (if required)
```bash
# Stop applications
docker compose -f docker-compose.traccar.yml stop
sudo systemctl stop vahan-backend

# Restore from snapshot
pg_restore -h db.staging.thevahan.com -U postgres -d vahan_staging --clean --if-exists "/opt/vahan/backups/<backup_file>.dump"

# Restart services
sudo systemctl start vahan-backend
docker compose -f docker-compose.traccar.yml start
```
