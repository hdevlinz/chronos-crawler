from typing import Optional

from dishka import Provider, Scope, provide
from mypy_boto3_s3 import S3Client

from chronos.core.settings import Settings
from chronos.infrastructure.storage.aws_s3 import S3StorageManager
from chronos.infrastructure.storage.base import StorageManager
from chronos.infrastructure.storage.local import LocalStorageManager


class ManagersProvider(Provider):
    @provide(scope=Scope.APP)
    def s3_storage_manager(self, settings: Settings, s3_client: Optional[S3Client] = None) -> StorageManager:
        if s3_client:
            return S3StorageManager(settings=settings, s3_client=s3_client)

        return LocalStorageManager(settings=settings)
