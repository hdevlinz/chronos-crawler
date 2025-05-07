from typing import Optional

import typer
from dishka import AsyncContainer

from chronos.core.async_typer import AsyncTyper
from chronos.services.browser_use import BrowserUseService

crawler_commands = AsyncTyper(
    name="crawler",
    help="[yellow]Manage[/yellow] crawler",
)


@crawler_commands.command()
async def run_crawler(
    ctx: typer.Context,
    platform: str = typer.Option(
        ...,
        "--platform",
        "-p",
        help="Target platform to crawl (e.g., tiktok, facebook, etc.)",
    ),
    action: str = typer.Option(
        ...,
        "--action",
        "-a",
        help="Action or workflow to perform (e.g., affiliate, search, etc). Maps to a specific crawler handler.",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of items (e.g., creators, posts) to process. If not provided, all items will be processed.",  # noqa: E501
    ),
    input_file: Optional[str] = typer.Option(
        None,
        "--input-file",
        help="Path to a JSON file in storage/ containing input data (e.g., list of usernames).",
    ),
    save_results: bool = typer.Option(
        False,
        "--save-results",
        help="Save the crawling result to a file in the storage/ directory.",
    ),
    headless: bool = typer.Option(
        False,
        "--headless",
        help="Run the browser in headless mode.",
    ),
    browser_path: Optional[str] = typer.Option(
        None,
        "--browser-path",
        help="Path to the browser executable. If not provided, the default browser will be used.",
    ),
    reopen_browser: bool = typer.Option(
        False,
        "--reopen-browser",
        help="Reopen the browser for each run. If set to true, the browser will be closed and reopened for each run.",  # noqa: E501
    ),
) -> None:
    """[green]Run[/green] crawler task."""
    ctx_container: AsyncContainer = ctx.obj.get("container")
    browser_task_service: BrowserUseService = await ctx_container.get(BrowserUseService)
    await browser_task_service.run_crawler(
        platform=platform,
        action=action,
        limit=limit,
        input_file=input_file,
        save_results=save_results,
        headless=headless,
        browser_path=browser_path,
        reopen_browser=reopen_browser,
    )
