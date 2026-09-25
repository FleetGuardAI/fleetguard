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
from sqlalchemy import select
from models.intelligence_condition import IntelligenceCondition, ConditionStatus
from services.driver_vehicle_intelligence import DriverVehicleIntelligenceService

logger = logging.getLogger("fleetguard.infrastructure.intelligence.sweeper")


class IntelligenceSweeperWorker:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

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
        async with async_session_factory() as session:
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
            except Exception as e:
                await session.rollback()
                raise e
