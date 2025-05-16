from typing import Any, Dict

import aiohttp
from loguru import logger

from chronos.infrastructure.clients.base import BaseClient
from chronos.schemas.captchas import (
    IconCaptchaResponse,
    PuzzleCaptchaResponse,
    RotateCaptchaResponse,
    ShapesCaptchaResponse,
)


class CaptchaClient(BaseClient):
    async def get_puzzle_solution(self, payload: Dict[str, Any]) -> PuzzleCaptchaResponse:
        async with aiohttp.ClientSession() as session:
            resp_data = await self.fetch_data(
                session=session,
                method="POST",
                url=f"{self._host}/slide",
                payload=payload,
            )
            logger.debug(f"🧩 Solution: {resp_data}")

        return PuzzleCaptchaResponse.model_validate(resp_data)

    async def get_shapes_solution(self, payload: Dict[str, Any]) -> ShapesCaptchaResponse:
        async with aiohttp.ClientSession() as session:
            resp_data = await self.fetch_data(
                session=session,
                method="POST",
                url=f"{self._host}/shapes",
                payload=payload,
            )
            logger.debug(f"🧩 Solution: {resp_data}")

        return ShapesCaptchaResponse.model_validate(resp_data)

    async def get_icon_solution(self, payload: Dict[str, Any]) -> IconCaptchaResponse:
        async with aiohttp.ClientSession() as session:
            resp_data = await self.fetch_data(
                session=session,
                method="POST",
                url=f"{self._host}/icon",
                payload=payload,
            )
            logger.debug(f"🧩 Solution: {resp_data}")

        return IconCaptchaResponse.model_validate(resp_data)

    async def get_rotate_solution(self, payload: Dict[str, Any]) -> RotateCaptchaResponse:
        async with aiohttp.ClientSession() as session:
            resp_data = await self.fetch_data(
                session=session,
                method="POST",
                url=f"{self._host}/rotate",
                payload=payload,
            )
            logger.debug(f"🧩 Solution: {resp_data}")

        return RotateCaptchaResponse.model_validate(resp_data)
