import json
from json import JSONDecodeError
from typing import Any, Optional

from botocore.exceptions import ClientError
from loguru import logger
from mypy_boto3_s3 import S3Client

from chronos.core.settings import Settings
from chronos.infrastructure.storage.base import StorageManager


class S3StorageManager(StorageManager):
    def __init__(self, settings: Settings, s3_client: S3Client) -> None:
        self._settings = settings
        self._s3_client = s3_client

    def read_file(self, file_key: str, file_type: Optional[str] = None) -> Any:
        assert self._settings.s3_bucket, "Storage bucket is not configured"
        try:
            resp = self._s3_client.get_object(Bucket=self._settings.s3_bucket, Key=file_key)
            data = resp["Body"].read().decode("utf-8")
            return json.loads(data) if file_type == "json" else data
        except (JSONDecodeError, TypeError) as e:
            logger.error(f"Error decoding JSON from S3: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading file from S3: {e}")
            return None

    def upload_file(self, file_path: str, file_key: str, content_type: str = "application/octet-stream") -> None:
        assert self._settings.s3_bucket, "Storage bucket is not configured"
        with open(file_path, "rb") as file_content:
            self._s3_client.put_object(
                Bucket=self._settings.s3_bucket,
                Key=file_key,
                Body=file_content,
                ACL="public-read",
                ContentType=content_type,
                CacheControl="max-age=31536000, public",
            )

    def delete_files(self, file_keys: list[str]) -> None:
        assert self._settings.s3_bucket, "Storage bucket is not configured"
        self._s3_client.delete_objects(
            Bucket=self._settings.s3_bucket,
            Delete={"Objects": [{"Key": key} for key in file_keys]},
        )

    def get_file_size(self, file_key: str) -> int:
        assert self._settings.s3_bucket, "Storage bucket is not configured"
        try:
            resp = self._s3_client.head_object(Bucket=self._settings.s3_bucket, Key=file_key)
            file_size = resp["ContentLength"]
            return file_size
        except ClientError as e:
            logger.error(f"Error retrieving file size from s3: {e}")
            return 0
