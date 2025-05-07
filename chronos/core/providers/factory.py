from dishka import AsyncContainer, make_async_container

from chronos.core.providers.configs import ConfigsProvider
from chronos.core.providers.connections import ConnectionsProvider
from chronos.core.providers.llm import LLMAdaptersProvider
from chronos.core.providers.managers import ManagersProvider
from chronos.core.providers.services import ServicesProvider
from chronos.core.providers.task_queue import TaskQueueAdaptersProvider
from chronos.core.settings import Settings


def make_container(settings: Settings) -> AsyncContainer:
    container = make_async_container(
        ConfigsProvider(settings=settings),
        ConnectionsProvider(),
        LLMAdaptersProvider(),
        ManagersProvider(),
        ServicesProvider(),
        TaskQueueAdaptersProvider(),
    )

    return container
