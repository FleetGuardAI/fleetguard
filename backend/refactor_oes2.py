import re

oes_path = r"c:\Fleetguard\backend\services\operational_event_service.py"
with open(oes_path, 'r', encoding='utf-8') as f:
    oes = f.read()

# 1. Remove EventBus import
oes = re.sub(r"from infrastructure\.events\.bus import EventBus\n", "", oes)

# 2. Update __init__
oes = re.sub(
    r"def __init__\(\n\s*self,\n\s*uow: AbstractUnitOfWork,\n\s*event_bus: Optional\[EventBus\] = None,\n\s*\) -> None:\n\s*self\.uow = uow\n\s*self\._event_bus = event_bus",
    r"def __init__(\n        self,\n        uow: AbstractUnitOfWork,\n    ) -> None:\n        self.uow = uow",
    oes
)

# 3. Update create_event
create_event_search = """        # Extension point — Event Dispatcher / Fleet Memory (not yet implemented)
        await self._after_create(persisted)"""
        
create_event_replace = """        # Stage the event in the Outbox to guarantee delivery
        outbox_payload = OperationalEventResponse.model_validate(persisted).model_dump(mode="json")
        await self.uow.repositories.outbox.create_event(
            topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
            payload=outbox_payload,
            event_id=str(persisted.id)
        )"""

oes = oes.replace(create_event_search, create_event_replace)

# 4. Remove _after_create
after_create_pattern = r"\s*async def _after_create\(self, event: OperationalEvent\) -> None:[\s\S]*?(?=async def _before_status_change)"
oes = re.sub(after_create_pattern, "\n    ", oes)

with open(oes_path, 'w', encoding='utf-8') as f:
    f.write(oes)

print("Updated OperationalEventService.")
