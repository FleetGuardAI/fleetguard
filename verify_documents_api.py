import asyncio
import os
import sys

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from database import async_session_maker
from models.user import User, UserRole
from models.driver import Driver
from models.document import Document
from main import app
from auth.security import create_access_token

async def test_endpoint():
    async with async_session_maker() as session:
        # Find a real driver
        result = await session.execute(select(Driver).limit(1))
        driver = result.scalar_one_or_none()
        
        if not driver:
            print("No driver found to test.")
            return

        result = await session.execute(select(User).where(User.mobile_number == driver.phone_number))
        user = result.scalar_one_or_none()

        if not user:
            print("No user found for driver.")
            return
            
        print(f"Testing with Driver ID: {driver.id}, Phone: {driver.phone_number}")
        
        # Create token
        token = create_access_token(data={"sub": user.mobile_number, "role": user.role.value})
        
        # Make request
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/driver-app/documents",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"Error detail: {response.json()}")
            else:
                import json
                print("Response JSON:")
                print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(test_endpoint())
