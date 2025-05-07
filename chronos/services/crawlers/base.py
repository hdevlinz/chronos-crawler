from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from browser_use.agent.service import Agent
from langchain_core.language_models import BaseLanguageModel
from redis.asyncio import ConnectionPool

from chronos.application.task_queue.run_service import EnqueueRunService
from chronos.core.settings import Settings
from chronos.infrastructure.browser_use import PatchedBrowserContext
from chronos.infrastructure.clients.captcha import CaptchaClient
from chronos.infrastructure.clients.courier import CourierClient
from chronos.infrastructure.storage.base import StorageManager
from chronos.infrastructure.storage.local import LocalStorageManager


class BaseCrawler(ABC):
    def __init__(
        self,
        settings: Settings,
        enqueue_service: EnqueueRunService,
        redis_pool: ConnectionPool,
        courier_client: CourierClient,
        captcha_client: CaptchaClient,
        storage_manager: StorageManager,
        llm_provider: Optional[BaseLanguageModel] = None,
    ) -> None:
        self._settings = settings
        self._enqueue_service = enqueue_service
        self._redis_pool = redis_pool
        self._courier_client = courier_client
        self._captcha_client = captcha_client
        self._storage_manager = storage_manager
        self._llm_provider = llm_provider

        self._local_storage = LocalStorageManager(settings=self._settings)

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    async def create_agent(self, task: str, context: PatchedBrowserContext) -> Agent:
        assert self._llm_provider is not None, "LLM provider is not set"
        return Agent(task=task, llm=self._llm_provider, browser_context=context)

    def _generate_file_key(
        self,
        platform: str,
        action: str,
        subdir: str,
        identifier: str,
        file_type: str = "json",
        is_raw: Optional[bool] = False,
    ) -> str:
        current_time = datetime.now()
        timestamp_str = current_time.strftime("%y%m%d_%H%M%S")
        raw_part = "raw_" if is_raw else ""
        filename = f"insight_{raw_part}{timestamp_str}"

        return f"{platform.lower()}/{action.lower()}/{subdir.lower()}/" f"{identifier.lower()}/{filename}.{file_type}"
