from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from chronos.presentation.api.services.router import services_router

root_router = APIRouter(
    prefix="/api/v1",
    route_class=DishkaRoute,
)

root_router.include_router(router=services_router)
