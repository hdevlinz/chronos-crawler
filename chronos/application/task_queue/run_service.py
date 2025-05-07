from typing import Any, Dict, Protocol


class EnqueueRunService(Protocol):
    async def __call__(self, *, payload: Dict[str, Any]) -> None:
        raise NotImplementedError
