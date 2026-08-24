import asyncio
from database import get_db, engine, SessionLocal
from models.user import User, UserRole
from services.auth_service import generate_owner_qr_token, verify_owner_qr_token

async def test():
    async with SessionLocal() as db:
        # Create a test user
        user = User(company_id=1, full_name="Test", mobile_number="123999999", password_hash="hash", role=UserRole.COMPANY_ADMIN, is_active=True)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        res = await generate_owner_qr_token(user, db)
        print("Generated:", res.pairing_token)
        
        try:
            res2 = await verify_owner_qr_token(res.pairing_token, db)
            print("Verified successfully!", res2.access_token)
        except Exception as e:
            print("Verification failed:", repr(e))

asyncio.run(test())
