from typing import Dict

from dishka import Provider, Scope, provide
from langchain_core.language_models import BaseLanguageModel
from redis.asyncio import ConnectionPool

from chronos.application.task_queue.run_service import EnqueueRunService
from chronos.core.settings import Settings
from chronos.infrastructure.clients.captcha import CaptchaClient
from chronos.infrastructure.clients.courier import CourierClient
from chronos.infrastructure.storage.base import StorageManager
from chronos.schemas.enums.providers import LLMProvider
from chronos.services.browser_use import BrowserUseService


class ServicesProvider(Provider):
    @provide(scope=Scope.APP)
    def browser_use_service(
        self,
        settings: Settings,
        enqueue_service: EnqueueRunService,
        redis_pool: ConnectionPool,
        courier_client: CourierClient,
        captcha_client: CaptchaClient,
        storage_manager: StorageManager,
        llm_providers: Dict[LLMProvider, BaseLanguageModel],
    ) -> BrowserUseService:
        return BrowserUseService(
            settings=settings,
            enqueue_service=enqueue_service,
            redis_pool=redis_pool,
            courier_client=courier_client,
            captcha_client=captcha_client,
            storage_manager=storage_manager,
            llm_providers=llm_providers,
        )
