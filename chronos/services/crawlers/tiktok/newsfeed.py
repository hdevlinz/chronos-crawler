from typing import Any

from loguru import logger

from chronos.services.crawlers.base import BaseCrawler


class TiktokNewsfeedCrawler(BaseCrawler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    async def execute(self, *args: Any, **kwargs: Any) -> None:
        logger.info("🟡 Start executing newsfeed flow")
