import asyncio
import json
import random
import re
import tempfile
import time
import traceback
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse

import aiohttp
from loguru import logger
from playwright.async_api import Page, Route
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright_stealth.stealth import StealthConfig, stealth_async

from chronos.infrastructure.browser_use import PatchedBrowserContext
from chronos.infrastructure.exceptions import ApplicationError
from chronos.schemas.creators.creators import CreatorSchema
from chronos.services.captchas.tiktok.solver import TiktokCaptchaSolver
from chronos.services.crawlers.base import BaseCrawler
from chronos.services.crawlers.stealth import AsyncStealth
from chronos.utils.constants import (
    AFFILIATE_CREATOR_NOT_FOUND,
    AFFILIATE_KEYS_TO_OMIT,
    CAPTCHA_NOT_SOLVED,
    TIKTOK_OEMBED_URL,
)
from chronos.utils.helpers import cleanup_temp_file, deep_flatten, deep_merge, deep_omit

if TYPE_CHECKING:
    from chronos.schemas.enums.platforms import PlatformConfig


class TiktokAffiliateCrawler(BaseCrawler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._stealth = AsyncStealth()

        self._otp_wait = 5
        self._list_sleep = 20
        self._creator_sleep = 10

        self._creators_list: List[CreatorSchema] = []
        self._current_creator: Dict[str, Any] = {}
        self._current_handle: str = ""  # uniqueId
        self._current_cid: str = ""  # creatorId
        self._current_req_id: str = ""
        self._current_search_key: str = ""

        self._intercept_pattern = re.compile(r".*/api/v1/oec/affiliate/creator/marketplace/(find|profile)(\?|$)")
        self._detail_query_params = {
            "cid": "",
            "pair_source": "author_search",
            "enter_from": "affiliate_find_creators",
            "search_key": "",
            "req_id": "",
            "query": "",
            "shop_region": "VN",
        }

    async def execute(  # noqa: C901
        self,
        context: PatchedBrowserContext,
        configs: "PlatformConfig",
        limit: Optional[int] = None,
        input_file: Optional[str] = None,
        save_results: bool = False,
        **kwargs: Any,
    ) -> None:
        _, page = kwargs, None
        try:
            page = await self._execute_login_flow(context=context, configs=configs)
            await page.wait_for_load_state(state="load", timeout=0)
            await page.context.route(url=self._intercept_pattern, handler=self._intercept_request)

            self._handle_input_files(input_file=input_file, limit=limit)

            while True:
                logger.info("🔄 Starting a new iteration over creators list")

                creators = self._creators_list or await self._courier_client.get_clairvoy_creators(limit=limit)
                for index, creator in enumerate(creators):
                    logger.info(f"🟢 Processing `{creator.unique_id}` - ({index + 1}/{len(creators)})")
                    start_time = time.time()
                    self._current_handle = creator.unique_id

                    try:
                        if not await self._creator_exists(creator_id=creator.unique_id):
                            continue

                        await self._solve_captcha_if_present(page=page)
                        page = await self._execute_search_flow(
                            context=context,
                            page=page,
                            creator=creator,
                            configs=configs,
                            save_results=save_results,
                        )
                        logger.success(f"✅ Processed `{creator.unique_id}` in {time.time() - start_time:.2f}s")

                        page = await context.get_current_page()
                        await self._stealth.simulate_human_reading(page, self._creator_sleep, context_type="search")

                    except PlaywrightTimeoutError:
                        logger.warning(f"⚠️ Timeout occurred while processing creator `{creator.unique_id}`")
                        try:
                            file_key = f"{self._settings.local_storage_dir}/{self._generate_file_key(
                              platform="tiktok",
                              action="affiliate",
                              subdir="timeout",
                              identifier=creator.unique_id,
                              file_type="png",
                            )}"
                            await page.screenshot(path=file_key, full_page=True)
                            logger.debug(f"📸 Screenshot captured for timeout case — saved to `{file_key}`")
                        except Exception as e:
                            logger.debug(f"🛑 Failed to save screenshot for `{creator.unique_id}`: {e}")

                    logger.info("-" * 30)

                await self._stealth.simulate_human_reading(page=page, duration=self._list_sleep, context_type="search")

        except ApplicationError as e:
            logger.error(f"🛑 {e.detail}")

        except Exception:
            logger.error(f"🛑 {traceback.format_exc()}")
            logger.error("🛑 Unexpected error occurred during affiliate handling")

        finally:
            try:
                await page.unroute(url=self._intercept_pattern) if page else None
                await context.reset_context()
                await context.close()
            except Exception as e:
                logger.debug(f"🛑 Failed to clean up resource: {e}")

    async def _execute_login_flow(self, context: PatchedBrowserContext, configs: "PlatformConfig") -> Page:
        logger.info("🔐 Starting the login process into the system")
        try:
            await context.create_new_tab(url=configs.login_url.format(redirect_url=configs.search_url))
            page = await context.get_current_page()
            await page.wait_for_load_state(state="load", timeout=0)

            config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
            await stealth_async(page=page, config=config)

            if page.url == configs.search_url:
                logger.info("✅ Already logged in; redirected directly to the search page")
                return page

            await page.wait_for_selector(selector=configs.email_panel_selector, state="visible")
            await self._stealth.random_sleep(1.0, 2.0)
            # TODO: Move mouse to the email panel to simulate human behavior
            await page.locator(configs.email_panel_selector).click()

            credentials = await self._courier_client.get_google_credentials()
            if not credentials:
                msg = "Missing credentials"
                raise ValueError(msg)
            logger.debug(f"🔑 Using credentials: `{credentials.username}` / `{credentials.password}`")

            await asyncio.gather(
                page.wait_for_selector(selector=configs.email_input_selector, state="visible"),
                page.wait_for_selector(selector=configs.pwd_input_selector, state="visible"),
            )

            await self._stealth.simulate_typing(page, selector=configs.email_input_selector, text=credentials.username)
            await self._stealth.random_sleep(1.0, 2.0)
            await self._stealth.simulate_typing(page, selector=configs.pwd_input_selector, text=credentials.password)
            await self._stealth.random_sleep(1.0, 2.0)
            await page.locator(configs.pwd_input_selector).press("Enter")

            await self._solve_captcha_if_present(page=page)

            try:
                await page.wait_for_selector(selector=configs.otp_input_selector, state="visible")
                await self._stealth.random_sleep(self._otp_wait, self._otp_wait + 2)

                otp_code = await self._courier_client.get_otp_code()
                if not otp_code:
                    msg = "Missing OTP code"
                    raise ValueError(msg)
                logger.debug(f"🔑 Using OTP code: `{otp_code.value}`")

                await self._stealth.simulate_typing(page, selector=configs.otp_input_selector, text=otp_code.value)
                await self._stealth.random_sleep(1.0, 2.0)
                await page.locator(configs.otp_input_selector).press("Enter")

            except PlaywrightTimeoutError:
                logger.info("⏭️ No OTP required — skipping OTP step")

            logger.success("🎉 Login process successfully completed")
            return page

        except PlaywrightTimeoutError:
            logger.info("ℹ️ Login not required — user is already authenticated")
            return await context.get_current_page()

    async def _execute_search_flow(
        self,
        context: PatchedBrowserContext,
        page: Page,
        creator: CreatorSchema,
        configs: "PlatformConfig",
        save_results: Optional[bool] = None,
    ) -> Page:
        logger.info(f"🔍 Start searching for creator `{creator.unique_id}`")

        await page.wait_for_selector(selector=configs.search_input_selector, state="visible")
        await self._stealth.random_sleep(1.0, 2.0)

        await page.locator(configs.search_input_selector).fill("")
        await self._stealth.simulate_typing(page=page, selector=configs.search_input_selector, text=creator.unique_id)
        await self._stealth.random_sleep(1.0, 2.0)

        await page.locator(configs.search_input_selector).press("Enter")
        await self._stealth.random_sleep(10, 20)

        await self._solve_captcha_if_present(page=page)

        creator_selector = configs.creator_span_selector.format(creator_id=creator.unique_id)
        await page.wait_for_selector(selector=creator_selector, state="visible", timeout=30000)
        await self._stealth.random_sleep(1.0, 2.0)

        if not self._current_cid:
            logger.warning("⚠️ No `creator_oecuid` found in the response, skipping creator")
            return page

        # Build detail query params
        self._detail_query_params["cid"] = self._current_cid
        self._detail_query_params["search_key"] = self._current_search_key
        self._detail_query_params["req_id"] = self._current_req_id
        self._detail_query_params["query"] = self._current_handle
        params = urlencode(self._detail_query_params)

        await page.goto(
            url=f"{configs.creator_detail_url.format(params=params)}",
            timeout=0,
            wait_until="load",
        )
        await self._stealth.simulate_human_reading(page=page, duration=20, context_type="detail")

        if page.url == configs.search_url:
            await page.reload(wait_until="load")
            return await context.get_current_page()

        await self._solve_captcha_if_present(page=page)

        await self._save_creator(creator, creator_data=self._current_creator, is_raw=True)
        creator_data = await self._extract_profiles(creator=creator)
        if not creator_data:
            return await context.get_current_page()

        await self._courier_client.send_crawl_result(
            payload={
                "endpoint": "crawler/results",
                "query": {
                    "source": "affiliate",
                },
                "payload": [creator_data],
            }
        )
        await self._save_creator(creator=creator, creator_data=creator_data) if save_results else None

        self._current_creator = {}
        self._current_handle = ""
        self._current_cid = ""
        self._current_req_id = ""
        self._current_search_key = ""
        await page.goto(url=configs.search_url, timeout=0, wait_until="load")

        return await context.get_current_page()

    async def _solve_captcha_if_present(self, page: Page) -> None:
        captcha_solver = TiktokCaptchaSolver(
            settings=self._settings,
            client=self._captcha_client,
            page=page,
            mouse_step_size=1,
            mouse_step_delay_ms=10,
        )

        if not await captcha_solver.solve_if_present(timeout=15, retries=3):
            raise ApplicationError(
                detail="Failed to solve captcha. Restarting the browser...",
                error_code=CAPTCHA_NOT_SOLVED,
            )

    async def _creator_exists(self, creator_id: str) -> bool:
        logger.info(f"🟠 Start checking existence of creator `{creator_id}` via oembed API")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=TIKTOK_OEMBED_URL.format(unique_id=creator_id)) as resp:
                    if resp.status != 200:
                        logger.warning(f"⚠️ Creator `{creator_id}` does not exist (checked via oembed API)")
                        await self._courier_client.send_crawl_result(
                            payload={
                                "endpoint": "crawler/results/errors",
                                "payload": [
                                    {
                                        "data": {
                                            "unique_id": creator_id,
                                        },
                                        "code": AFFILIATE_CREATOR_NOT_FOUND,
                                        "message": "Creator not found in affiliate system",
                                    }
                                ],
                            }
                        )
                        return False

                    logger.info(f"✅ Creator `{creator_id}` exists (checked via oembed API)")
                    return True

        except Exception as e:
            logger.error(f"🛑 Failed to check existence of creator {creator_id}: {e}")
            return False

    async def _extract_profiles(self, creator: CreatorSchema) -> Optional[Dict[str, Any]]:
        logger.info(f"🟣 Start extracting profiles for creator `{creator.unique_id}`")

        profiles = deep_omit(obj=self._current_creator, keys=AFFILIATE_KEYS_TO_OMIT)
        profiles = deep_flatten(obj=profiles)

        if not profiles or not isinstance(profiles, dict):
            logger.warning(f"⚠️ Invalid response format for creator `{creator.unique_id}`")
            return None

        logger.debug(profiles)
        logger.info(f"✅ Extracted profiles for creator `{creator.unique_id}`")

        return {
            "id": profiles.get("creator_connect_info", {}).get("creator_id", ""),
            "uniqueId": creator.unique_id,
            "nickname": profiles.get("creator_profile", {}).get("nickname", ""),
            "profiles": profiles,
        }

    async def _save_creator(
        self,
        creator: CreatorSchema,
        creator_data: Dict[str, Any],
        is_raw: Optional[bool] = False,
    ) -> None:
        logger.info(f"💾 Start saving creator data for `{creator.unique_id}`")

        temp_file_path = ""
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as temp:
                json.dump(obj=creator_data, fp=temp, ensure_ascii=False, indent=4)
                temp_file_path = temp.name

            file_key = self._generate_file_key(
                platform="tiktok",
                action="affiliate",
                subdir="creators",
                identifier=creator.unique_id,
                file_type="json",
                is_raw=is_raw,
            )
            self._local_storage.upload_file(file_path=temp_file_path, file_key=file_key)

            logger.info(
                f"📂 Successfully saved{' raw' if is_raw else ' extracted'} data of creator: `{creator.unique_id}`"
            )

        except Exception as e:
            logger.error(f"🛑 Failed to save creator data: {e}")

        finally:
            await cleanup_temp_file(file_path=temp_file_path)

    async def _intercept_request(self, route: Route) -> None:
        logger.debug(f"🟤 Intercepting request: `{urlparse(route.request.url).path}`")
        try:
            resp = await route.fetch()
            data: Dict[str, Any] = await resp.json()

            if "/api/v1/oec/affiliate/creator/marketplace/profile" in route.request.url:
                if not data.pop("code") == 0 or not data.pop("message") == "success":
                    logger.warning("⚠️ Invalid response from API")
                    await route.continue_()
                    return

                self._current_creator = deep_merge(dict1=self._current_creator, dict2=data)
                await route.continue_()
                return

            # /api/v1/oec/affiliate/creator/marketplace/find
            if "recommendation_req_id" in data:
                self._current_req_id = data["recommendation_req_id"]
                self._current_search_key = data.get("next_pagination", {}).get("search_key", "")

            creator_profile_list = data.get("creator_profile_list", [])
            self._current_cid = next(
                (
                    creator.get("creator_oecuid", {}).get("value", "")
                    for creator in creator_profile_list
                    if creator.get("handle", {}).get("value", "") == self._current_handle
                ),
                "",
            )

            await route.continue_()

        except Exception as e:
            logger.error(f"{e}")
            await route.continue_()

    def _handle_input_files(self, input_file: Optional[str] = None, limit: Optional[int] = None) -> None:
        if input_file:
            logger.debug(f"📂 Read input file: `{input_file}`")

            usernames = self._local_storage.read_file(file_key=input_file, file_type="json")
            if not isinstance(usernames, list):
                logger.warning("⚠️ Input JSON must be an array of usernames.")
                return

            random.shuffle(usernames)
            usernames = usernames[:limit] if limit and limit > 1 else usernames

            self._creators_list = [CreatorSchema(unique_id=username) for username in usernames]
            logger.debug(f"🎲 Shuffled and prepared {len(self._creators_list)} creators from input file")
