from collections.abc import Sequence
from math import ceil
from typing import Any, Generic, Optional, TypeVar

from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage, AbstractParams
from pydantic import BaseModel, ConfigDict, Field

DataType = TypeVar("DataType", bound=(BaseModel))
T = TypeVar("T")


class PageBase(Page[T], Generic[T]):
    previous_page: int | None = Field(default=None, description="Page number of the previous page")
    next_page: int | None = Field(default=None, description="Page number of the next page")


class ResponseBase(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    message: str | None = ""
    meta: dict | Any | None = {}
    data: T | None = None

    @property
    def is_empty(self) -> bool:
        return self.data is None


class GetResponsePaginated(AbstractPage[T], Generic[T]):
    message: str | None = ""
    meta: dict | None = {}
    data: PageBase[T]

    __params_type__ = Params  # Set params related to Page

    @classmethod
    def create(cls, items: Sequence[T], total: int, params: AbstractParams) -> Any:
        page = getattr(params, "page")
        size = getattr(params, "size")

        if size is not None and total is not None and size != 0:
            pages = ceil(total / size)
        else:
            pages = 0

        return cls(
            data=PageBase[T](
                items=items,
                page=page,
                size=size,
                total=total,
                pages=pages,
                next_page=page + 1 if page < pages else None,
                previous_page=page - 1 if page > 1 else None,
            )
        )

    @property
    def is_empty(self) -> bool:
        return (not self.data.items) or self.data.total == 0


class GetResponseBase(ResponseBase[DataType], Generic[DataType]):
    message: str | None = "Data got correctly"


class ListResponseBase(ResponseBase[DataType], Generic[DataType]):
    message: str | None = "Data listed correctly"


class PostResponseBase(ResponseBase[DataType], Generic[DataType]):
    message: str | None = "Data created correctly"


class PutResponseBase(ResponseBase[DataType], Generic[DataType]):
    message: str | None = "Data updated correctly"


class DeleteResponseBase(ResponseBase[DataType], Generic[DataType]):
    message: str | None = "Data deleted correctly"


def create_response(
    data: DataType | Page[DataType],
    message: Optional[str] = None,
    meta: dict | Any | None = {},
) -> Any:
    if isinstance(data, GetResponsePaginated):
        data.message = "Data paginated correctly" if message is None else message
        data.meta = meta
        return data

    if message is None:
        return {"data": data, "meta": meta}

    return {"data": data, "message": message, "meta": meta}
