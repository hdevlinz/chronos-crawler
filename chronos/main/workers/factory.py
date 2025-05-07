from typing import Optional

from dishka import AsyncContainer
from dishka.integrations.faststream import setup_dishka
from faststream import FastStream
from faststream.nats import NatsBroker

from chronos.core.logging import init_logger
from chronos.core.settings import Settings, get_settings
from chronos.presentation.workers.router import router


class WorkerFactory:
    def __init__(self, container: AsyncContainer, settings: Optional[Settings] = None) -> None:
        self._settings = settings if settings else get_settings()
        self._container = container

    def get_nats_url(self) -> str:
        assert self._settings.nats_url is not None, "NATS URL is not configured"
        return self._settings.nats_url

    def make(self) -> FastStream:
        broker = NatsBroker(servers=self.get_nats_url())
        broker.include_router(router=router)
        app = FastStream(broker=broker)

        setup_dishka(container=self._container, app=app)
        init_logger(debug=self._settings.debug)

        return app
