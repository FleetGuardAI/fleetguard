import asyncio
import os
from dotenv import load_dotenv

async def inspect():
    from config import settings
    import models
    from database import Base
    
    tables = Base.metadata.tables.keys()
    print("Models defined in SQLAlchemy:")
    for t in tables:
        print(f" - {t}")

if __name__ == "__main__":
    asyncio.run(inspect())
