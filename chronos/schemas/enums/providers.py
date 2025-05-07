from enum import StrEnum


class LLMProvider(StrEnum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"


class StorageProvider(StrEnum):
    AWS_S3 = "AWS_S3"
    LOCAL = "LOCAL"
