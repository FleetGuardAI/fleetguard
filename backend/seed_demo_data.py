import asyncio
import os
import argparse
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import uuid

# Models
from database import Base
from models.user import User
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus
from models.trip_domain import Trip, TripStatus
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
# from models.ticket import Ticket, TicketPriority, TicketStatus

async def seed_data(email: str):
    import dotenv
    dotenv.load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgresql+asyncpg://"):
        pass
    else:
        db_url = "sqlite+aiosqlite:///./fleetguard.db"

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    from database import create_all_tables
    await create_all_tables()

    async with async_session() as session:
        # Find user and company
        result = await session.execute(select(User))
        users = result.scalars().all()
        print("Users in DB:", [u.email for u in users])
        print("Looking for:", email)
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user:
            print(f"User with email {email} not found. Ensure the user is registered.")
            return

        company_id = user.company_id
        if not company_id:
            print("User has no associated company.")
            return

        print(f"Found user {user.full_name} for company ID {company_id}.")
        
        # Trucks
        trucks_data = [
            {"reg": "MH04AB1234", "make": "Tata", "model": "Signa 4923.S"},
            {"reg": "MH04AB5678", "make": "Ashok Leyland", "model": "3118 IL"},
            {"reg": "GJ01XY9012", "make": "Eicher", "model": "Pro 3015"},
            {"reg": "DL1PB3456", "make": "Mahindra", "model": "Blazo X 49"},
            {"reg": "MH43CD7890", "make": "Tata", "model": "Prima 3530.K"}
        ]
        
        vehicles = []
        for t in trucks_data:
            result = await session.execute(select(Vehicle).where(Vehicle.registration_number == t["reg"]))
            v = result.scalars().first()
            if not v:
                v = Vehicle(
                    registration_number=t["reg"],
                    make=t["make"],
                    model=t["model"],
                    year=2022,
                    tank_capacity=400.0,
                    status=VehicleStatus.ACTIVE,
                    company_id=company_id
                )
                session.add(v)
            vehicles.append(v)
        
        await session.commit()
        for v in vehicles:
            await session.refresh(v)
            
        # Drivers
        drivers_data = [
            {"name": "Ramesh Kumar", "phone": "+919876543210", "license": "MH1420101234567"},
            {"name": "Suresh Singh", "phone": "+919876543211", "license": "MH1420101234568"},
            {"name": "Abdul Rehman", "phone": "+919876543212", "license": "MH1420101234569"},
            {"name": "Vikram Patel", "phone": "+919876543213", "license": "MH1420101234570"},
            {"name": "Rajesh Sharma", "phone": "+919876543214", "license": "MH1420101234571"},
        ]
        
        drivers = []
        for i, d in enumerate(drivers_data):
            result = await session.execute(select(Driver).where(Driver.phone_number == d["phone"]))
            dr = result.scalars().first()
            if not dr:
                dr = Driver(
                    employee_id=f"DRV-{i+100}",
                    name=d["name"],
                    phone_number=d["phone"],
                    license_number=d["license"],
                    status=DriverStatus.ACTIVE,
                    company_id=company_id
                )
                session.add(dr)
            drivers.append(dr)
            
        await session.commit()
        for dr in drivers:
            await session.refresh(dr)
            
        # Assign Drivers to Vehicles
        for i in range(min(len(vehicles), len(drivers))):
            vehicles[i].assigned_driver_id = drivers[i].id
            
        await session.commit()
        
        # Clean up previously seeded trips, expenses, and notifications for this company
        await session.execute(
            Expense.__table__.delete().where(
                Expense.company_id == company_id,
                Expense.origin_type == "seed"
            )
        )
        await session.execute(
            Trip.__table__.delete().where(
                Trip.company_id == company_id,
                Trip.origin_type == "seed"
            )
        )
        from models.notification import Notification
        await session.execute(
            Notification.__table__.delete().where(
                Notification.company_id == company_id,
                Notification.title.in_(["Trip Completed", "Maintenance Due", "Expense Recorded"])
            )
        )
        await session.commit()

        # Trips
        now = datetime.now(timezone.utc)
        trips_data = [
            {"vid": vehicles[0].id, "did": drivers[0].id, "origin": "Mumbai, MH", "dest": "Delhi, DL", "status": TripStatus.IN_PROGRESS, "dist": 1400.0, "rev": 45000.0, "fuel": 300, "toll": 5000},
            {"vid": vehicles[1].id, "did": drivers[1].id, "origin": "Pune, MH", "dest": "Bangalore, KA", "status": TripStatus.COMPLETED, "dist": 850.0, "rev": 30000.0, "fuel": 200, "toll": 3000},
            {"vid": vehicles[2].id, "did": drivers[2].id, "origin": "Ahmedabad, GJ", "dest": "Surat, GJ", "status": TripStatus.COMPLETED, "dist": 260.0, "rev": 12000.0, "fuel": 60, "toll": 800},
            {"vid": vehicles[3].id, "did": drivers[3].id, "origin": "Delhi, DL", "dest": "Jaipur, RJ", "status": TripStatus.IN_PROGRESS, "dist": 280.0, "rev": 15000.0, "fuel": 70, "toll": 1000},
            {"vid": vehicles[4].id, "did": drivers[4].id, "origin": "Chennai, TN", "dest": "Hyderabad, TS", "status": TripStatus.CREATED, "dist": 620.0, "rev": 22000.0, "fuel": 0, "toll": 0},
        ]
        
        trips_created = 0
        expenses_created = 0
        
        for i, t in enumerate(trips_data):
            trip_code = f"TRP-{uuid.uuid4().hex[:6].upper()}"
            start_time = now - timedelta(days=i)
            end_time = start_time + timedelta(hours=i*5 + 10) if t["status"] == TripStatus.COMPLETED else None
            
            trip = Trip(
                trip_id=trip_code,
                status=t["status"],
                origin_location=t["origin"],
                destination_location=t["dest"],
                actual_distance=t["dist"],
                actual_start_time=start_time,
                actual_end_time=end_time,
                vehicle_id=t["vid"],
                driver_id=t["did"],
                company_id=company_id,
                revenue=t["rev"],
                planned_cost=t["fuel"]*90 + t["toll"],
                origin_type="seed",
                origin_id="seed"
            )
            session.add(trip)
            trips_created += 1
            
            # Add expenses for completed/in-progress trips
            if t["fuel"] > 0:
                exp_fuel = Expense(
                    business_id=f"EXP-F-{uuid.uuid4().hex[:8]}",
                    category=ExpenseCategory.FUEL,
                    amount=t["fuel"] * 90.0,  # Assume 90 INR/L
                    currency="INR",
                    status=ExpenseStatus.APPROVED,
                    expense_date=start_time + timedelta(hours=1),
                    company_id=company_id,
                    vehicle_id=t["vid"],
                    driver_id=t["did"],
                    origin_type="seed",
                    origin_id="seed"
                )
                session.add(exp_fuel)
                expenses_created += 1
                
            if t["toll"] > 0:
                exp_toll = Expense(
                    business_id=f"EXP-T-{uuid.uuid4().hex[:8]}",
                    category=ExpenseCategory.TOLL,
                    amount=float(t["toll"]),
                    currency="INR",
                    status=ExpenseStatus.APPROVED,
                    expense_date=start_time + timedelta(hours=2),
                    company_id=company_id,
                    vehicle_id=t["vid"],
                    driver_id=t["did"],
                    origin_type="seed",
                    origin_id="seed"
                )
                session.add(exp_toll)
                expenses_created += 1
                    
        # General expenses
        general_exp = [
            ExpenseCategory.MAINTENANCE, ExpenseCategory.TYRE, ExpenseCategory.SALARY, ExpenseCategory.MISCELLANEOUS
        ]
        for i, cat in enumerate(general_exp):
            exp = Expense(
                business_id=f"EXP-G-{uuid.uuid4().hex[:8]}",
                category=cat,
                amount=5000.0 * (i+1),
                currency="INR",
                status=ExpenseStatus.APPROVED,
                expense_date=now - timedelta(days=i*2),
                company_id=company_id,
                origin_type="seed",
                origin_id="seed"
            )
            session.add(exp)
            expenses_created += 1
            
        # Notifications
        from models.notification import NotificationCategory
        notifs = [
            {"cat": NotificationCategory.TRIP, "title": "Trip Completed", "desc": f"Trip {trips_data[1]['vid']} completed successfully."},
            {"cat": NotificationCategory.VEHICLE, "title": "Maintenance Due", "desc": f"Vehicle {vehicles[0].registration_number} requires maintenance."},
            {"cat": NotificationCategory.FINANCE, "title": "Expense Recorded", "desc": "A toll expense of 5000 was recorded."},
        ]
        
        for i, n in enumerate(notifs):
            notif = Notification(
                category=n["cat"],
                title=n["title"],
                description=n["desc"],
                is_read=False,
                company_id=company_id,
                user_id=user.id,
                created_at=now - timedelta(hours=i)
            )
            session.add(notif)
            
        await session.commit()
        
        print("\n========================================")
        print("Seed completed successfully")
        print("========================================")
        print("User:")
        print(f"  email: {email}")
        print(f"  user_id: {user.id}")
        print(f"  company_id: {company_id}")
        print("\nCreated/Verified:")
        print(f"  Trucks: {len(vehicles)}")
        print(f"  Drivers: {len(drivers)}")
        print(f"  Trips: {trips_created}")
        print(f"  Expenses: {expenses_created}")
        print(f"  Notifications: {len(notifs)}")
        print("========================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data for a specific user.")
    parser.add_argument("--email", required=True, help="Email of the user/company owner to seed data for")
    args = parser.parse_args()
    
    asyncio.run(seed_data(args.email))
