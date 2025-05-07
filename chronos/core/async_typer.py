import asyncio
import inspect
from functools import wraps
from typing import Any, Callable, Coroutine, cast

import nest_asyncio
from typer import Typer
from typer.models import CommandFunctionType

nest_asyncio.apply()


class AsyncTyper(Typer):
    @staticmethod
    def maybe_run_async(
        decorator: Callable[[CommandFunctionType], CommandFunctionType],
        func: CommandFunctionType,
    ) -> CommandFunctionType:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            def runner(*args: Any, **kwargs: Any) -> Any:
                return asyncio.run(cast(Callable[..., Coroutine[Any, Any, Any]], func)(*args, **kwargs))

            decorator(cast(CommandFunctionType, runner))
        else:
            decorator(func)

        return func

    def callback(self, *args: Any, **kwargs: Any) -> Callable[[CommandFunctionType], CommandFunctionType]:
        decorator = super().callback(*args, **kwargs)
        return lambda func: self.maybe_run_async(decorator=decorator, func=func)

    def command(self, *args: Any, **kwargs: Any) -> Callable[[CommandFunctionType], CommandFunctionType]:
        decorator = super().command(*args, **kwargs)
        return lambda func: self.maybe_run_async(decorator=decorator, func=func)
