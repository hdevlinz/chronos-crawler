from typing import Any, Dict, Literal, Optional

import aiohttp
from fastapi.encoders import jsonable_encoder
from loguru import logger

from chronos.infrastructure.exceptions import ExternalClientError


class BaseClient:
    def __init__(self, host: str, api_key: Optional[str] = None) -> None:
        self._host = host
        self._api_key = api_key

        self._headers: Dict[str, Any] = {
            "Content-Type": "application/json",
            **({"X-API-Key": self._api_key} if self._api_key else {}),
        }

    async def fetch_data(
        self,
        session: aiohttp.ClientSession,
        method: Literal["GET", "POST"],
        url: str,
        query: Optional[Dict[str, Any]] = None,
        payload: Optional[Any] = None,
        retries: int = 3,
    ) -> Any:
        req_args = {
            "url": url,
            "headers": self._headers,
            "params": query,
        }

        try:
            for i in range(1, retries + 1):
                logger.debug(f"Attempt {i} for {method} request to {url}")

                if method == "POST" and payload is not None:
                    req_args["json"] = jsonable_encoder(payload)

                async with getattr(session, method.lower())(**req_args) as resp:
                    if not resp.ok:
                        continue

                    if resp.content_type == "application/json":
                        resp_data = await resp.json()
                    else:
                        resp_data = await resp.text()

                logger.debug(f"Response from {url}: {resp_data}")
                return resp_data

        except Exception as e:
            raise ExternalClientError(detail=f"Error fetching data from {url}: {e}")

        raise ExternalClientError(detail=f"Max retries exceeded. Unable to fetch valid data from {url}.")

    async def send_data(
        self,
        session: aiohttp.ClientSession,
        url: str,
        payload: Any,
        query: Optional[Dict[str, Any]] = None,
        retries: int = 3,
    ) -> Any:
        request_kwargs = {
            "url": url,
            "headers": self._headers,
            "json": jsonable_encoder(payload),
            "params": query,
        }

        try:
            for i in range(1, retries + 1):
                logger.debug(f"Attempt {i} for POST request to {url}")

                async with session.post(**request_kwargs) as resp:
                    if not resp.ok:
                        continue

                    if resp.content_type == "application/json":
                        resp_data = await resp.json()
                    else:
                        resp_data = await resp.text()

                    logger.debug(f"Response from {url}: {resp_data}")
                    return resp_data

        except Exception as e:
            raise ExternalClientError(detail=f"Error sending data to {url}: {e}")

        raise ExternalClientError(detail=f"Max retries exceeded. Unable to send valid data to {url}.")
