import typer

from chronos.core.async_typer import AsyncTyper
from chronos.core.providers.factory import make_container
from chronos.core.settings import settings
from chronos.main.api.app import run_api
from chronos.main.workers.app import run_worker
from chronos.presentation.cli.crawlers import crawler_commands


class CLIFactory:
    def make(self) -> typer.Typer:
        container = make_container(settings=settings)

        app = AsyncTyper(
            rich_markup_mode="rich",
            context_settings={
                "obj": {
                    "container": container,
                    "settings": settings,
                },
            },
        )

        self.add_api_command(app=app)
        self.add_worker_command(app=app)
        self.add_app_commands(app=app)

        return app

    def add_api_command(self, app: AsyncTyper) -> None:
        @app.command(name="api")
        def api(
            ctx: typer.Context,
            port: int = typer.Option(
                8000,
                "--port",
                "-p",
                help="Port to run the API Sever",
            ),
        ) -> None:
            """[green]Run[/green] api."""
            ctx_container = ctx.obj.get("container")
            ctx_settings = ctx.obj.get("settings")
            run_api(settings=ctx_settings, container=ctx_container, port=port)

    def add_worker_command(self, app: AsyncTyper) -> None:
        @app.command(name="worker")
        def worker(ctx: typer.Context) -> None:
            """[green]Run[/green] worker."""
            ctx_container = ctx.obj.get("container")
            ctx_settings = ctx.obj.get("settings")
            run_worker(settings=ctx_settings, container=ctx_container)

    def add_app_commands(self, app: AsyncTyper) -> None:
        app.add_typer(crawler_commands, name="crawler")
