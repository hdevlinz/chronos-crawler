import inspect
from inspect import isawaitable
from typing import Annotated, Any, Awaitable, Callable, Dict, TypeVar, Union

from dishka import AsyncContainer, FromDishka
from dishka.integrations.faststream import inject
from fastapi.dependencies.utils import get_typed_signature
from loguru import logger
from pydantic import BaseModel, TypeAdapter

from chronos.schemas.services.run_service import RunServicePayload
from chronos.utils.module_loading import import_string

T = TypeVar("T")


@inject
async def run_service(
    container: Annotated[AsyncContainer, FromDishka()],
    payload: RunServicePayload,
) -> None:
    async with container() as request_container:
        service_class = import_string(dotted_path=payload.service_)
        service_instance = await request_container.get(service_class)

        service_func = getattr(service_instance, payload.func)
        validated_kwargs = await get_handler_params(service_func, **payload.params)

        await maybe_awaitable(func=service_func(**validated_kwargs))


async def get_handler_params(func: Callable[..., Any], **kwargs: Dict[str, Any]) -> Dict[str, Any]:
    func_signature = get_typed_signature(func)
    signature_params = func_signature.parameters
    validated_kwargs = {}

    for param_name, param in signature_params.items():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            msg = f"Positional arguments are not supported in {func.__name__}"
            raise Exception(msg)

        adapter = analyze_param(func=func, param_name=param_name, annotation=param.annotation)
        if param_name in kwargs:
            value = kwargs[param_name]
        elif param.default != inspect.Signature.empty:
            value = param.default
        else:
            msg = f"No value provided for {param_name}"
            raise Exception(msg)

        if adapter:
            if hasattr(adapter, "model_validate"):
                validated_value = adapter.model_validate(value)
            elif hasattr(adapter, "validate_python"):
                validated_value = adapter.validate_python(value)
            else:
                msg = f"Not supported for {adapter.__class__.__name__}"
                raise Exception(msg)

            validated_kwargs[param_name] = validated_value
        elif param_name in kwargs:
            validated_kwargs[param_name] = value

    return validated_kwargs


def analyze_param(func: Callable[..., Any], param_name: str, annotation: Any) -> Any:
    if annotation is inspect.Signature.empty:
        logger.error(f"Parameter {param_name} needs to be annotated with type in {func.__name__}")

    if isinstance(annotation, TypeAdapter):
        adapter = annotation
    elif inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        adapter = annotation  # type: ignore
    else:
        try:
            adapter = TypeAdapter(annotation)
        except Exception as err:
            logger.error(f"Not supported for {annotation}")
            raise err

    return adapter


async def maybe_awaitable(func: Union[T, Awaitable[T]]) -> T:
    if isawaitable(func):
        return await func  # type: ignore
    return func
