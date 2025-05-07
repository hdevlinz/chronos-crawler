from typing import Annotated

from dishka.integrations.faststream import FromDishka
from fastapi import Response, status

from chronos.application.task_queue.run_service import EnqueueRunService
from chronos.schemas.services.run_service import RunServicePayload


async def enqueue_run_service(
    *,
    enqueue_run_service: Annotated[EnqueueRunService, FromDishka()],
    body: RunServicePayload,
) -> Response:
    await enqueue_run_service(payload=body.model_dump())

    return Response(status_code=status.HTTP_202_ACCEPTED)
