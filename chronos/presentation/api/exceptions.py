from typing import Union

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.constants import REF_PREFIX
from fastapi.openapi.utils import validation_error_response_definition
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from chronos.infrastructure.exceptions import ApplicationError
from chronos.utils.constants import VALIDATION_ERROR


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(exc_class_or_status_code=ApplicationError, handler=_application_error_handler)
    app.add_exception_handler(exc_class_or_status_code=HTTPException, handler=_http_error_handler)
    app.add_exception_handler(exc_class_or_status_code=RequestValidationError, handler=_http422_error_handler)


def _get_error_response(exc: Exception) -> dict:
    detail = getattr(exc, "detail", str(exc))
    res = {"errors": [detail], "success": False}

    if hasattr(exc, "error_code"):
        res["error_code"] = getattr(exc, "error_code")

    return res


def _application_error_handler(_, error: Union[ApplicationError, Exception]) -> JSONResponse:  # type: ignore
    content = _get_error_response(exc=error)

    return JSONResponse(content=content, status_code=400)


def _http_error_handler(_: Request, exc: Union[HTTPException, Exception]) -> JSONResponse:
    content = _get_error_response(exc=exc)

    status_code = getattr(exc, "status_code", 500)
    return JSONResponse(content=content, status_code=status_code)


def _http422_error_handler(_: Request, exc: Union[RequestValidationError, ValidationError, Exception]) -> JSONResponse:
    errors = ["Validation Error"]
    if hasattr(exc, "errors"):
        errors = exc.errors()

    result = {}
    if isinstance(errors, list):
        pydantic_errors = jsonable_encoder(obj=errors)
        for error in pydantic_errors:
            loc = error["loc"]
            if len(loc) == 2:
                field = loc[1]
            else:
                field = loc[0]
            message = error["msg"]
            result[field] = message
    else:
        result = jsonable_encoder(obj=errors)

    return JSONResponse(
        content={"errors": result, "success": False, "error_code": VALIDATION_ERROR},
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
    )


validation_error_response_definition["properties"] = {
    "errors": {
        "title": "Errors",
        "type": "array",
        "items": {"$ref": f"{REF_PREFIX}ValidationError"},
    },
}
