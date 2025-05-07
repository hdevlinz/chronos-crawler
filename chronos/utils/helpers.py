import asyncio
import os
from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union

from loguru import logger


async def cleanup_temp_file(file_path: Optional[str] = None) -> None:
    if not file_path or not os.path.exists(file_path):
        return

    try:
        await asyncio.to_thread(os.remove, file_path) if asyncio.get_event_loop().is_running() else os.remove(file_path)
        logger.debug(f"Removed temporary file: {file_path}")
    except Exception as e:
        logger.debug(f"Failed to remove temporary file {file_path}: {str(e)}")


def deep_merge(dict1: Dict[str, Any], dict2: Union[Mapping[Any, Any], Dict[str, Any]]) -> Dict[str, Any]:
    for key, value in dict2.items():
        if isinstance(value, Mapping) and key in dict1:
            dict1[key] = deep_merge(dict1.get(key, {}), value)
        else:
            dict1[key] = value

    return dict1


def deep_omit(obj: Union[Dict[str, Any], List[Any]], keys: Union[str, List[str]]) -> Union[Dict[str, Any], List[Any]]:
    if isinstance(keys, str):
        keys = [keys]
    keys_set = set(keys)

    def omit_from_object(o: Union[Dict[str, Any], List[Any]]) -> Union[Dict[str, Any], List[Any]]:
        if isinstance(o, list):
            return [omit_from_object(item) for item in o]

        if isinstance(o, Mapping):
            result = {}
            for key, value in o.items():
                if key in keys_set:
                    continue
                if isinstance(value, (dict, list)):
                    result[key] = omit_from_object(value)
                else:
                    result[key] = value
            return result

        return o

    return omit_from_object(deepcopy(obj))


def deep_flatten(obj: Union[Dict[str, Any], List[Any]]) -> Union[Dict[str, Any], List[Any]]:
    def flatten(o: Union[Dict[str, Any], List[Any]]) -> Union[Dict[str, Any], List[Any], Any]:
        if isinstance(o, list):
            return [flatten(item) for item in o]

        if isinstance(o, dict):
            new_obj: Dict[str, Any] = {}
            for key, value in o.items():
                if isinstance(value, dict):
                    if not value:
                        new_obj[key] = None
                    elif set(value.keys()) == {"value"}:
                        new_obj[key] = flatten(value["value"])
                    else:
                        new_obj[key] = flatten(value)
                elif isinstance(value, list):
                    new_obj[key] = [flatten(item) for item in value]
                else:
                    new_obj[key] = value
            return new_obj

        return o

    return flatten(obj)
