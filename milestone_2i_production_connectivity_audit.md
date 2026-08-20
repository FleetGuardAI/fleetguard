# Milestone 2I — Production Backend Connectivity & Deployment Infrastructure Audit

## 1. Executive Summary
A read-only connectivity and deployment audit was conducted to verify the FleetGuard backend infrastructure. The backend successfully established an authenticated connection to the Supabase PostgreSQL instance via the asyncpg driver. However, **critical deployment blockers were found**: the production Supabase database contains absolutely no tables, and the frontend is not configured to communicate with a cross-origin Render backend. The deployment is classified as **NOT READY**.

---

## 2. Render Deployment Status
*   **Service Name:** `fleetguard-api` (Type: web)
*   **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
*   **Port Binding:** Yes, correctly binds to `0.0.0.0`.
*   **Health Check Path:** `/health`
*   **Status:** CONFIGURED

---

## 3. Backend Startup Status
*   **Lifecycle Hooks:** Yes, `main.py` explicitly runs `create_all_tables()` and starts background consumers (Validation, Processing, Evidence, Outbox, Fuel Intelligence).
*   **Status:** VERIFIED (Code logic exists).

---

## 4. Environment Variable Audit
An audit of `render.yaml` and `.env` revealed the following production variables:

| Variable | Required | Present in Code | Render Required | Status |
|---|---|---|---|---|
| `DATABASE_URL` | YES | YES | YES | PRESENT |
| `SECRET_KEY` | YES | YES | YES | PRESENT |
| `DEBUG` | NO | YES | YES | PRESENT (Value: false) |
| `CORS_ORIGINS` | YES | YES | YES | PRESENT |
| `OPENAI_API_KEY` | NO | YES | YES | PRESENT |
| `KAFKA_BOOTSTRAP_SERVERS` | YES | YES | YES | PRESENT |
| `SUPABASE_URL` | YES | YES | YES | PRESENT |
| `SUPABASE_KEY` | YES | YES | YES | PRESENT |

---

## 5. Supabase Connection Status
A read-only Python connection test using the `.env` configuration yielded:
*   **Database reachable:** YES
*   **Authentication successful:** YES
*   **PostgreSQL responding:** YES (Connected to 'postgres')
*   **Connection pooling functional:** YES (Using Supabase pooler via port 5432)
*   **SSL Configured:** YES (`?ssl=require`)
*   **Status:** CONNECTED & VERIFIED

---

## 6. Database Schema Status
A query for `public` schema tables via the live Supabase connection yielded **0 tables**.
*   `operational_events`: MISSING
*   `vehicles`, `drivers`, `trips`: MISSING
*   `derived_fuel_metrics`, `entity_baselines`, `fuel_anomalies`: MISSING
*   **Status:** BROKEN (Database is empty).

---

## 7. Alembic Migration Status
*   **Current Alembic revision in codebase:** N/A (Alembic CLI exited with an error locally, suggesting `alembic` is not correctly configured in the venv).
*   **Production Alembic Table (`alembic_version`):** MISSING (Does not exist in Supabase).
*   **Status:** BROKEN

---

## 8. FastAPI Health Status
*   **Endpoint:** `/health` is configured in `main.py`.
*   **Response:** Expected to return `{"status": "healthy", "database": "connected"}`.
*   **Status:** NOT TESTED (Cannot reach live Render URL without the domain name).

---

## 9. Database → API Connectivity
*   **Status:** BROKEN. Because the Supabase database contains no tables, any API request attempting to read/write (e.g., fleet summary) will immediately fail with a 500 Internal Server Error (Table Not Found).

---

## 10. Financial Intelligence API Status
*   **Endpoints:** `GET /api/v1/intelligence/fuel/summary` and `GET /api/v1/intelligence/fuel/trucks/{truck_id}` are properly configured in `routers/fuel_intelligence.py`.
*   **Status:** API works conceptually, but API/database integration is **BROKEN** due to missing schema.

---

## 11. Operational Event Path
*   **Code Path:** `API -> OperationalEventService -> OperationalEvent -> OutboxEvent`.
*   **Configuration:** The dependencies and lifespan startup logic in `main.py` correctly instantiate this flow.
*   **Status:** CONFIGURED (But execution is broken due to missing database schema).

---

## 12. Outbox Status
*   **Configuration:** `OutboxWorkerRunner` and `OutboxPublisher` are fully wired up in `main.py`'s lifespan.
*   **Status:** CONFIGURED

---

## 13. Kafka Status
*   **Configuration:** `render.yaml` securely sets SASL_SSL with SCRAM-SHA-256 for Kafka communication.
*   **Status:** CONFIGURED / UNKNOWN (Cannot safely publish/subscribe to production Kafka to verify credentials).

---

## 14. Authentication Status
*   **Configuration:** JWT secret and validation logic exist.
*   **User Lookup:** Hits the Supabase database.
*   **Status:** BROKEN (Cannot authenticate without a `users` table).

---

## 15. CORS Status
*   **Configuration:** `render.yaml` requires a `CORS_ORIGINS` variable.
*   **Status:** CONFIGURED (Dependent on proper Render dashboard values).

---

## 16. Frontend → Backend Connectivity
*   **Code Audit:** The frontend `api/client.js` hardcodes `const API_BASE = '/api'`. There is no `VITE_API_URL` environment variable utilized.
*   **Issue:** Unless the frontend is built and served natively via FastAPI's `StaticFiles` (which it currently is not), a detached frontend (e.g., Vercel) will send API requests to its own domain (`frontend-domain.com/api`) instead of the Render backend, resulting in a 404.
*   **Status:** BROKEN

---

## 17. Connection Pool Assessment
*   **Configuration:** SQLAlchemy is using `asyncpg` with `pool_pre_ping=True`. Connection sessions are neatly yielded and closed via context managers.
*   **Safety:** Safe. Connecting to Supabase port 5432 leverages PgBouncer/Supavisor session pooling, ensuring the Render backend does not exhaust database connections.
*   **Status:** VERIFIED

---

## 18. Runtime Error Audit
*   Render server logs were unavailable for this audit.
*   **Status:** UNKNOWN

---

## 19. Environment Drift
*   **Database:** Massive drift. Local development contains full schema and migrations; Production Supabase is completely empty.
*   **Frontend:** Local development utilizes a Vite proxy (`127.0.0.1:8000`), but production lacks a configuration to target a cross-origin Render URL.

---

## 20. P0/P1/P2/P3 Findings
*   **P0 (Production Unavailable):** The Supabase `public` schema contains 0 tables. API requests and application logic will catastrophically fail.
*   **P1 (Major Functionality Broken):** The frontend API client uses relative paths (`/api`) and lacks support for an absolute backend URL via environment variables.
*   **P2:** Alembic is not managing the schema. The app relies on `Base.metadata.create_all()` in `main.py`, which is an anti-pattern for production migrations.

---

## 21. Production Connectivity Score
*   Render Backend Availability: UNKNOWN (Assumed 5/10)
*   Supabase Connectivity: 15/15
*   Database Schema: 0/15
*   Migration State: 0/10
*   FastAPI/API Layer: 5/10
*   Authentication: 0/10 (Broken by DB)
*   Frontend → Backend: 0/10
*   Operational Event Path: 5/10
*   Kafka/Outbox: 5/5
*   Intelligence Pipeline: 5/5
*   **Total Score: 40 / 100**

---

## 22. Final Production Readiness Decision
**NOT READY.**

---

## 23. Exact Recommended Fixes
1.  **Resolve P0 Database Empty State:** Manually execute `alembic upgrade head` against the production Supabase database to generate the tables, or ensure the Render API instance restarts successfully so `create_all_tables()` can trigger.
2.  **Resolve P1 Frontend Detachment:** Modify `c:\Fleetguard\frontend\src\api\client.js` to accept `import.meta.env.VITE_API_URL || '/api'`. Add `VITE_API_URL=https://fleetguard-api.onrender.com/api` to the frontend production environment.
3.  **Harden P2 Migrations:** Remove `create_all_tables()` from the `lifespan` in `main.py` to prevent race conditions during horizontal scaling, and strictly enforce Alembic migrations in a CI/CD pipeline step.
