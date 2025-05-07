from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

DetailViewItem = TypeVar("DetailViewItem", bound=BaseModel)


class BaseListViewModel(BaseModel, Generic[DetailViewItem]):
    model_config = ConfigDict(from_attributes=True)

    items: list[DetailViewItem]
    total: int
