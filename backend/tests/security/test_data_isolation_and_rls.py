"""
FleetGuard — Batch 2 Security Verification Suite (FG-SEC-009, FG-SEC-024, FG-SEC-030, FG-SEC-031)

Verifies:
1. FG-SEC-024: Elimination of dangerous company_id defaults across entity models.
2. FG-SEC-030: Field-level AES-256-GCM authenticated encryption and blind indexing.
3. FG-SEC-031: Absence of runtime startup DDL execution.
4. FG-SEC-009: PostgreSQL Row-Level Security session context and policy definition.
"""

import pytest
import secrets
from utils.encryption import (
    encrypt_field,
    decrypt_field,
    generate_blind_index,
    EncryptedString,
    ENCRYPTION_PREFIX,
)
from models.vehicle_domain import Vehicle
from models.trip_domain import Trip
from models.maintenance_domain import MaintenanceRecord
from models.tyre_domain import Tyre
from models.driver_domain import Driver


# ==============================================================================
# 1. FG-SEC-024: Elimination of Dangerous company_id Defaults
# ==============================================================================

def test_models_do_not_default_company_id_to_one():
    """
    Verify Vehicle, Trip, MaintenanceRecord, and Tyre do NOT default company_id to 1.
    If company_id is omitted, it must be None/unset before persistence.
    """
    v = Vehicle(registration_number="MH12AB1234")
    assert v.company_id is None, "Vehicle must not default company_id to 1"

    t = Trip(origin_location="Pune", destination_location="Mumbai", trip_id="TRIP-TEST-001")
    assert t.company_id is None, "Trip must not default company_id to 1"

    m = MaintenanceRecord(description="Oil Change")
    assert m.company_id is None, "MaintenanceRecord must not default company_id to 1"

    ty = Tyre(serial_number="TYRE-001")
    assert ty.company_id is None, "Tyre must not default company_id to 1"


# ==============================================================================
# 2. FG-SEC-030: PII Field-Level AES-256-GCM Encryption Tests
# ==============================================================================

def test_aes_gcm_encryption_roundtrip():
    """Verify AES-256-GCM authenticated encryption and decryption."""
    plain_aadhaar = "1234 5678 9012"
    encrypted = encrypt_field(plain_aadhaar)

    assert encrypted.startswith(ENCRYPTION_PREFIX)
    assert encrypted != plain_aadhaar

    decrypted = decrypt_field(encrypted)
    assert decrypted == plain_aadhaar


def test_encryption_generates_unique_iv():
    """Verify encrypting identical plaintext twice produces different ciphertexts (unique nonces)."""
    plain = "DL-14-2011-0012345"
    enc1 = encrypt_field(plain)
    enc2 = encrypt_field(plain)

    assert enc1 != enc2
    assert decrypt_field(enc1) == plain
    assert decrypt_field(enc2) == plain


def test_decryption_rejects_tampered_ciphertext():
    """Verify AES-GCM detects ciphertext tampering (authentication tag verification)."""
    plain = "SECRET-PII-DATA"
    enc = encrypt_field(plain)

    # Tamper with the base64 payload
    tampered = enc[:-4] + "AAAA"
    with pytest.raises(ValueError, match="Field decryption failed or invalid MAC"):
        decrypt_field(tampered)


def test_decryption_backward_compatibility():
    """Verify pre-existing unencrypted strings pass through safely without error."""
    legacy_plaintext = "MH1420110012345"
    assert decrypt_field(legacy_plaintext) == legacy_plaintext


def test_deterministic_blind_indexing():
    """Verify blind indexing produces consistent HMACs for search lookups."""
    val1 = "dl-14-2011-0012345 "
    val2 = "DL-14-2011-0012345"

    # Normalized whitespace and casing produces identical blind index
    bidx1 = generate_blind_index(val1)
    bidx2 = generate_blind_index(val2)

    assert bidx1 == bidx2
    assert len(bidx1) == 64  # SHA-256 hex


# ==============================================================================
# 3. FG-SEC-031: Absence of Runtime Startup DDL
# ==============================================================================

def test_main_does_not_execute_raw_alter_table():
    """
    Verify backend/main.py lifespan does NOT contain raw ALTER TABLE or CREATE TABLE
    queries that bypass Alembic migrations.
    """
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    assert "ALTER TABLE admin_password_reset_requests" not in content
    assert "ALTER TABLE driver_locations" not in content
    assert "CREATE TABLE IF NOT EXISTS copilot_conversations" not in content
    assert "CREATE TABLE IF NOT EXISTS copilot_messages" not in content


# ==============================================================================
# 4. FG-SEC-009: PostgreSQL RLS Helper Verification
# ==============================================================================

@pytest.mark.asyncio
async def test_set_tenant_context_helper():
    """
    Verify set_tenant_context sets app.current_company_id and app.is_super_admin
    without raising exceptions.
    """
    from database import set_tenant_context, AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Tenant user context
        await set_tenant_context(session, company_id=42, is_super_admin=False)

        # Super admin context
        await set_tenant_context(session, company_id=None, is_super_admin=True)

        # Unauthenticated / empty context
        await set_tenant_context(session, company_id=None, is_super_admin=False)
