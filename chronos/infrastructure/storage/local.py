import json
import os
import shutil
from typing import Any, List, Optional

from loguru import logger

from chronos.core.settings import Settings
from chronos.infrastructure.storage.base import StorageManager


class LocalStorageManager(StorageManager):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        os.makedirs(self._settings.local_storage_dir, exist_ok=True)

    def read_file(self, file_key: str, file_type: Optional[str] = None) -> Any:
        file_path = os.path.join(self._settings.local_storage_dir, file_key)
        mode = "r" if file_type == "text" else "rb"

        try:
            with open(file=file_path, mode=mode) as file:
                data = file.read()
            return json.loads(data) if file_type == "json" else data
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error decoding JSON from local storage: {e}")
            return {}
        except FileNotFoundError:
            msg = f"File {file_key} does not exist"
            raise FileNotFoundError(msg)

    def upload_file(self, file_path: str, file_key: str, content_type: str = "application/octet-stream") -> None:
        dest_path = os.path.join(self._settings.local_storage_dir, file_key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        try:
            shutil.copy2(file_path, dest_path)
        except FileNotFoundError as e:
            logger.error(f"Error uploading file: {e}")

    def delete_files(self, file_keys: List[str]) -> None:
        for file_key in file_keys:
            try:
                os.remove(os.path.join(self._settings.local_storage_dir, file_key))
            except FileNotFoundError:
                logger.warning(f"File {file_key} does not exist")
            except OSError as e:
                logger.error(f"Error deleting file {file_key}: {e}")

    def get_file_size(self, file_key: str) -> int:
        file_path = os.path.join(self._settings.local_storage_dir, file_key)
        try:
            return os.path.getsize(file_path)
        except FileNotFoundError:
            logger.error(f"File {file_key} not found")
            return 0
