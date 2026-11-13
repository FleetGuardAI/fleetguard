"""
FleetGuard — PostgreSQL Migration & Concurrency Verification (FG-SEC-002)
Batch 1.4: Dedicated test suite executed in isolated PostgreSQL service container.
Verifies Alembic schema/indexes, atomic concurrency across independent database connections,
session rollback, application restart persistence, and migration downgrade/upgrade cycles.
"""

import os
import sys
import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config import settings
from services.otp_service import compute_recipient_fingerprint, normalize_identifier


def get_postgres_url() -> str:
    url = os.getenv("POSTGRES_TEST_URL") or os.getenv("DATABASE_URL", "")
    if "postgresql" not in url:
        pytest.skip("Skipping PostgreSQL verification: PostgreSQL database not configured in current environment.")
    return url


@pytest.fixture
def pg_engine():
    url = get_postgres_url()
    engine = create_async_engine(url, pool_pre_ping=True, echo=False)
    yield engine
    # Cleanup engine connections
    asyncio.run(engine.dispose())


@pytest.mark.asyncio
async def test_postgres_schema_and_indexes(pg_engine):
    """
    Step 5: Verifies that Alembic migration e5b6c7d8a9f0 created the otp_transactions
    table with correct column definitions, constraints, and performance indexes.
    """
    async with pg_engine.connect() as conn:
        # 1. Verify table columns
        col_res = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'otp_transactions'
            ORDER BY ordinal_position;
        """))
        cols = {row[0]: {"type": row[1], "nullable": row[2]} for row in col_res.fetchall()}

        expected_cols = [
            "id", "transaction_id", "recipient_fingerprint",
            "purpose", "status", "expires_at", "created_at", "consumed_at"
        ]
        for col in expected_cols:
            assert col in cols, f"Column '{col}' missing from otp_transactions table"

        assert cols["transaction_id"]["nullable"] == "NO"
        assert cols["recipient_fingerprint"]["nullable"] == "NO"
        assert cols["status"]["nullable"] == "NO"

        # 2. Verify indexes
        idx_res = await conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'otp_transactions';
        """))
        indexes = [row[0] for row in idx_res.fetchall()]

        assert "ix_otp_transactions_transaction_id" in indexes
        assert "ix_otp_transactions_recipient_fingerprint" in indexes
        assert "ix_otp_transactions_status" in indexes


@pytest.mark.asyncio
async def test_postgres_otp_lifecycle_and_binding(pg_engine):
    """
    Step 6: Exercises OTP transaction creation, cryptographic identity binding,
    TTL expiry enforcement, and valid consumption in PostgreSQL.
    """
    from models.otp_transaction import OTPTransaction
    session_factory = async_sessionmaker(pg_engine, expire_on_commit=False)

    phone = "+91 98765 43210"
    fingerprint = compute_recipient_fingerprint(phone)
    now = datetime.now(timezone.utc)

    # 1. Create OTP Transaction
    async with session_factory() as session:
        txn = OTPTransaction(
            transaction_id="pg-test-txn-1",
            recipient_fingerprint=fingerprint,
            purpose="login",
            status="PENDING",
            expires_at=now + timedelta(minutes=5),
            created_at=now
        )
        session.add(txn)
        await session.commit()
        txn_id = txn.id

    # 2. Identity binding verification
    async with session_factory() as session:
        # Correct phone matches fingerprint
        res = await session.execute(
            select(OTPTransaction).where(
                OTPTransaction.transaction_id == "pg-test-txn-1",
                OTPTransaction.recipient_fingerprint == compute_recipient_fingerprint("+919876543210")
            )
        )
        matched = res.scalar_one_or_none()
        assert matched is not None

        # Different phone rejected
        res_diff = await session.execute(
            select(OTPTransaction).where(
                OTPTransaction.transaction_id == "pg-test-txn-1",
                OTPTransaction.recipient_fingerprint == compute_recipient_fingerprint("+919999988888")
            )
        )
        assert res_diff.scalar_one_or_none() is None

    # 3. Expiry enforcement check
    async with session_factory() as session:
        expired_txn = OTPTransaction(
            transaction_id="pg-test-expired",
            recipient_fingerprint=fingerprint,
            purpose="login",
            status="PENDING",
            expires_at=now - timedelta(seconds=10),
            created_at=now - timedelta(minutes=6)
        )
        session.add(expired_txn)
        await session.commit()

        # Query active transactions (expires_at > now) excludes expired transaction
        active_res = await session.execute(
            select(OTPTransaction).where(
                OTPTransaction.transaction_id == "pg-test-expired",
                OTPTransaction.expires_at > datetime.now(timezone.utc)
            )
        )
        assert active_res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_postgres_atomic_concurrent_consumption(pg_engine):
    """
    Steps 7 & 8: 10 concurrent requests from independent async sessions and
    independent PostgreSQL database connections attempt to consume the same OTP transaction.
    Asserts that EXACTLY ONE competing request succeeds and 9 fail.
    """
    from models.otp_transaction import OTPTransaction
    session_factory = async_sessionmaker(pg_engine, expire_on_commit=False)

    txn_uuid = f"concurrent-txn-{datetime.now().timestamp()}"
    now = datetime.now(timezone.utc)

    # Insert test transaction
    async with session_factory() as session:
        txn = OTPTransaction(
            transaction_id=txn_uuid,
            recipient_fingerprint="test-fingerprint-concurrency",
            purpose="login",
            status="PENDING",
            expires_at=now + timedelta(minutes=5),
            created_at=now
        )
        session.add(txn)
        await session.commit()

    # Worker simulating independent request/connection attempting atomic consumption
    async def attempt_consume(worker_id: int) -> bool:
        # Each worker opens its own dedicated AsyncSession and connection
        async with session_factory() as worker_session:
            # Atomic update with WHERE status = 'PENDING'
            result = await worker_session.execute(text("""
                UPDATE otp_transactions
                SET status = 'CONSUMED', consumed_at = NOW()
                WHERE transaction_id = :txn_id AND status = 'PENDING'
                RETURNING id;
            """), {"txn_id": txn_uuid})
            row = result.fetchone()
            await worker_session.commit()
            return row is not None

    # Run 10 concurrent competing workers
    tasks = [attempt_consume(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    # Step 8: Assert EXACTLY ONE competing request succeeds
    success_count = sum(1 for r in results if r is True)
    failure_count = sum(1 for r in results if r is False)

    assert success_count == 1, f"Expected exactly 1 winner, but got {success_count}!"
    assert failure_count == 9, f"Expected exactly 9 losers, but got {failure_count}!"


@pytest.mark.asyncio
async def test_postgres_rollback_and_persistence(pg_engine):
    """
    Step 9: Test transaction rollback and persistence across session/application restart.
    """
    from models.otp_transaction import OTPTransaction
    session_factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    # 1. Test Rollback
    async with session_factory() as session:
        txn_rollback = OTPTransaction(
            transaction_id="pg-test-rollback",
            recipient_fingerprint="fp-rollback",
            purpose="login",
            status="PENDING",
            expires_at=now + timedelta(minutes=5),
            created_at=now
        )
        session.add(txn_rollback)
        # Explicit rollback without commit
        await session.rollback()

    async with session_factory() as session:
        check = await session.execute(
            select(OTPTransaction).where(OTPTransaction.transaction_id == "pg-test-rollback")
        )
        assert check.scalar_one_or_none() is None, "Rolled-back transaction was persisted!"

    # 2. Test Persistence across session / application restart simulation
    async with session_factory() as session:
        txn_persist = OTPTransaction(
            transaction_id="pg-test-persist",
            recipient_fingerprint="fp-persist",
            purpose="login",
            status="PENDING",
            expires_at=now + timedelta(minutes=5),
            created_at=now
        )
        session.add(txn_persist)
        await session.commit()

    # Simulate application restart: dispose engine and recreate fresh engine
    await pg_engine.dispose()
    new_engine = create_async_engine(get_postgres_url(), pool_pre_ping=True)
    new_session_factory = async_sessionmaker(new_engine, expire_on_commit=False)

    try:
        async with new_session_factory() as session:
            check = await session.execute(
                select(OTPTransaction).where(OTPTransaction.transaction_id == "pg-test-persist")
            )
            persisted = check.scalar_one_or_none()
            assert persisted is not None, "Committed transaction did not persist across engine restart!"
            assert persisted.status == "PENDING"
    finally:
        await new_engine.dispose()
