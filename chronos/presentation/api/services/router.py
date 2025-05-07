from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from chronos.presentation.api.services.services import enqueue_run_service

services_router = APIRouter(
    prefix="/services",
    tags=["services"],
    route_class=DishkaRoute,
)

services_router.add_api_route(
    path="",
    endpoint=enqueue_run_service,
    methods=["POST"],
)
