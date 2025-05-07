class ApplicationError(Exception):
    """Class for Application errors."""

    detail: str
    error_code: str

    def __init__(self, detail: str = "Application Error", error_code: str = "application_error") -> None:
        self.detail = detail
        self.error_code = error_code

    def __str__(self) -> str:
        return f"{self.error_code}: {self.detail}"


class ExternalClientError(Exception):
    """Class for External Client errors."""

    detail: str
    error_code: str

    def __init__(self, detail: str = "External Client Error", error_code: str = "400") -> None:
        self.detail = detail
        self.error_code = error_code

    def __str__(self) -> str:
        return f"{self.error_code}: {self.detail}"
