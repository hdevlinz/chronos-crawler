from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import uvicorn
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from chronos.core.logging import init_logger
from chronos.core.settings import Settings, get_settings
from chronos.presentation.api.default_router import default_router
from chronos.presentation.api.exceptions import setup_exception_handlers
from chronos.presentation.api.root_router import root_router
from chronos.schemas.enums.providers import StorageProvider


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    debug = getattr(app, "debug", False)
    init_logger(debug=debug)
    yield

    state = getattr(app, "state", None)
    if not state:
        return

    dishka_container = getattr(state, "dishka_container", None)
    if not dishka_container:
        return

    await dishka_container.close()
    logger.info("Dishka container closed")


class APIFactory:
    def __init__(self, container: AsyncContainer, settings: Optional[Settings] = None) -> None:
        self._settings = settings if settings else get_settings()
        self._container = container

    def make(self) -> FastAPI:
        app = FastAPI(
            lifespan=lifespan,
            title="Playwright Browser",
            description="Playwright Browser API",
            version="0.1.0",
            debug=self._settings.debug,
            swagger_ui_parameters={
                "defaultModelsExpandDepth": -1,
                "tagsSorter": "alpha",
                "displayRequestDuration": True,
            },
        )

        setup_dishka(container=self._container, app=app)
        setup_exception_handlers(app=app)

        app.include_router(router=default_router)
        app.include_router(router=root_router)

        if self._settings.storage_provider == StorageProvider.LOCAL:
            app.mount(
                name="storage",
                path=f"/{self._settings.local_storage_dir or 'storage'}",
                app=StaticFiles(directory=f"{self._settings.local_storage_dir or 'storage'}", check_dir=False),
            )

        return app

    def run(self, app: FastAPI, host: str = "0.0.0.0", port: int = 8000) -> None:
        uvicorn.run(app=app, host=host, port=port)
