# FleetGuard — Authentication Foundation Implementation Plan

## Overview

Building the authentication layer for a multi-tenant SaaS fleet management platform.
Each **Company** is a tenant. All future data belongs to a company. The first user per company is a `COMPANY_ADMIN` — created automatically during company registration. No self-registration for regular users.

---

## Architecture Decisions

| Decision | Choice | Reason |
|---|---|---|
| Password hashing | `passlib[bcrypt]` | Already implied; standard |
| JWT library | `python-jose[cryptography]` | FastAPI recommended |
| Token type | Bearer (OAuth2PasswordBearer) | FastAPI standard |
| Login identifier | Email OR Mobile (auto-detected) | Regex: `@` = email, else mobile |
| Role storage | `Enum` column in DB | Type-safe, queryable |
| Company status | `Enum` (ACTIVE / SUSPENDED / PENDING) | Future admin controls |
| ID type | `Integer` autoincrement | Consistent with existing models |
| Timestamps | `DateTime` with `server_default=func.now()` | UTC, DB-managed |

---

## Proposed Changes

### New Dependencies (requirements.txt)

```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

---

### Milestone 1 — Database Models

#### [NEW] `models/company.py`
- `Company` ORM model with all specified fields
- `CompanyStatus` enum: `ACTIVE`, `SUSPENDED`, `PENDING`
- Relationship → `users`

#### [NEW] `models/user.py`
- `User` ORM model with all specified fields
- `UserRole` enum: `SUPER_ADMIN`, `COMPANY_ADMIN`, `FLEET_MANAGER`
- `company_id` FK → `companies.id`
- Relationship → `company`

#### [MODIFY] `models/__init__.py`
- Add `Company` and `User` imports

#### [MODIFY] `config.py`
- Add `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`

#### [MODIFY] `.env`
- Add `SECRET_KEY` value

---

### Milestone 2 — Schemas (Pydantic)

#### [NEW] `schemas/auth.py`
- `CompanyRegistrationRequest` — registration payload
- `LoginRequest` — email or mobile + password
- `TokenResponse` — access_token, token_type
- `CompanyOut` — safe company response (no sensitive fields)
- `UserOut` — safe user response (no password_hash)
- `RegisterCompanyResponse` — wraps company + user + token
- `MeResponse` — current user + company + role

---

### Milestone 3 — Authentication Services

#### [NEW] `services/auth_service.py`
- `register_company()` — atomic company + admin user creation
- `authenticate_user()` — lookup by email OR mobile, verify password
- `get_current_user()` — decode JWT → fetch user from DB

---

### Milestone 4 — Routers

#### [NEW] `routers/auth.py`
- `POST /auth/register-company`
- `POST /auth/login`
- `GET /auth/me`

#### [MODIFY] `main.py`
- Mount `auth_router` under `/api`

---

### Milestone 5 — JWT & Security Utilities

#### [NEW] `utils/security.py`
- `hash_password(plain: str) → str`
- `verify_password(plain: str, hashed: str) → bool`
- `create_access_token(data: dict) → str`
- `decode_access_token(token: str) → dict`

#### [NEW] `utils/__init__.py`

---

## Verification Plan

### Automated
- Run server: `uvicorn main:app --reload`
- Swagger UI at `/docs` — test all 3 endpoints interactively

### Manual
1. `POST /api/auth/register-company` → get token
2. `POST /api/auth/login` (email) → get token
3. `POST /api/auth/login` (mobile) → get token
4. `GET /api/auth/me` with Bearer token → get user + company
5. Duplicate mobile/email → expect 400 errors
6. Wrong password → expect 401

---

## Open Questions

> [!NOTE]
> JWT `SECRET_KEY` will be added to `.env` with a strong default placeholder. Replace with a proper secret in production.

> [!IMPORTANT]
> The existing models (Truck, Driver, Ticket, FuelLog) do NOT yet have `company_id`. This plan does NOT add it — that will be a separate migration task once auth is stable.
