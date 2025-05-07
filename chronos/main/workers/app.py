import asyncio

from dishka import AsyncContainer

from chronos.core.settings import Settings
from chronos.main.workers.factory import WorkerFactory


def run_worker(settings: Settings, container: AsyncContainer) -> None:
    factory = WorkerFactory(container=container, settings=settings)
    app = factory.make()
    asyncio.run(app.run())
