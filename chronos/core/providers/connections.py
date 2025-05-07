from typing import AsyncIterator, Optional

from boto3 import session as boto3_session
from dishka import Provider, Scope, provide
from loguru import logger
from mypy_boto3_s3 import S3Client
from redis.asyncio import ConnectionPool

from chronos.core.settings import Settings
from chronos.infrastructure.clients.captcha import CaptchaClient
from chronos.infrastructure.clients.courier import CourierClient
from chronos.infrastructure.nats_client import NatsClient


class ConnectionsProvider(Provider):
    @provide(scope=Scope.APP)
    async def redis_pool(self, settings: Settings) -> AsyncIterator[ConnectionPool]:
        assert settings.redis_url, "Redis URL is not configured"
        connection_pool = ConnectionPool.from_url(url=settings.redis_url, max_connections=10)
        yield connection_pool

        logger.info("Closing Redis connection pool")
        await connection_pool.disconnect()

    @provide(scope=Scope.APP)
    async def nats_client(self, settings: Settings) -> AsyncIterator[NatsClient]:
        assert settings.nats_url, "NATS URL is not configured"
        nats_client = NatsClient(settings.nats_url)
        yield nats_client

        logger.info("Closing NATS client connection")
        await nats_client.close()

    @provide(scope=Scope.APP)
    async def s3_client(self, settings: Settings) -> Optional[S3Client]:
        if settings.s3_access_key and settings.s3_secret_key:
            session = boto3_session.Session()
            client = session.client(
                service_name="s3",
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region_name,
                endpoint_url=settings.s3_endpoint_url,
            )

            return client

        return None

    @provide(scope=Scope.APP)
    async def captcha_client(self, settings: Settings) -> CaptchaClient:
        assert settings.captcha_host, "Captcha host is not configured"
        return CaptchaClient(host=settings.captcha_host, api_key=settings.captcha_api_key)

    @provide(scope=Scope.APP)
    async def courier_client(self, settings: Settings) -> CourierClient:
        assert settings.courier_host, "Courier host is not configured"
        return CourierClient(host=settings.courier_host, api_key=settings.courier_api_key)
