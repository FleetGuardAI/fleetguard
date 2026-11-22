import os
import sys
os.environ["OTP_MOCK_MODE"] = "True"

import pytest
import random
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.otp_transaction import OTPTransaction
from services.otp_service import otp_tracker, PersistentOTPTracker, compute_recipient_fingerprint

settings.OTP_MOCK_MODE = True


def random_phone():
    return f"+9198{random.randint(10000000, 99999999)}"


def test_otp_identity_binding_success(client: TestClient):
    """Legitimate OTP flow: requested for phone A and verified for phone A succeeds."""
    uid = uuid.uuid4().hex[:6]
    phone = random_phone()
    email = f"user_{uid}@fleetguard.com"

    # Register user
    reg = client.post("/api/v1/auth/register", json={
        "company_name": f"OTP Co {uid}",
        "owner_name": f"Owner {uid}",
        "mobile_number": phone,
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    assert reg.status_code in [200, 201], reg.text

    # Request OTP
    req = client.post("/api/v1/auth/request-otp", json={"identifier": phone})
    assert req.status_code == 200
    req_id = req.json().get("req_id")
    assert req_id is not None

    # Verify OTP for the same phone
    verify = client.post("/api/v1/auth/verify-otp", json={
        "identifier": phone,
        "req_id": req_id,
        "code": "123456",
    })
    assert verify.status_code == 200, verify.text
    assert "access_token" in verify.json()


def test_otp_mismatched_identity_rejected(client: TestClient):
    """
    FG-SEC-002: Attacker requests OTP for their own identifier (User A),
    then attempts to verify against victim account (User B).
    Must be rejected; no token issued.
    """
    uid1 = uuid.uuid4().hex[:6]
    uid2 = uuid.uuid4().hex[:6]
    phone_a = random_phone()
    phone_b = random_phone()

    # Register User A (attacker)
    reg_a = client.post("/api/v1/auth/register", json={
        "company_name": f"Attacker Co {uid1}",
        "owner_name": "Attacker",
        "mobile_number": phone_a,
        "email": f"attacker_{uid1}@test.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    assert reg_a.status_code in [200, 201], reg_a.text

    # Register User B (victim)
    reg_b = client.post("/api/v1/auth/register", json={
        "company_name": f"Victim Co {uid2}",
        "owner_name": "Victim",
        "mobile_number": phone_b,
        "email": f"victim_{uid2}@test.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    assert reg_b.status_code in [200, 201], reg_b.text

    # Attacker requests OTP for phone A
    req = client.post("/api/v1/auth/request-otp", json={"identifier": phone_a})
    assert req.status_code == 200
    attacker_req_id = req.json().get("req_id")
    assert attacker_req_id is not None

    # Attacker attempts to login as Victim using their own req_id
    verify = client.post("/api/v1/auth/verify-otp", json={
        "identifier": phone_b,
        "req_id": attacker_req_id,
        "code": "123456",
    })
    assert verify.status_code == 401
    assert "access_token" not in verify.json()


def test_otp_replay_attack_rejected(client: TestClient):
    """FG-SEC-002: OTP cannot be replayed after successful consumption."""
    uid = uuid.uuid4().hex[:6]
    phone = random_phone()

    reg = client.post("/api/v1/auth/register", json={
        "company_name": f"Replay Co {uid}",
        "owner_name": "User Replay",
        "mobile_number": phone,
        "email": f"replay_{uid}@test.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    assert reg.status_code in [200, 201], reg.text

    req = client.post("/api/v1/auth/request-otp", json={"identifier": phone})
    assert req.status_code == 200
    req_id = req.json().get("req_id")

    # First verify succeeds
    v1 = client.post("/api/v1/auth/verify-otp", json={
        "identifier": phone,
        "req_id": req_id,
        "code": "123456",
    })
    assert v1.status_code == 200

    # Second verify with same req_id must fail
    v2 = client.post("/api/v1/auth/verify-otp", json={
        "identifier": phone,
        "req_id": req_id,
        "code": "123456",
    })
    assert v2.status_code == 401
    assert "access_token" not in v2.json()


@pytest.mark.asyncio
async def test_otp_expired_rejected(client: TestClient, db_session: AsyncSession):
    """FG-SEC-002: Expired OTP transaction in database is rejected."""
    uid = uuid.uuid4().hex[:6]
    phone = random_phone()

    reg = client.post("/api/v1/auth/register", json={
        "company_name": f"Expire Co {uid}",
        "owner_name": "User Expire",
        "mobile_number": phone,
        "email": f"expire_{uid}@test.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    assert reg.status_code in [200, 201], reg.text

    req = client.post("/api/v1/auth/request-otp", json={"identifier": phone})
    assert req.status_code == 200
    req_id = req.json().get("req_id")

    # Update database record to be expired
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    await db_session.execute(
        update(OTPTransaction)
        .where(OTPTransaction.req_id == req_id)
        .values(expires_at=past_time)
    )
    await db_session.flush()

    verify = client.post("/api/v1/auth/verify-otp", json={
        "identifier": phone,
        "req_id": req_id,
        "code": "123456",
    })
    assert verify.status_code == 401
    assert "access_token" not in verify.json()


def test_driver_mobile_otp_mismatched_phone_rejected(client: TestClient):
    """
    FG-SEC-002: In Driver Mobile app, verifying OTP with a phone number
    different from the one that requested the OTP must fail.
    """
    driver_phone_a = random_phone()
    driver_phone_b = random_phone()

    # Request OTP for phone A
    send_resp = client.post("/api/v1/driver-app/send-otp", json={"phone_number": driver_phone_a})
    assert send_resp.status_code == 200
    req_id = send_resp.json().get("req_id")
    assert req_id is not None

    # Attempt to verify OTP for phone B using req_id from phone A
    verify_resp = client.post("/api/v1/driver-app/verify-otp", json={
        "phone_number": driver_phone_b,
        "req_id": req_id,
        "otp_code": "123456",
    })
    assert verify_resp.status_code == 400
    assert "access_token" not in verify_resp.json()


def test_wrong_otp_does_not_consume_transaction(client: TestClient):
    """
    FG-SEC-002: An invalid OTP code does NOT prematurely consume the transaction,
    preventing DoS and allowing the user to enter the correct code on retry.
    """
    uid = uuid.uuid4().hex[:6]
    phone = random_phone()

    reg = client.post("/api/v1/auth/register", json={
        "company_name": f"Retry Co {uid}",
        "owner_name": f"Retry User {uid}",
        "mobile_number": phone,
        "email": f"retry_{uid}@test.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    assert reg.status_code in [200, 201], reg.text

    req = client.post("/api/v1/auth/request-otp", json={"identifier": phone})
    assert req.status_code == 200
    req_id = req.json().get("req_id")

    # 1. First attempt with wrong OTP
    wrong_v = client.post("/api/v1/auth/verify-otp", json={
        "identifier": phone,
        "req_id": req_id,
        "code": "999999",  # incorrect code
    })
    assert wrong_v.status_code == 401

    # 2. Subsequent attempt with correct OTP still succeeds
    correct_v = client.post("/api/v1/auth/verify-otp", json={
        "identifier": phone,
        "req_id": req_id,
        "code": "123456",  # valid mock code
    })
    assert correct_v.status_code == 200
    assert "access_token" in correct_v.json()


@pytest.mark.asyncio
async def test_shared_state_across_independent_tracker_instances(db_session: AsyncSession):
    """
    FG-SEC-002: Two separate tracker instances (simulating two app servers)
    share the same persistent database state.
    """
    tracker_a = PersistentOTPTracker()
    tracker_b = PersistentOTPTracker()

    req_id = f"shared_req_{uuid.uuid4().hex[:10]}"
    phone = random_phone()

    # Instance A records request
    recorded = await tracker_a.record_request(req_id, phone, db=db_session)
    assert recorded is True

    # Instance B validates binding
    is_valid, msg = await tracker_b.validate_binding(req_id, phone, db=db_session)
    assert is_valid is True

    # Instance B consumes transaction
    is_consumed, msg = await tracker_b.consume_transaction(req_id, phone, db=db_session)
    assert is_consumed is True

    # Instance A cannot consume again (replay prevention across instances)
    is_consumed_again, msg = await tracker_a.consume_transaction(req_id, phone, db=db_session)
    assert is_consumed_again is False


@pytest.mark.asyncio
async def test_atomic_concurrent_consumption(db_session: AsyncSession):
    """
    FG-SEC-002: Under concurrent consumption attempts across multiple workers,
    exactly ONE request succeeds in consuming the transaction.
    """
    tracker = PersistentOTPTracker()
    req_id = f"concur_req_{uuid.uuid4().hex[:10]}"
    phone = random_phone()

    await tracker.record_request(req_id, phone, db=db_session)

    # Launch two concurrent consume attempts
    results = await asyncio.gather(
        tracker.consume_transaction(req_id, phone, db=db_session),
        tracker.consume_transaction(req_id, phone, db=db_session),
    )

    success_count = sum(1 for success, _ in results if success)
    assert success_count == 1, f"Expected exactly 1 successful consumption, got {success_count}"


def test_otp_fingerprint_key_validation(monkeypatch):
    """
    FG-SEC-002 (Batch 1.3): OTP_RECIPIENT_FINGERPRINT_KEY must be >= 32 bytes AND have
    sufficient cryptographic entropy. Key length alone does not prove entropy.
    Weak, low-entropy, or missing secrets must raise RuntimeError.
    """
    import secrets
    from services.otp_service import get_otp_fingerprint_key

    # 1. Cryptographically secure random key (high entropy, >= 32 bytes) passes
    valid_key = secrets.token_hex(32)  # 64 hex characters
    monkeypatch.setattr(settings, "OTP_RECIPIENT_FINGERPRINT_KEY", valid_key)
    monkeypatch.setenv("OTP_RECIPIENT_FINGERPRINT_KEY", valid_key)
    monkeypatch.setattr(settings, "OTP_PREVIOUS_FINGERPRINT_KEY", None)
    assert get_otp_fingerprint_key() == valid_key.encode("utf-8")

    # 2. Key with length >= 32 but low entropy (repeated character) is rejected
    low_entropy_key = "a" * 32
    monkeypatch.setattr(settings, "OTP_RECIPIENT_FINGERPRINT_KEY", low_entropy_key)
    monkeypatch.setenv("OTP_RECIPIENT_FINGERPRINT_KEY", low_entropy_key)
    with pytest.raises(RuntimeError, match="fails heuristic diversity check"):
        get_otp_fingerprint_key()

    # 3. Weak key (< 32 bytes) raises RuntimeError
    weak_key = "short-secret-key"
    monkeypatch.setattr(settings, "OTP_RECIPIENT_FINGERPRINT_KEY", weak_key)
    monkeypatch.setenv("OTP_RECIPIENT_FINGERPRINT_KEY", weak_key)
    with pytest.raises(RuntimeError, match="at least 32 bytes"):
        get_otp_fingerprint_key()

    # 4. Invalid previous rotation key fails safely (never silently ignored)
    monkeypatch.setattr(settings, "OTP_RECIPIENT_FINGERPRINT_KEY", valid_key)
    monkeypatch.setattr(settings, "OTP_PREVIOUS_FINGERPRINT_KEY", "invalid-short-prev")
    with pytest.raises(RuntimeError, match="OTP_PREVIOUS_FINGERPRINT_KEY must contain at least 32 bytes"):
        get_otp_fingerprint_key()

    # 5. Missing key in production mode raises RuntimeError
    monkeypatch.setattr(settings, "OTP_RECIPIENT_FINGERPRINT_KEY", None)
    monkeypatch.setattr(settings, "OTP_PREVIOUS_FINGERPRINT_KEY", None)
    monkeypatch.delenv("OTP_RECIPIENT_FINGERPRINT_KEY", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "modules", {k: v for k, v in sys.modules.items() if k != "pytest"})
    with pytest.raises(RuntimeError, match="CRITICAL: OTP_RECIPIENT_FINGERPRINT_KEY"):
        get_otp_fingerprint_key()


def test_recipient_fingerprint_stability_and_uniqueness():
    """
    FG-SEC-002 (Batch 1.2): Recipient fingerprint must be deterministic for identical inputs
    and produce distinct hashes for different phone numbers / email addresses.
    """
    import secrets
    phone1 = "+919876543210"
    phone2 = "+919876543211"
    key1 = secrets.token_bytes(32)
    key2 = secrets.token_bytes(32)

    # Stability
    fp1a = compute_recipient_fingerprint(phone1, key_override=key1)
    fp1b = compute_recipient_fingerprint(phone1, key_override=key1)
    assert fp1a == fp1b
    assert len(fp1a) == 64  # SHA256 hex string

    # Uniqueness across recipients
    fp2 = compute_recipient_fingerprint(phone2, key_override=key1)
    assert fp1a != fp2

    # Uniqueness across keys
    fp1_key2 = compute_recipient_fingerprint(phone1, key_override=key2)
    assert fp1a != fp1_key2


@pytest.mark.asyncio
async def test_dual_key_rotation_support(db_session: AsyncSession, monkeypatch):
    """
    FG-SEC-002 (Batch 1.3): Supports zero-downtime key rotation.
    In-flight OTP transactions created with previous key can still be validated
    and consumed when OTP_PREVIOUS_FINGERPRINT_KEY is configured.
    """
    import secrets
    key_active = secrets.token_hex(32)
    key_previous = secrets.token_hex(32)

    phone = random_phone()
    req_id = f"rotate_req_{uuid.uuid4().hex[:10]}"

    # Transaction generated under previous key
    fp_previous = compute_recipient_fingerprint(phone, key_override=key_previous.encode("utf-8"))
    now = datetime.now(timezone.utc)
    tx = OTPTransaction(
        req_id=req_id,
        recipient_fingerprint=fp_previous,
        created_at=now,
        expires_at=now + timedelta(minutes=5),
        is_consumed=False,
    )
    db_session.add(tx)
    await db_session.flush()

    # Configure server with active key and previous key
    monkeypatch.setattr(settings, "OTP_RECIPIENT_FINGERPRINT_KEY", key_active)
    monkeypatch.setattr(settings, "OTP_PREVIOUS_FINGERPRINT_KEY", key_previous)

    tracker = PersistentOTPTracker()

    # Validation succeeds because tx.recipient_fingerprint matches previous key
    is_valid, msg = await tracker.validate_binding(req_id, phone, db=db_session)
    assert is_valid is True

    # Consumption succeeds under previous key
    is_consumed, msg = await tracker.consume_transaction(req_id, phone, db=db_session)
    assert is_consumed is True

    # Replay fails
    is_replayed, _ = await tracker.consume_transaction(req_id, phone, db=db_session)
    assert is_replayed is False


@pytest.mark.asyncio
async def test_multi_instance_key_consistency(db_session: AsyncSession, monkeypatch):
    """
    FG-SEC-002 (Batch 1.3):
    1. Multiple app instances sharing the same key configuration successfully verify transactions.
    2. An instance with incorrect / unshared key cannot verify or bypass binding.
    """
    import secrets
    shared_key = secrets.token_hex(32)
    wrong_key = secrets.token_hex(32)
    phone = random_phone()
    req_id = f"multi_inst_{uuid.uuid4().hex[:10]}"

    # Instance 1 records request with shared_key
    monkeypatch.setattr(settings, "OTP_RECIPIENT_FINGERPRINT_KEY", shared_key)
    monkeypatch.setattr(settings, "OTP_PREVIOUS_FINGERPRINT_KEY", None)
    tracker_instance_1 = PersistentOTPTracker()
    recorded = await tracker_instance_1.record_request(req_id, phone, db=db_session)
    assert recorded is True

    # Instance 2 (with identical shared key) verifies binding and consumes
    tracker_instance_2 = PersistentOTPTracker()
    is_valid, _ = await tracker_instance_2.validate_binding(req_id, phone, db=db_session)
    assert is_valid is True

    # Instance 3 (with incorrect/desynchronized key) fails validation safely
    monkeypatch.setattr(settings, "OTP_RECIPIENT_FINGERPRINT_KEY", wrong_key)
    tracker_instance_3 = PersistentOTPTracker()
    is_valid_wrong, _ = await tracker_instance_3.validate_binding(req_id, phone, db=db_session)
    assert is_valid_wrong is False
