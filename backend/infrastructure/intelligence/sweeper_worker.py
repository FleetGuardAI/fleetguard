"""
FleetGuard — Driver Vehicle Intelligence Sweeper Worker
Periodically evaluates active intelligence conditions to ensure duration-based anomalies
can trigger even if no new GPS events arrive.
"""

import asyncio
import logging
from datetime import datetime, timezone
import traceback

from config import settings
from database import async_session_factory
from sqlalchemy import select, func, text, pool
from sqlalchemy.ext.asyncio import create_async_engine
from models.intelligence_condition import IntelligenceCondition, ConditionStatus
from services.driver_vehicle_intelligence import DriverVehicleIntelligenceService
from services.maintenance_due_service import MaintenanceDueService

logger = logging.getLogger("fleetguard.infrastructure.intelligence.sweeper")

_lock_engine = None

def _get_dedicated_lock_engine():
    global _lock_engine
    if _lock_engine is None:
        _lock_engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    return _lock_engine


class DistributedSweeperLock:
    """
    Coordinates sweeper execution across multiple worker processes/replicas.
    In PostgreSQL production environments, leverages session-level advisory locks
    (`pg_try_advisory_lock`), which prevent duplicate execution across separate
    containers/dynos and automatically release upon process exit, crash, or disconnect.
    
    Database Pool Safety:
    Uses a dedicated connection from an unpooled (NullPool) engine specifically for the advisory lock:
    1. Lock ownership is bound to a single, dedicated PostgreSQL session.
    2. The lock connection is retained for the full lock ownership period.
    3. The lock connection NEVER returns to the general application connection pool while held.
    4. Application transactions/commits on the worker's session cannot inadvertently cycle,
       reset, or reuse the lock-holding session.
    5. Clean release via pg_advisory_unlock on the exact same underlying connection.
    6. Abrupt process or network termination cleanly terminates the TCP connection, causing
       PostgreSQL to automatically and immediately release the advisory lock.
    
    In non-Postgres environments (e.g. SQLite test runners), provides an in-memory
    non-blocking lock fallback for local coordination and testing.
    """
    SWEEPER_ADVISORY_LOCK_KEY = 847291049281
    _local_process_lock = asyncio.Lock()
    _active_holders = 0

    def __init__(self, session=None):
        self.session = session
        self.acquired = False
        self.is_pg = False
        self._dedicated_conn = None

    async def __aenter__(self):
        engine = None
        if hasattr(self.session, "connect") and callable(self.session.connect):
            engine = self.session
        elif hasattr(self.session, "get_bind"):
            try:
                engine = self.session.get_bind()
            except Exception:
                engine = getattr(self.session, "bind", None)
        else:
            engine = getattr(self.session, "bind", None)

        dialect_name = "sqlite"
        if engine and hasattr(engine, "dialect"):
            dialect_name = getattr(engine.dialect, "name", "sqlite")
        elif hasattr(self.session, "bind") and hasattr(self.session.bind, "dialect"):
            dialect_name = getattr(self.session.bind.dialect, "name", "sqlite")
        elif settings.DATABASE_URL.startswith("postgresql"):
            # If default environment is PostgreSQL and session is not bound to SQLite
            dialect_name = "postgresql" if not str(getattr(self.session, "__class__", "")).lower().count("sqlite") else "sqlite"

        self.is_pg = (dialect_name == "postgresql")

        if self.is_pg:
            try:
                # Check out dedicated unpooled connection for advisory lock
                lock_engine = _get_dedicated_lock_engine()
                self._dedicated_conn = await lock_engine.connect()
                res = await self._dedicated_conn.execute(
                    text("SELECT pg_try_advisory_lock(:lock_id)"),
                    {"lock_id": self.SWEEPER_ADVISORY_LOCK_KEY}
                )
                self.acquired = bool(res.scalar())
                if not self.acquired:
                    await self._dedicated_conn.close()
                    self._dedicated_conn = None
            except Exception as e:
                logger.warning(f"Could not acquire PostgreSQL advisory lock: {e}")
                if self._dedicated_conn:
                    await self._dedicated_conn.close()
                    self._dedicated_conn = None
                self.acquired = False
        else:
            # Fallback for SQLite / mock test environments
            if not DistributedSweeperLock._local_process_lock.locked():
                await DistributedSweeperLock._local_process_lock.acquire()
                self.acquired = True
                DistributedSweeperLock._active_holders += 1
            else:
                self.acquired = False

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            try:
                if self.is_pg and self._dedicated_conn is not None:
                    try:
                        await self._dedicated_conn.execute(
                            text("SELECT pg_advisory_unlock(:lock_id)"),
                            {"lock_id": self.SWEEPER_ADVISORY_LOCK_KEY}
                        )
                    finally:
                        await self._dedicated_conn.close()
                        self._dedicated_conn = None
                else:
                    if DistributedSweeperLock._local_process_lock.locked():
                        DistributedSweeperLock._local_process_lock.release()
                        DistributedSweeperLock._active_holders = max(0, DistributedSweeperLock._active_holders - 1)
            except Exception as e:
                logger.warning(f"Error releasing sweeper lock: {e}")
            finally:
                if self._dedicated_conn:
                    await self._dedicated_conn.close()
                    self._dedicated_conn = None
                self.acquired = False


class IntelligenceSweeperWorker:
    def __init__(self, session_factory=None):
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._session_factory = session_factory or async_session_factory

    async def start(self) -> None:
        if self._task is not None:
            return
            
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        # Run sweeper every minute
        logger.info("IntelligenceSweeperWorker started. Polling every 60s.")

    async def stop(self) -> None:
        if self._task is None:
            return
            
        logger.info("IntelligenceSweeperWorker stopping...")
        self._stop_event.set()
        
        try:
            await asyncio.wait_for(self._task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("IntelligenceSweeperWorker did not shut down gracefully. Forcing cancellation.")
            self._task.cancel()
            
        self._task = None
        logger.info("IntelligenceSweeperWorker stopped.")

    async def _run_loop(self) -> None:
        interval_seconds = 60.0
        
        while not self._stop_event.is_set():
            try:
                await self._sweep_active_conditions()
            except Exception as e:
                logger.error(f"IntelligenceSweeperWorker encountered an error: {e}")
                
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                pass

    async def _sweep_active_conditions(self):
        async with self._session_factory() as session:
            async with DistributedSweeperLock(session) as lock:
                if not lock.acquired:
                    logger.info("Intelligence sweeper advisory lock held by another worker instance. Skipping cycle.")
                    return False

                try:
                    # Get all unique active vehicles
                    query = select(IntelligenceCondition.vehicle_id, IntelligenceCondition.company_id).where(
                        IntelligenceCondition.status == ConditionStatus.ACTIVE
                    ).distinct()
                    
                    result = await session.execute(query)
                    active_vehicles = result.all()
                    
                    service = DriverVehicleIntelligenceService(session)
                    now = datetime.now(timezone.utc)
                    
                    count = 0
                    for vehicle_id, company_id in active_vehicles:
                        signals = await service.compute_signals(vehicle_id, company_id)
                        await service.process_conditions(signals, now)
                        count += 1
                        
                    if count > 0:
                        await session.commit()
                        logger.debug(f"Sweeper evaluated {count} vehicles.")
                        
                    # Evaluate maintenance due status
                    maintenance_service = MaintenanceDueService(session)
                    await maintenance_service.sweep_maintenance_status()
                    return True
                except Exception as e:
                    await session.rollback()
                    raise e
