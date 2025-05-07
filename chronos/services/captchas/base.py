import asyncio
import json
import re
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar

from loguru import logger
from playwright.async_api import FloatRect, Page

from chronos.core.settings import Settings
from chronos.infrastructure.clients.captcha import CaptchaClient
from chronos.infrastructure.storage.local import LocalStorageManager
from chronos.schemas.enums.captchas import CaptchaType
from chronos.utils.helpers import cleanup_temp_file

T = TypeVar("T")


class BaseCaptchaSolver(ABC):
    def __init__(
        self,
        settings: Settings,
        client: CaptchaClient,
        page: Page,
        mouse_step_size: int = 1,
        mouse_step_delay_ms: int = 10,
    ) -> None:
        self._settings = settings
        self._client = client
        self._page = page
        self._mouse_step_size = mouse_step_size
        self._mouse_step_delay_ms = mouse_step_delay_ms

        self._local_storage = LocalStorageManager(settings=self._settings)

    async def solve_if_present(self, timeout: int = 15, retries: int = 3) -> bool:
        if not await self.captcha_is_present(timeout=timeout):
            return True

        match await self.identify_captcha():
            case CaptchaType.PUZZLE_V1:
                return await self.solve_puzzle_v1(retries=retries)
            case CaptchaType.PUZZLE_V2:
                return await self.solve_puzzle_v2(retries=retries)
            case CaptchaType.SHAPES_V1:
                return await self.solve_shapes_v1(retries=retries)
            case CaptchaType.SHAPES_V2:
                return await self.solve_shapes_v2(retries=retries)
            case CaptchaType.ICON_V1:
                return await self.solve_icon_v1(retries=retries)
            case CaptchaType.ICON_V2:
                return await self.solve_icon_v2(retries=retries)
            case CaptchaType.ROTATE_V1:
                return await self.solve_rotate_v1(retries=retries)
            case CaptchaType.ROTATE_V2:
                return await self.solve_rotate_v2(retries=retries)

        return False

    async def _any_selector_visible(self, selectors: List[str]) -> bool:
        for selector in selectors:
            elements = await self._page.locator(selector=selector).all()
            if not elements:
                continue

            visible_results = await asyncio.gather(*(element.is_visible() for element in elements))
            if any(visible_results):
                logger.debug(f"👁️ Selector visible: `{selector}`")
                return True

        return False

    async def _get_image_url(self, selector: str) -> str:
        try:
            element = self._page.locator(selector=selector)
            url = await element.get_attribute(name="src")
            if not url:
                msg = f"Image URL was None for selector: {selector}"
                raise ValueError(msg)

            logger.debug(f"🖼️ Image URL for selector `{selector}`: `{url}`")
            return url

        except Exception as e:
            logger.error(f"❌ Error while getting image URL for selector `{selector}`: {e}")
            raise

    async def _get_bounding_box(self, selector: str) -> FloatRect:
        try:
            element = self._page.locator(selector=selector)
            box = await element.bounding_box()
            if not box:
                msg = f"Element was found but had no bounding box (selector: `{selector}`)"
                raise AttributeError(msg)

            logger.debug(f"📦 Bounding box for selector `{selector}`: {box}")
            return box

        except Exception as e:
            logger.error(f"❌ Error while getting bounding box for selector `{selector}`: {e}")
            raise

    async def _get_style_attribute(
        self,
        selector: str,
        attr: str,
        type_cast: Callable[[str], T] = str,  # type: ignore
        default: Optional[T] = None,
        strict: bool = True,
    ) -> T:
        def _clean_numeric(value: str) -> str:
            match = re.match(r"[-+]?[0-9]*\.?[0-9]+", value)
            return match.group(0) if match else value

        try:
            element = self._page.locator(selector=selector)
            style = await element.get_attribute("style")
            if not style:
                if not strict and default is not None:
                    logger.warning(f"⚠️ No style attribute found on element: {selector}, returning default: {default}")
                    return default
                msg = f"No style attribute found on element: {selector}"
                raise ValueError(msg)

            pattern = rf"{attr}\s*:\s*([^;]+)"
            match = re.search(pattern, style)
            if not match:
                if not strict and default is not None:
                    logger.warning(f"⚠️ Attribute '{attr}' not found in style: {style}, returning default: {default}")
                    return default
                msg = f"Attribute '{attr}' not found in style: `{style}` (selector: `{selector}`)"
                raise ValueError(msg)

            value_str = match.group(1).strip()

            if type_cast in [float, int]:
                value_str = _clean_numeric(value_str)

            result = type_cast(value_str)
            logger.debug(f"🎯 Style attribute '{attr}' for selector `{selector}`: `{result}`")
            return result

        except Exception as e:
            logger.error(f"❌ Error while getting style attribute `{attr}` for selector `{selector}`: {e}")
            if not strict and default is not None:
                logger.warning(f"⚠️ Returning default value for `{attr}` in selector `{selector}`: `{default}`")
                return default
            raise

    async def _save_captcha_logs(
        self,
        type: str,
        status: str,
        platform: str,
        extra: Dict[str, Any],
    ) -> None:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": type.lower(),
            "status": status.lower(),
            **extra,
        }

        current_time = datetime.now()
        timestamp_str = current_time.strftime("%y%m%d_%H%M%S")
        file_key = f"{platform.lower()}/captchas/{type.lower()}/{status.lower()}/{timestamp_str}.json"

        temp_file_path = ""
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as temp:
                json.dump(obj=log_data, fp=temp, ensure_ascii=False, indent=4)
                temp_file_path = temp.name

            self._local_storage.upload_file(file_path=temp_file_path, file_key=file_key)
            logger.info(f"📂 Successfully saved captcha log: `{type} - {status}`")

        except Exception as e:
            logger.error(f"❌ Failed to save captcha log: {e}")

        finally:
            await cleanup_temp_file(file_path=temp_file_path)

    @abstractmethod
    async def captcha_is_present(self, timeout: int = 15) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def captcha_is_not_present(self, timeout: int = 15) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def identify_captcha(self) -> Optional[CaptchaType]:
        raise NotImplementedError

    async def solve_puzzle_v1(self, retries: int = 3) -> bool:
        raise NotImplementedError

    async def solve_puzzle_v2(self, retries: int = 3) -> bool:
        raise NotImplementedError

    async def solve_shapes_v1(self, retries: int = 3) -> bool:
        raise NotImplementedError

    async def solve_shapes_v2(self, retries: int = 3) -> bool:
        raise NotImplementedError

    async def solve_icon_v1(self, retries: int = 3) -> bool:
        raise NotImplementedError

    async def solve_icon_v2(self, retries: int = 3) -> bool:
        raise NotImplementedError

    async def solve_rotate_v1(self, retries: int = 3) -> bool:
        raise NotImplementedError

    async def solve_rotate_v2(self, retries: int = 3) -> bool:
        raise NotImplementedError
