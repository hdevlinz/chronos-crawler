import json

from nats.aio.client import Client as NATS  # noqa: N814


class NatsClient:
    def __init__(self, url: str):
        self._url = url
        self._client = NATS()

    async def connect(self) -> None:
        await self._client.connect(
            servers=[self._url],
            max_reconnect_attempts=60,
            connect_timeout=30,
            reconnect_time_wait=2,
            max_outstanding_pings=2,
        )

    async def publish(self, subject: str, message: dict, drain: bool = True) -> None:
        await self.connect()
        if self._client.is_connected:
            json_message = json.dumps(message)
            await self._client.publish(subject, json_message.encode())
            await self._client.flush()
            if drain:
                await self._client.drain()

    async def close(self) -> None:
        if self._client.is_connected:
            await self._client.flush()
            await self._client.drain()
            await self._client.close()
