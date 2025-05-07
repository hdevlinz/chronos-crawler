from typing import Any, Dict

import aiohttp
from loguru import logger

from chronos.infrastructure.clients.base import BaseClient
from chronos.schemas.captchas import PuzzleCaptchaResponse


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
