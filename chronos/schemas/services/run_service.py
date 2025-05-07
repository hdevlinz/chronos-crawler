from typing import Any, Dict

from pydantic import BaseModel


class RunServicePayload(BaseModel):
    service: str
    func: str
    params: Dict[str, Any] = {}

    @property
    def service_(self) -> str:
        formatted_service = self.service
        if not formatted_service.endswith("Service"):
            formatted_service += "Service"

        if not formatted_service.startswith("chronos.services."):
            formatted_service = f"chronos.services.{formatted_service}"

        return formatted_service
