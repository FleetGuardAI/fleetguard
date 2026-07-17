import os
import re

services_dir = r"c:\Fleetguard\backend\services"
service_files = [f for f in os.listdir(services_dir) if f.endswith("_service.py")]

for f in service_files:
    path = os.path.join(services_dir, f)
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Ignore auth, operational_event, document, evidence services for now,
    # as they are not explicitly listed in the task for Business Domains,
    # but let's check if they need the UoW. The user said 'Business Services'.
    
    if f in ['auth_service.py', 'operational_event_service.py', 'document_service.py', 'evidence_service.py']:
        continue
    
    # Determine domain name from filename (e.g., fuel_service.py -> fuel)
    domain_name = f.replace('_service.py', '')
    
    # 1. Add import for UoW
    if 'AbstractUnitOfWork' not in content:
        content = re.sub(
            r"(from sqlalchemy\.ext\.asyncio import AsyncSession)",
            r"\1\nfrom infrastructure.uow import AbstractUnitOfWork",
            content
        )
    
    # 2. Replace __init__ signature
    content = re.sub(
        r"def __init__\(self, db: AsyncSession\):.*?self\.repo = [A-Za-z]+Repository\(db\)",
        r"def __init__(self, uow: AbstractUnitOfWork):\n        self.uow = uow",
        content,
        flags=re.DOTALL
    )
    
    # 3. Replace self.repo. with self.uow.repositories.<domain_name>.
    content = content.replace("self.repo.", f"self.uow.repositories.{domain_name}.")
    
    # 4. If any self.db is left, like in FuelService
    if f == 'fuel_service.py':
        content = content.replace("await self.db.get(Truck, truck_id)", "await self.uow.repositories.vehicle.get_vehicle_by_id(truck_id)")
    
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)

print("Done replacing.")
