from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger
from pydantic import TypeAdapter

from chronos.infrastructure.clients.base import BaseClient
from chronos.presentation.api.base_response import ResponseBase
from chronos.schemas.creators.creators import CreatorSchema
from chronos.schemas.credentials import CredentialsSchema, OTPCodeSchema


class CourierClient(BaseClient):
    def __init__(self, *arg: Any, **kwargs: Any) -> None:
        super().__init__(*arg, **kwargs)
        self._api_version = "api/v1"
        self._versioned_url = f"{self._host}/{self._api_version}"

    async def get_google_credentials(self, endpoint: str = "google/credentials") -> Optional[CredentialsSchema]:
        logger.info("📥 Fetching google credentials...")
        try:
            async with aiohttp.ClientSession() as session:
                resp = await self.fetch_data(
                    session=session,
                    method="GET",
                    url=f"{self._versioned_url}/{endpoint}",
                )
                resp_data: ResponseBase = ResponseBase.model_validate(resp)

            return CredentialsSchema.model_validate(resp_data.data)
        except Exception as e:
            logger.error(f"🛑 Failed to fetch google credentials: {e}")
            return None

    async def get_otp_code(
        self,
        endpoint: str = "google/gmail/otp",
        query: Optional[Dict[str, Any]] = None,
    ) -> Optional[OTPCodeSchema]:
        logger.info("📬 Fetching OTP code...")

        default_query = {
            "otp_length": 6,
            "days_ago": 0,  # Now
            "from_email": "register@account.tiktok.com",
            "subject": "verification code",
        }

        if query:
            default_query.update(query)

        try:
            async with aiohttp.ClientSession() as session:
                resp = await self.fetch_data(
                    session=session,
                    method="GET",
                    url=f"{self._versioned_url}/{endpoint}",
                    query=default_query,
                )
                resp_data: ResponseBase = ResponseBase.model_validate(resp)

            return OTPCodeSchema.model_validate(resp_data.data)
        except Exception as e:
            logger.error(f"🛑 Failed to fetch OTP code: {e}")
            return None

    async def get_clairvoy_creators(
        self,
        endpoint: str = "clairvoy/creators",
        limit: Optional[int] = None,
    ) -> List[CreatorSchema]:
        logger.info("📊 Fetching creators...")

        payload = {
            "endpoint": "crawler/creators",
            "query": {
                "limit": limit,
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                resp = await self.fetch_data(
                    session=session,
                    method="POST",
                    url=f"{self._versioned_url}/{endpoint}",
                    payload=payload,
                )
                resp_data: ResponseBase = ResponseBase.model_validate(resp)

            logger.info(f"✅ Fetched {len(resp_data.data['items'])} creators from Clairvoy")  # type: ignore
            creators = TypeAdapter(List[CreatorSchema]).validate_python(resp_data.data["items"])  # type: ignore
            return creators

        except Exception as e:
            logger.error(f"🛑 Failed to fetch Clairvoy creators: {e}")
            return []

    async def send_crawl_result(self, payload: Any, endpoint: str = "clairvoy") -> None:
        logger.info("📤 Sending crawl result...")
        try:
            async with aiohttp.ClientSession() as session:
                await self.send_data(
                    session=session,
                    url=f"{self._versioned_url}/{endpoint}",
                    payload=payload,
                )
                logger.info("✅ Payload sent successfully")

        except Exception as e:
            logger.error(f"🛑 Failed to send crawl result: {e}")
