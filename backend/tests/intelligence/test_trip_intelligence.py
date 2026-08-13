import unittest
import asyncio
from datetime import datetime, timedelta, timezone

from models.trip_domain import Trip, TripStatus
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from models.fuel_domain import FuelTransaction, FuelTransactionType
from services.trip_intelligence_service import TripIntelligenceService
from schemas.trip_intelligence import DataQuality, InsightSeverity, InsightType


class MockRepository:
    def __init__(self, items=None):
        self.items = items or []

    async def get_expenses_by_trip(self, trip_id, limit=100):
        return [e for e in self.items if getattr(e, 'trip_id', None) == trip_id]

    async def get_fuel_transactions_by_truck(self, truck_id, limit=100):
        return [f for f in self.items if getattr(f, 'vehicle_id', None) == truck_id]

    async def get_trips_by_vehicle(self, vehicle_id, limit=20, offset=0):
        return [t for t in self.items if getattr(t, 'vehicle_id', None) == vehicle_id]

    async def get_trips_by_driver(self, driver_id, limit=20, offset=0):
        return [t for t in self.items if getattr(t, 'driver_id', None) == driver_id]


class MockRegistry:
    def __init__(self, expenses=None, fuel=None, trips=None):
        self.expense = MockRepository(expenses or [])
        self.fuel = MockRepository(fuel or [])
        self.trip = MockRepository(trips or [])


class MockUnitOfWork:
    def __init__(self, expenses=None, fuel=None, trips=None):
        self.repositories = MockRegistry(expenses, fuel, trips)


class TestTripIntelligenceService(unittest.TestCase):

    def setUp(self):
        self.now = datetime.now(timezone.utc)

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_1_profitable_trip(self):
        trip = Trip(
            id=1,
            trip_id="TRIP-001",
            status=TripStatus.COMPLETED,
            planned_distance=500.0,
            actual_distance=505.0,
            planned_start_time=self.now - timedelta(hours=10),
            actual_start_time=self.now - timedelta(hours=10),
            planned_end_time=self.now,
            actual_end_time=self.now,
            vehicle_id=1,
            driver_id=1,
            revenue=120000.0,
            planned_cost=50000.0,
            planned_fuel_liters=200.0,
        )

        expenses = [
            Expense(id=1, trip_id=1, category=ExpenseCategory.FUEL, amount=30000.0, status=ExpenseStatus.RECORDED, business_id="EXP-1", origin_type="test", origin_id="1"),
            Expense(id=2, trip_id=1, category=ExpenseCategory.TOLL, amount=5000.0, status=ExpenseStatus.RECORDED, business_id="EXP-2", origin_type="test", origin_id="2"),
            Expense(id=3, trip_id=1, category=ExpenseCategory.SALARY, amount=10000.0, status=ExpenseStatus.RECORDED, business_id="EXP-3", origin_type="test", origin_id="3"),
        ]

        fuel_txns = [
            FuelTransaction(id=1, vehicle_id=1, transaction_type=FuelTransactionType.FILL, amount_liters=195.0, timestamp=self.now - timedelta(hours=5))
        ]

        uow = MockUnitOfWork(expenses=expenses, fuel=fuel_txns, trips=[trip])
        service = TripIntelligenceService(uow)

        res = self.run_async(service.compute_intelligence(trip))

        self.assertEqual(res.financial_summary.revenue, 120000.0)
        self.assertEqual(res.financial_summary.total_cost, 45000.0)
        self.assertEqual(res.financial_summary.net_profit, 75000.0)
        self.assertAlmostEqual(res.financial_summary.profit_margin_pct, 62.5, places=1)
        self.assertTrue(res.efficiency_score.has_sufficient_data)
        self.assertGreaterEqual(res.efficiency_score.overall_score, 80)

    def test_2_loss_making_trip(self):
        trip = Trip(
            id=2,
            trip_id="TRIP-002",
            status=TripStatus.COMPLETED,
            planned_distance=400.0,
            actual_distance=420.0,
            planned_start_time=self.now - timedelta(hours=8),
            actual_start_time=self.now - timedelta(hours=8),
            planned_end_time=self.now,
            actual_end_time=self.now + timedelta(hours=5), # 5 hour delay
            vehicle_id=2,
            driver_id=2,
            revenue=50000.0,
            planned_cost=40000.0,
            planned_fuel_liters=150.0,
        )

        expenses = [
            Expense(id=4, trip_id=2, category=ExpenseCategory.FUEL, amount=35000.0, status=ExpenseStatus.RECORDED, business_id="EXP-4", origin_type="test", origin_id="4"),
            Expense(id=5, trip_id=2, category=ExpenseCategory.DETENTION, amount=12000.0, status=ExpenseStatus.RECORDED, business_id="EXP-5", origin_type="test", origin_id="5"),
            Expense(id=6, trip_id=2, category=ExpenseCategory.MAINTENANCE, amount=15000.0, status=ExpenseStatus.RECORDED, business_id="EXP-6", origin_type="test", origin_id="6"),
        ]

        uow = MockUnitOfWork(expenses=expenses, fuel=[], trips=[trip])
        service = TripIntelligenceService(uow)

        res = self.run_async(service.compute_intelligence(trip))

        self.assertEqual(res.financial_summary.revenue, 50000.0)
        self.assertEqual(res.financial_summary.total_cost, 62000.0)
        self.assertEqual(res.financial_summary.net_profit, -12000.0)
        self.assertLess(res.financial_summary.profit_margin_pct, 0)
        self.assertGreater(len(res.profit_loss_contributors), 0)

    def test_3_trip_with_missing_data(self):
        trip = Trip(
            id=3,
            trip_id="TRIP-003",
            status=TripStatus.CREATED,
            origin_location="Delhi",
            destination_location="Jaipur",
        )

        uow = MockUnitOfWork(expenses=[], fuel=[], trips=[trip])
        service = TripIntelligenceService(uow)

        res = self.run_async(service.compute_intelligence(trip))

        self.assertIsNone(res.financial_summary.revenue)
        self.assertIsNone(res.financial_summary.total_cost)
        self.assertIsNone(res.financial_summary.net_profit)
        self.assertFalse(res.financial_summary.has_sufficient_data)
        self.assertFalse(res.efficiency_score.has_sufficient_data)
        self.assertEqual(res.data_quality, DataQuality.INSUFFICIENT)
        self.assertEqual(len(res.cost_breakdown), 0)

    def test_4_unusually_high_fuel_consumption(self):
        trip = Trip(
            id=4,
            trip_id="TRIP-004",
            status=TripStatus.COMPLETED,
            planned_distance=300.0,
            actual_distance=305.0,
            planned_start_time=self.now - timedelta(hours=6),
            actual_start_time=self.now - timedelta(hours=6),
            planned_end_time=self.now,
            actual_end_time=self.now,
            vehicle_id=4,
            driver_id=4,
            revenue=80000.0,
            planned_cost=30000.0,
            planned_fuel_liters=100.0,
        )

        # Actual fuel = 135L (+35% fuel variance)
        fuel_txns = [
            FuelTransaction(id=2, vehicle_id=4, transaction_type=FuelTransactionType.FILL, amount_liters=135.0, timestamp=self.now - timedelta(hours=3))
        ]

        uow = MockUnitOfWork(expenses=[], fuel=fuel_txns, trips=[trip])
        service = TripIntelligenceService(uow)

        res = self.run_async(service.compute_intelligence(trip))

        fuel_insights = [i for i in res.insights if i.insight_type == InsightType.FUEL_ANOMALY]
        self.assertEqual(len(fuel_insights), 1)
        self.assertEqual(fuel_insights[0].severity, InsightSeverity.CRITICAL)
        self.assertIn("35.0% higher", fuel_insights[0].description)

    def test_5_significant_delay_and_detention(self):
        trip = Trip(
            id=5,
            trip_id="TRIP-005",
            status=TripStatus.COMPLETED,
            planned_distance=200.0,
            actual_distance=200.0,
            planned_start_time=self.now - timedelta(hours=5),
            actual_start_time=self.now - timedelta(hours=5),
            planned_end_time=self.now,
            actual_end_time=self.now + timedelta(hours=10), # 10 hours delayed (+200% duration)
            vehicle_id=5,
            driver_id=5,
            revenue=40000.0,
            planned_cost=20000.0,
        )

        expenses = [
            Expense(id=7, trip_id=5, category=ExpenseCategory.DETENTION, amount=8000.0, status=ExpenseStatus.RECORDED, business_id="EXP-7", origin_type="test", origin_id="7")
        ]

        uow = MockUnitOfWork(expenses=expenses, fuel=[], trips=[trip])
        service = TripIntelligenceService(uow)

        res = self.run_async(service.compute_intelligence(trip))

        duration_insights = [i for i in res.insights if i.insight_type == InsightType.DURATION_ANOMALY]
        detention_insights = [i for i in res.insights if i.insight_type == InsightType.DETENTION]

        self.assertEqual(len(duration_insights), 1)
        self.assertEqual(len(detention_insights), 1)
        self.assertIn("Detention charges incurred", detention_insights[0].title)
        self.assertEqual(len(res.recommendations), 2)


if __name__ == "__main__":
    unittest.main()
