from typing import Dict, List, Optional

from browser_use import BrowserConfig, BrowserContextConfig
from langchain_core.language_models import BaseLanguageModel
from redis.asyncio import ConnectionPool

from chronos.application.task_queue.run_service import EnqueueRunService
from chronos.core.settings import Settings
from chronos.infrastructure.browser_use import BrowserClient
from chronos.infrastructure.clients.captcha import CaptchaClient
from chronos.infrastructure.clients.courier import CourierClient
from chronos.infrastructure.storage.base import StorageManager
from chronos.schemas.enums.platforms import Platform
from chronos.schemas.enums.providers import LLMProvider


class BrowserUseService:
    def __init__(
        self,
        settings: Settings,
        enqueue_service: EnqueueRunService,
        redis_pool: ConnectionPool,
        courier_client: CourierClient,
        captcha_client: CaptchaClient,
        storage_manager: StorageManager,
        llm_providers: Dict[LLMProvider, BaseLanguageModel],
    ) -> None:
        self._settings = settings
        self._enqueue_service = enqueue_service
        self._redis_pool = redis_pool
        self._courier_client = courier_client
        self._captcha_client = captcha_client
        self._storage_manager = storage_manager
        self._llm_providers = llm_providers

        self._trace_path = self._settings.trace_path
        self._cookies_file = self._settings.cookies_file

    def _new_browser(
        self,
        headless: bool = False,
        disable_security: bool = True,
        extra_chromium_args: List[str] = [],
        browser_path: Optional[str] = None,
        wss_url: Optional[str] = None,
        cdp_url: Optional[str] = None,
    ) -> BrowserClient:
        # Default arguments
        extra_chromium_args.extend(
            [
                #  "--disable-blink-features=AutomationControlled",
                #  "--disable-infobars",
                #  "--disable-background-timer-throttling",
                #  "--disable-popup-blocking",
                #  "--disable-backgrounding-occluded-windows",
                #  "--disable-renderer-backgrounding",
                #  "--disable-window-activation",
                #  "--disable-focus-on-load",
                #  "--no-first-run",
                #  "--no-default-browser-check",
                #  "--no-startup-window",
                #  "--window-position=0,0",
                #  "--disable-dev-shm-usage",
                #  "--enable-automation",
                #  "--hide-scrollbars",
                #  "--mute-audio",
                #  "--disable-web-security",
            ]
        )

        if headless:
            extra_chromium_args.append("--headless")

        return BrowserClient(
            config=BrowserConfig(
                headless=headless,
                disable_security=disable_security,
                extra_chromium_args=extra_chromium_args,
                chrome_instance_path=browser_path,
                wss_url=wss_url,
                cdp_url=cdp_url,
            )
        )

    async def run_crawler(
        self,
        platform: str,
        action: str,
        limit: Optional[int] = None,
        input_file: Optional[str] = None,
        save_results: bool = False,
        headless: bool = False,
        browser_path: Optional[str] = None,
        reopen_browser: bool = False,
    ) -> None:
        platform_class = Platform.from_str(key=f"{platform.upper()}_{action.upper()}")

        # Get the appropriate LLM based on settings
        llm_provider = self._settings.llm_provider
        llm_provider_class = self._llm_providers.get(llm_provider)

        # Create the appropriate crawler using the factory
        crawler = platform_class.crawler(
            settings=self._settings,
            enqueue_service=self._enqueue_service,
            redis_pool=self._redis_pool,
            courier_client=self._courier_client,
            captcha_client=self._captcha_client,
            storage_manager=self._storage_manager,
            llm_provider=llm_provider_class,
        )

        context_config = BrowserContextConfig(trace_path=self._trace_path, cookies_file=self._cookies_file)
        while True:
            browser = self._new_browser(headless=headless, browser_path=browser_path)
            browser_context = await browser.new_context(config=context_config)
            async with browser_context as context:
                await crawler.execute(
                    configs=platform_class.configs,
                    context=context,
                    limit=limit,
                    input_file=input_file,
                    save_results=save_results,
                )

            if not reopen_browser:
                break
