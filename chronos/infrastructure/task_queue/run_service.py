from typing import Any, Dict

from faststream.nats import NatsBroker

from chronos.core.settings import Settings
from chronos.infrastructure.task_queue.base import EnqueuesWithNats


class EnqueueRunServiceWithNats(EnqueuesWithNats):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings=settings)
        self._subject = "run_service"

    async def __call__(self, *, payload: Dict[str, Any]) -> None:
        async with NatsBroker(self.get_nats_url()) as br:
            await br.publish(message=payload, subject=self._subject)
