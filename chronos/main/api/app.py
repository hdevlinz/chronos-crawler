from dishka import AsyncContainer

from chronos.core.settings import Settings
from chronos.main.api.factory import APIFactory


def run_api(settings: Settings, container: AsyncContainer, port: int = 8000) -> None:
    factory = APIFactory(container=container, settings=settings)
    app = factory.make()
    factory.run(app=app, port=port)
