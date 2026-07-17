import os
import re

# 1. Update OperationalEventService
oes_path = r"c:\Fleetguard\backend\services\operational_event_service.py"
with open(oes_path, 'r', encoding='utf-8') as f:
    oes = f.read()

# Add UoW import
oes = re.sub(
    r"(from sqlalchemy\.ext\.asyncio import AsyncSession)",
    r"\1\nfrom infrastructure.uow import AbstractUnitOfWork",
    oes
)

# Replace __init__ signature
oes = re.sub(
    r"def __init__\(\s*self,\s*db: AsyncSession,\s*event_bus: Optional\[EventBus\] = None,\s*\) -> None:\s*self\._db = db\s*self\._repo = OperationalEventRepository\(db\)",
    r"def __init__(\n        self,\n        uow: AbstractUnitOfWork,\n        event_bus: Optional[EventBus] = None,\n    ) -> None:\n        self.uow = uow",
    oes
)

# Replace self._repo with self.uow.repositories.operational_event
oes = oes.replace("self._repo", "self.uow.repositories.operational_event")

with open(oes_path, 'w', encoding='utf-8') as f:
    f.write(oes)

# 2. Update main.py
main_path = r"c:\Fleetguard\backend\main.py"
with open(main_path, 'r', encoding='utf-8') as f:
    main = f.read()

main = main.replace(
    "def event_service_factory(db: async_session_factory) -> OperationalEventService:\n    return OperationalEventService(db, event_bus=event_bus)",
    "def event_service_factory(uow) -> OperationalEventService:\n    return OperationalEventService(uow, event_bus=event_bus)"
)
# main.py has another event_service_factory function defined at line 107
main = main.replace(
    "def event_service_factory(db: async_session_factory) -> OperationalEventService:\n    return OperationalEventService(db, event_bus=event_bus)",
    "def event_service_factory(uow) -> OperationalEventService:\n    return OperationalEventService(uow, event_bus=event_bus)"
)

# Now, wait, what about ValidationService which takes db_session_factory?
# The user said no layer BELOW ProcessingEngine should know AsyncSession.
# But ValidationService and EvidenceOrchestrator are ABOVE or on PAR with ProcessingEngine.
# Let's fix main.py
with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main)

# 3. Update routers
routers_dir = r"c:\Fleetguard\backend\routers"
for root, dirs, files in os.walk(routers_dir):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # replace get_db with get_uow
            if "OperationalEventService" in content:
                content = content.replace("from database import get_db", "from database import get_db, get_uow")
                content = content.replace("db: AsyncSession = Depends(get_db)", "uow = Depends(get_uow)")
                content = content.replace("OperationalEventService(db)", "OperationalEventService(uow)")
                content = content.replace("OperationalEventService(db, event_bus)", "OperationalEventService(uow, event_bus)")
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

print("Done refactoring OperationalEventService and routers.")
