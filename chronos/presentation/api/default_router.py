from fastapi import APIRouter, Request
from scalar_fastapi import get_scalar_api_reference
from starlette.responses import HTMLResponse

default_router = APIRouter()


@default_router.get("/")
async def root() -> dict:
    return {
        "success": True,
        "msg": "running",
    }


@default_router.get("/scalar", include_in_schema=False)
async def scalar_html(request: Request) -> HTMLResponse:
    return get_scalar_api_reference(
        openapi_url=request.app.openapi_url,
        title=request.app.title,
    )
