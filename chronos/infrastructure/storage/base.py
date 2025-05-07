from abc import ABC, abstractmethod
from typing import Any, Optional


class StorageManager(ABC):
    @abstractmethod
    def read_file(self, file_key: str, file_type: Optional[str] = None) -> Any:
        pass

    @abstractmethod
    def upload_file(self, file_path: str, file_key: str, content_type: str = "application/octet-stream") -> None:
        pass

    @abstractmethod
    def delete_files(self, file_keys: list[str]) -> None:
        pass

    @abstractmethod
    def get_file_size(self, file_key: str) -> int:
        pass
